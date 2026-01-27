/**
 * @fileoverview Pino-backed singleton logger with environment-adaptive output.
 * Implements RFC5424 level mapping, structured context, automatic trace injection via
 * OpenTelemetry, and graceful shutdown. In a serverless environment (like Cloudflare
 * Workers), it uses a lightweight console-based logger.
 * @module src/utils/internal/logger
 */
import type { LevelWithSilent, Logger as PinoLogger } from 'pino';
import pino from 'pino';

import { config } from '@/config/index.js';
import {
  requestContextService,
  type RequestContext,
} from '@/utils/internal/requestContext.js';
import { sanitization } from '@/utils/security/sanitization.js';

export type McpLogLevel =
  | 'debug'
  | 'info'
  | 'notice'
  | 'warning'
  | 'error'
  | 'crit'
  | 'alert'
  | 'emerg';

const mcpToPinoLevel: Record<McpLogLevel, LevelWithSilent> = {
  emerg: 'fatal',
  alert: 'fatal',
  crit: 'error',
  error: 'error',
  warning: 'warn',
  notice: 'info',
  info: 'info',
  debug: 'debug',
};

const pinoToMcpLevelSeverity: Record<string, number> = {
  fatal: 0,
  error: 2,
  warn: 4,
  info: 6,
  debug: 7,
};

const isServerless =
  typeof process === 'undefined' || process.env.IS_SERVERLESS === 'true';

export class Logger {
  private static readonly instance: Logger = new Logger();
  private pinoLogger?: PinoLogger;
  private interactionLogger?: PinoLogger | undefined;
  private initialized = false;
  private currentMcpLevel: McpLogLevel = 'info';

  private rateLimitThreshold = 10;
  private rateLimitWindow = 60000;
  private messageCounts = new Map<
    string,
    { count: number; firstSeen: number }
  >();
  private suppressedMessages = new Map<string, number>();
  private cleanupTimer?: NodeJS.Timeout;

  private constructor() {
    // The constructor is now safe to call in a global scope.
  }

  public static getInstance(): Logger {
    return Logger.instance;
  }

  private async createPinoLogger(
    level: McpLogLevel,
    transportType?: 'stdio' | 'http',
  ): Promise<PinoLogger> {
    const pinoLevel = mcpToPinoLevel[level] || 'info';
    const isTest = config.environment === 'testing';

    // In test environment, suppress all output unless explicitly enabled
    const enableTestLogs = process.env.ENABLE_TEST_LOGS === 'true';

    const pinoOptions: pino.LoggerOptions = {
      level: isTest && !enableTestLogs ? 'silent' : pinoLevel,
      base: {
        env: config.environment,
        version: config.mcpServerVersion,
        pid: !isServerless ? process.pid : undefined,
      },
      redact: {
        paths: sanitization.getSensitivePinoFields(),
        censor: '[REDACTED]',
      },
    };

    if (isServerless) {
      return pino(pinoOptions);
    }

    // Node.js specific transports
    const { default: fs } = await import('fs');
    const { default: path } = await import('path');

    const transports: pino.TransportTargetOptions[] = [];
    const isDevelopment = config.environment === 'development';

    // CRITICAL: STDIO transport MUST NOT output colored logs to stdout.
    // The MCP specification requires clean JSON-RPC on stdout with no ANSI codes.
    // Only use pretty/colored output for HTTP mode or when explicitly debugging.
    // Respect NO_COLOR environment variable (https://no-color.org/)
    const noColorEnv =
      process.env.NO_COLOR === '1' || process.env.FORCE_COLOR === '0';
    const useColoredOutput =
      isDevelopment && transportType !== 'stdio' && !noColorEnv;

    if (useColoredOutput && !isServerless) {
      // Try to resolve 'pino-pretty' robustly even when bundled (e.g., Bun/ESM),
      // falling back to JSON stdout if resolution fails.
      try {
        const { createRequire } = await import('node:module');
        const require = createRequire(import.meta.url);
        const prettyTarget = require.resolve('pino-pretty');
        transports.push({
          target: prettyTarget,
          options: { colorize: true, translateTime: 'yyyy-mm-dd HH:MM:ss' },
        });
      } catch (err) {
        console.warn(
          `[Logger Init] Pretty transport unavailable (${err instanceof Error ? err.message : String(err)}); falling back to stdout JSON.`,
        );
        transports.push({ target: 'pino/file', options: { destination: 1 } });
      }
    } else if (!isTest) {
      // CRITICAL: For STDIO transport, logs MUST go to stderr (fd 2), NOT stdout (fd 1).
      // The MCP specification requires only JSON-RPC messages on stdout.
      // For HTTP transport or production, we also use stderr to avoid polluting stdout.
      transports.push({ target: 'pino/file', options: { destination: 2 } });
    }

    if (config.logsPath) {
      try {
        if (!fs.existsSync(config.logsPath)) {
          fs.mkdirSync(config.logsPath, { recursive: true });
        }
        transports.push({
          level: pinoLevel,
          target: 'pino/file',
          options: {
            destination: path.join(config.logsPath, 'combined.log'),
            mkdir: true,
          },
        });
        transports.push({
          level: 'error',
          target: 'pino/file',
          options: {
            destination: path.join(config.logsPath, 'error.log'),
            mkdir: true,
          },
        });
      } catch (err) {
        console.error(
          `[Logger Init] Failed to configure file logging: ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }

    return pino({ ...pinoOptions, transport: { targets: transports } });
  }

  private async createInteractionLogger(): Promise<PinoLogger | undefined> {
    if (isServerless || !config.logsPath) return undefined;

    const { default: path } = await import('path');
    return pino({
      transport: {
        target: 'pino/file',
        options: {
          destination: path.join(config.logsPath, 'interactions.log'),
          mkdir: true,
        },
      },
    });
  }

  public async initialize(
    level: McpLogLevel = 'info',
    transportType?: 'stdio' | 'http',
  ): Promise<void> {
    if (this.initialized) {
      this.warning(
        'Logger already initialized.',
        requestContextService.createRequestContext({
          operation: 'loggerReinit',
        }),
      );
      return;
    }
    this.currentMcpLevel = level;
    this.pinoLogger = await this.createPinoLogger(level, transportType);
    this.interactionLogger = await this.createInteractionLogger();

    // Start the cleanup timer only after initialization and only in Node.js
    if (!isServerless && !this.cleanupTimer) {
      this.cleanupTimer = setInterval(
        () => this.flushSuppressedMessages(),
        this.rateLimitWindow,
      );
      this.cleanupTimer.unref?.();
    }

    this.initialized = true;
    this.info(
      `Logger initialized. MCP level: ${level}.`,
      requestContextService.createRequestContext({ operation: 'loggerInit' }),
    );
  }

  public setLevel(newLevel: McpLogLevel): void {
    if (!this.pinoLogger || !this.initialized) {
      console.error('Cannot set level: Logger not initialized.');
      return;
    }
    this.currentMcpLevel = newLevel;
    this.pinoLogger.level = mcpToPinoLevel[newLevel] || 'info';
    this.info(
      `Log level changed to ${newLevel}.`,
      requestContextService.createRequestContext({
        operation: 'loggerSetLevel',
      }),
    );
  }

  public async close(): Promise<void> {
    if (!this.initialized) return Promise.resolve();
    this.info(
      'Logger shutting down.',
      requestContextService.createRequestContext({ operation: 'loggerClose' }),
    );
    if (this.cleanupTimer) clearInterval(this.cleanupTimer);
    this.flushSuppressedMessages();

    // Wait for all pending writes to complete
    await Promise.all([
      new Promise<void>((resolve) => {
        if (this.pinoLogger) {
          this.pinoLogger.flush((err) => {
            if (err) console.error('Error flushing main logger:', err);
            resolve();
          });
        } else {
          resolve();
        }
      }),
      new Promise<void>((resolve) => {
        if (this.interactionLogger) {
          this.interactionLogger.flush((err) => {
            if (err) console.error('Error flushing interaction logger:', err);
            resolve();
          });
        } else {
          resolve();
        }
      }),
    ]);

    this.initialized = false;
  }

  public isInitialized(): boolean {
    return this.initialized;
  }

  private isRateLimited(message: string): boolean {
    const now = Date.now();
    const entry = this.messageCounts.get(message);
    if (!entry) {
      this.messageCounts.set(message, { count: 1, firstSeen: now });
      return false;
    }
    if (now - entry.firstSeen > this.rateLimitWindow) {
      this.messageCounts.set(message, { count: 1, firstSeen: now });
      return false;
    }
    entry.count++;
    if (entry.count > this.rateLimitThreshold) {
      this.suppressedMessages.set(
        message,
        (this.suppressedMessages.get(message) || 0) + 1,
      );
      return true;
    }
    return false;
  }

  private flushSuppressedMessages(): void {
    if (this.suppressedMessages.size === 0) return;
    for (const [message, count] of this.suppressedMessages.entries()) {
      this.warning(
        `Log message suppressed ${count} times due to rate limiting.`,
        requestContextService.createRequestContext({
          operation: 'loggerRateLimitFlush',
          additionalContext: { originalMessage: message },
        }),
      );
    }
    this.suppressedMessages.clear();
    this.messageCounts.clear();
  }

  private log(
    level: McpLogLevel,
    msg: string,
    context?: RequestContext,
    error?: Error,
  ): void {
    if (!this.pinoLogger || !this.initialized) return;

    const pinoLevel = mcpToPinoLevel[level] || 'info';
    const currentPinoLevel = mcpToPinoLevel[this.currentMcpLevel] || 'info';

    const levelSeverity = pinoToMcpLevelSeverity[pinoLevel];
    const currentLevelSeverity = pinoToMcpLevelSeverity[currentPinoLevel];

    if (
      typeof levelSeverity === 'number' &&
      typeof currentLevelSeverity === 'number' &&
      levelSeverity > currentLevelSeverity
    ) {
      return;
    }

    if (this.isRateLimited(msg)) return;

    const logObject: Record<string, unknown> = { ...context };
    if (error) logObject.err = pino.stdSerializers.err(error);

    this.pinoLogger[pinoLevel](logObject, msg);
  }

  public debug(msg: string, context?: RequestContext): void {
    this.log('debug', msg, context);
  }
  public info(msg: string, context?: RequestContext): void {
    this.log('info', msg, context);
  }
  public notice(msg: string, context?: RequestContext): void {
    this.log('notice', msg, context);
  }
  public warning(msg: string, context?: RequestContext): void {
    this.log('warning', msg, context);
  }

  public error(
    msg: string,
    errorOrContext: Error | RequestContext,
    context?: RequestContext,
  ): void {
    const errorObj =
      errorOrContext instanceof Error ? errorOrContext : undefined;
    const actualContext =
      errorOrContext instanceof Error ? context : errorOrContext;
    this.log('error', msg, actualContext, errorObj);
  }

  public crit(
    msg: string,
    errorOrContext: Error | RequestContext,
    context?: RequestContext,
  ): void {
    const errorObj =
      errorOrContext instanceof Error ? errorOrContext : undefined;
    const actualContext =
      errorOrContext instanceof Error ? context : errorOrContext;
    this.log('crit', msg, actualContext, errorObj);
  }

  public alert(
    msg: string,
    errorOrContext: Error | RequestContext,
    context?: RequestContext,
  ): void {
    const errorObj =
      errorOrContext instanceof Error ? errorOrContext : undefined;
    const actualContext =
      errorOrContext instanceof Error ? context : errorOrContext;
    this.log('alert', msg, actualContext, errorObj);
  }

  public emerg(
    msg: string,
    errorOrContext: Error | RequestContext,
    context?: RequestContext,
  ): void {
    const errorObj =
      errorOrContext instanceof Error ? errorOrContext : undefined;
    const actualContext =
      errorOrContext instanceof Error ? context : errorOrContext;
    this.log('emerg', msg, actualContext, errorObj);
  }

  public fatal(
    msg: string,
    errorOrContext: Error | RequestContext,
    context?: RequestContext,
  ): void {
    this.emerg(msg, errorOrContext, context);
  }

  public logInteraction(
    interactionName: string,
    data: Record<string, unknown>,
  ): void {
    if (!this.interactionLogger) {
      if (!isServerless)
        this.warning(
          'Interaction logger not available.',
          (data.context || {}) as RequestContext,
        );
      return;
    }
    this.interactionLogger.info({ interactionName, ...data });
  }
}

export const logger = Logger.getInstance();
