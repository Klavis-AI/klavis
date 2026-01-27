/**
 * @fileoverview Health snapshot utility to surface observability/runtime readiness.
 * This avoids heavy checks and focuses on quick signals for status endpoints or logs.
 * @module src/utils/internal/health
 */

import { config } from '@/config/index.js';
import { logger } from '@/utils/internal/logger.js';
import { runtimeCaps } from '@/utils/internal/runtime.js';

export interface HealthSnapshot {
  app: { name: string; version: string; environment: string };
  runtime: {
    isNode: boolean;
    isWorkerLike: boolean;
    isBrowserLike: boolean;
  };
  telemetry: {
    enabled: boolean;
    diagLevel: string | undefined;
  };
  logging: {
    initialized: boolean;
  };
}

export function getHealthSnapshot(): HealthSnapshot {
  return {
    app: {
      name: config.mcpServerName,
      version: config.mcpServerVersion,
      environment: config.environment,
    },
    runtime: {
      isNode: runtimeCaps.isNode,
      isWorkerLike: runtimeCaps.isWorkerLike,
      isBrowserLike: runtimeCaps.isBrowserLike,
    },
    telemetry: {
      enabled: Boolean(config.openTelemetry.enabled),
      diagLevel: config.openTelemetry.logLevel,
    },
    logging: {
      initialized: logger.isInitialized(),
    },
  };
}
