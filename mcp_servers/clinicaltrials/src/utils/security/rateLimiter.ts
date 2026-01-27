/**
 * @fileoverview Provides a generic `RateLimiter` class for implementing rate limiting logic.
 * It supports configurable time windows, request limits, and automatic cleanup of expired entries.
 * @module src/utils/security/rateLimiter
 */
import { trace } from '@opentelemetry/api';
import { inject, injectable } from 'tsyringe';

import { config as ConfigType } from '@/config/index.js';
import { AppConfig, Logger } from '@/container/tokens.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  type RequestContext,
  logger as LoggerType,
  requestContextService,
} from '@/utils/index.js';

/**
 * Defines configuration options for the {@link RateLimiter}.
 */
export interface RateLimitConfig {
  /** Time window in milliseconds. */
  windowMs: number;
  /** Maximum number of requests allowed in the window. */
  maxRequests: number;
  /** Custom error message template. Can include `{waitTime}` placeholder. */
  errorMessage?: string;
  /** If true, skip rate limiting in development. */
  skipInDevelopment?: boolean;
  /** Optional function to generate a custom key for rate limiting. */
  keyGenerator?: (identifier: string, context?: RequestContext) => string;
  /** How often, in milliseconds, to clean up expired entries. */
  cleanupInterval?: number;
  /** Maximum number of tracked keys. When exceeded, oldest entries are evicted (LRU). Default: 10000 */
  maxTrackedKeys?: number;
}

/**
 * Represents an individual entry for tracking requests against a rate limit key.
 */
export interface RateLimitEntry {
  /** Current request count. */
  count: number;
  /** When the window resets (timestamp in milliseconds). */
  resetTime: number;
  /** Last access timestamp for LRU eviction. */
  lastAccess: number;
}

@injectable()
export class RateLimiter {
  private readonly limits: Map<string, RateLimitEntry>;
  private cleanupTimer: NodeJS.Timeout | null = null;
  private readonly effectiveConfig: RateLimitConfig;

  constructor(
    @inject(AppConfig) private config: typeof ConfigType,
    @inject(Logger) private logger: typeof LoggerType,
  ) {
    const defaultConfig: RateLimitConfig = {
      windowMs: 15 * 60 * 1000,
      maxRequests: 100,
      errorMessage:
        'Rate limit exceeded. Please try again in {waitTime} seconds.',
      skipInDevelopment: false,
      cleanupInterval: 5 * 60 * 1000,
      maxTrackedKeys: 10000,
    };
    this.effectiveConfig = { ...defaultConfig };
    this.limits = new Map();
    this.startCleanupTimer();
  }

  /**
   * Evicts the least recently used entry from the limits Map.
   * This prevents unbounded memory growth in high-traffic scenarios.
   * @private
   */
  private evictLRUEntry(): void {
    if (this.limits.size === 0) return;

    let oldestKey: string | null = null;
    let oldestTime = Infinity;

    // Find the entry with the oldest lastAccess time
    for (const [key, entry] of this.limits.entries()) {
      if (entry.lastAccess < oldestTime) {
        oldestTime = entry.lastAccess;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.limits.delete(oldestKey);
      const logContext = requestContextService.createRequestContext({
        operation: 'RateLimiter.evictLRUEntry',
        additionalContext: {
          evictedKey: oldestKey,
          remainingEntries: this.limits.size,
        },
      });
      this.logger.debug('Evicted LRU entry from rate limiter', logContext);
    }
  }

  private startCleanupTimer(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }
    const interval = this.effectiveConfig.cleanupInterval;
    if (interval && interval > 0) {
      this.cleanupTimer = setInterval(() => {
        this.cleanupExpiredEntries();
      }, interval);
      if (this.cleanupTimer.unref) {
        this.cleanupTimer.unref();
      }
    }
  }

  private cleanupExpiredEntries(): void {
    const now = Date.now();
    let expiredCount = 0;
    for (const [key, entry] of this.limits.entries()) {
      if (now >= entry.resetTime) {
        this.limits.delete(key);
        expiredCount++;
      }
    }
    if (expiredCount > 0) {
      const logContext = requestContextService.createRequestContext({
        operation: 'RateLimiter.cleanupExpiredEntries',
        additionalContext: {
          cleanedCount: expiredCount,
          totalRemainingAfterClean: this.limits.size,
        },
      });
      this.logger.debug(
        `Cleaned up ${expiredCount} expired rate limit entries`,
        logContext,
      );
    }
  }

  public configure(config: Partial<RateLimitConfig>): void {
    Object.assign(this.effectiveConfig, config);
    if (config.cleanupInterval !== undefined) {
      this.startCleanupTimer();
    }
  }

  public getConfig(): RateLimitConfig {
    return { ...this.effectiveConfig };
  }

  public reset(): void {
    this.limits.clear();
    const logContext = requestContextService.createRequestContext({
      operation: 'RateLimiter.reset',
    });
    this.logger.debug('Rate limiter reset, all limits cleared', logContext);
  }

  public check(key: string, context?: RequestContext): void {
    const activeSpan = trace.getActiveSpan();
    activeSpan?.setAttribute('mcp.rate_limit.checked', true);

    if (
      this.effectiveConfig.skipInDevelopment &&
      this.config.environment === 'development'
    ) {
      activeSpan?.setAttribute('mcp.rate_limit.skipped', 'development');
      return;
    }

    const limitKey = this.effectiveConfig.keyGenerator
      ? this.effectiveConfig.keyGenerator(key, context)
      : key;
    activeSpan?.setAttribute('mcp.rate_limit.key', limitKey);

    const now = Date.now();
    let entry = this.limits.get(limitKey);

    if (!entry || now >= entry.resetTime) {
      // Check if we need to evict an entry before adding a new one
      const maxKeys = this.effectiveConfig.maxTrackedKeys || 10000;
      if (!entry && this.limits.size >= maxKeys) {
        this.evictLRUEntry();
        activeSpan?.addEvent('rate_limit_lru_eviction', {
          'mcp.rate_limit.size_before_eviction': this.limits.size + 1,
          'mcp.rate_limit.max_keys': maxKeys,
        });
      }

      entry = {
        count: 1,
        resetTime: now + this.effectiveConfig.windowMs,
        lastAccess: now,
      };
      this.limits.set(limitKey, entry);
    } else {
      entry.count++;
      entry.lastAccess = now; // Update LRU timestamp
    }

    const remaining = Math.max(
      0,
      this.effectiveConfig.maxRequests - entry.count,
    );
    activeSpan?.setAttributes({
      'mcp.rate_limit.limit': this.effectiveConfig.maxRequests,
      'mcp.rate_limit.count': entry.count,
      'mcp.rate_limit.remaining': remaining,
      'mcp.rate_limit.tracked_keys': this.limits.size,
    });

    if (entry.count > this.effectiveConfig.maxRequests) {
      const waitTime = Math.ceil((entry.resetTime - now) / 1000);
      const errorMessage = (
        this.effectiveConfig.errorMessage ||
        'Rate limit exceeded. Please try again in {waitTime}  seconds.'
      ).replace('{waitTime}', waitTime.toString());

      activeSpan?.addEvent('rate_limit_exceeded', {
        'mcp.rate_limit.wait_time_seconds': waitTime,
      });

      throw new McpError(JsonRpcErrorCode.RateLimited, errorMessage, {
        waitTimeSeconds: waitTime,
        key: limitKey,
        limit: this.effectiveConfig.maxRequests,
        windowMs: this.effectiveConfig.windowMs,
      });
    }
  }

  public getStatus(key: string): {
    current: number;
    limit: number;
    remaining: number;
    resetTime: number;
  } | null {
    const entry = this.limits.get(key);
    if (!entry) return null;
    return {
      current: entry.count,
      limit: this.effectiveConfig.maxRequests,
      remaining: Math.max(0, this.effectiveConfig.maxRequests - entry.count),
      resetTime: entry.resetTime,
    };
  }

  public dispose(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
    this.limits.clear();
  }
}
