#!/usr/bin/env node
/**
 * @fileoverview Main entry point for the MCP TypeScript Template application.
 * This script initializes the configuration, sets up the logger, starts the
 * MCP server (either via STDIO or HTTP transport), and handles graceful
 * shutdown on process signals or unhandled errors.
 * @module src/index
 */

// CRITICAL: Disable ANSI color codes BEFORE any imports when running via MCP clients.
// The MCP specification requires clean output. Even in HTTP mode, if launched via
// bunx/npx by an MCP client, colored output pollutes the client's process streams.
// This must be set before pino-pretty or any other library loads.
//
// We disable colors in these scenarios:
// 1. STDIO mode (always - MCP JSON-RPC on stdout)
// 2. HTTP mode when NOT in TTY (likely launched by MCP client via bunx/npx)
// 3. When explicitly disabled via existing NO_COLOR env var
const transportType = process.env.MCP_TRANSPORT_TYPE?.toLowerCase();
const isStdioMode = !transportType || transportType === 'stdio';
const isHttpModeWithoutTty = transportType === 'http' && !process.stdout.isTTY;

if (isStdioMode || isHttpModeWithoutTty) {
  process.env.NO_COLOR = '1'; // Standard env var that most libraries respect
  process.env.FORCE_COLOR = '0'; // Disable forced coloring
}

import {
  initializeOpenTelemetry,
  shutdownOpenTelemetry,
} from '@/utils/telemetry/instrumentation.js';
import 'reflect-metadata';

import {
  initializePerformance_Hrt,
  requestContextService,
} from '@/utils/index.js';
import { type McpLogLevel, logger } from '@/utils/internal/logger.js';

import { config as appConfigType } from '@/config/index.js';
import container, {
  AppConfig,
  TransportManagerToken,
  composeContainer,
} from '@/container/index.js';
import { TransportManager } from '@/mcp-server/transports/manager.js';

// The container is now composed in start(), so we must resolve config there.
let config: typeof appConfigType;
let transportManager: TransportManager;
let isShuttingDown = false;

const shutdown = async (signal: string): Promise<void> => {
  if (isShuttingDown) {
    return;
  }
  isShuttingDown = true;

  const shutdownContext = requestContextService.createRequestContext({
    operation: 'ServerShutdown',
    triggerEvent: signal,
  });

  logger.info(
    `Received ${signal}. Initiating graceful shutdown...`,
    shutdownContext,
  );

  try {
    if (transportManager) {
      await transportManager.stop(signal);
    }

    logger.info(
      'Graceful shutdown completed successfully. Exiting.',
      shutdownContext,
    );

    // Shutdown OpenTelemetry and logger last to ensure all telemetry and logs are sent.
    await shutdownOpenTelemetry();
    await logger.close();

    process.exit(0);
  } catch (error) {
    logger.error(
      'Critical error during shutdown process.',
      error as Error,
      shutdownContext,
    );
    try {
      await logger.close();
    } catch (_e) {
      // Ignore errors during final logger close attempt
    }
    process.exit(1);
  }
};

const start = async (): Promise<void> => {
  try {
    // Initialize DI container first
    composeContainer();
    // Now it's safe to resolve dependencies
    config = container.resolve<typeof appConfigType>(AppConfig);
  } catch (_error) {
    // This will catch the McpError from parseConfig
    if (process.stdout.isTTY) {
      // The config module already logged the details. We just provide a final message.
      console.error('Halting due to critical configuration error.');
    }
    // Ensure OpenTelemetry is shut down if it was started before the error
    await shutdownOpenTelemetry();
    process.exit(1);
  }

  // Initialize OpenTelemetry before logger to capture all spans
  // This must happen before logger initialization for proper instrumentation
  try {
    await initializeOpenTelemetry();
  } catch (error) {
    // Observability failure should not block startup
    console.error('[Startup] Failed to initialize OpenTelemetry:', error);
    // Continue - application can run without telemetry
  }

  // Initialize the high-resolution timer
  await initializePerformance_Hrt();

  const validMcpLogLevels: McpLogLevel[] = [
    'debug',
    'info',
    'notice',
    'warning',
    'error',
    'crit',
    'alert',
    'emerg',
  ];
  const initialLogLevelConfig = config.logLevel;

  let validatedMcpLogLevel: McpLogLevel = 'info';
  if (validMcpLogLevels.includes(initialLogLevelConfig as McpLogLevel)) {
    validatedMcpLogLevel = initialLogLevelConfig as McpLogLevel;
  } else {
    if (process.stdout.isTTY) {
      console.warn(
        `[Startup Warning] Invalid MCP_LOG_LEVEL "${initialLogLevelConfig}". Defaulting to "info".`,
      );
    }
  }

  // Pass transport type to logger to ensure STDIO mode uses plain JSON (no ANSI colors)
  await logger.initialize(validatedMcpLogLevel, config.mcpTransportType);

  // Storage Service is now initialized in the container
  logger.info(
    `Storage service initialized with provider: ${config.storage.providerType}`,
    requestContextService.createRequestContext({ operation: 'StorageInit' }),
  );

  transportManager = container.resolve<TransportManager>(TransportManagerToken);

  const startupContext = requestContextService.createRequestContext({
    operation: 'ServerStartup',
    applicationName: config.mcpServerName,
    applicationVersion: config.mcpServerVersion,
    nodeEnvironment: config.environment,
  });

  logger.info(
    `Starting ${config.mcpServerName} (v${config.mcpServerVersion})...`,
    startupContext,
  );

  try {
    await transportManager.start();

    logger.info(
      `${config.mcpServerName} is now running and ready.`,
      startupContext,
    );

    process.on('SIGTERM', () => void shutdown('SIGTERM'));
    process.on('SIGINT', () => void shutdown('SIGINT'));
    process.on('uncaughtException', (error: Error) => {
      logger.fatal(
        'FATAL: Uncaught exception detected.',
        error,
        startupContext,
      );
      void shutdown('uncaughtException');
    });
    process.on('unhandledRejection', (reason: unknown) => {
      logger.fatal(
        'FATAL: Unhandled promise rejection detected.',
        reason as Error,
        startupContext,
      );
      void shutdown('unhandledRejection');
    });
  } catch (error) {
    logger.fatal(
      'CRITICAL ERROR DURING STARTUP.',
      error as Error,
      startupContext,
    );
    await shutdownOpenTelemetry(); // Attempt to flush any startup-related traces
    process.exit(1);
  }
};

void (async () => {
  try {
    await start();
  } catch (error) {
    if (process.stdout.isTTY) {
      console.error('[GLOBAL CATCH] A fatal, unhandled error occurred:', error);
    }
    process.exit(1);
  }
})();
