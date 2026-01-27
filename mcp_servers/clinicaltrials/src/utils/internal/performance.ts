/**
 * @fileoverview Performance utility for tool execution with modern observability.
 * Wraps tool logic to measure duration, payload sizes, and memory usage, and
 * records results to OpenTelemetry plus structured logs. No manual spans beyond
 * the single wrapper span here per project guidelines.
 * @module src/utils/internal/performance
 */
import { SpanStatusCode, trace } from '@opentelemetry/api';
import type { performance as PerfHooksPerformance } from 'perf_hooks';

import { config } from '@/config/index.js';
import { McpError } from '@/types-global/errors.js';
import {
  ATTR_CODE_FUNCTION,
  ATTR_CODE_NAMESPACE,
  ATTR_MCP_TOOL_DURATION_MS,
  ATTR_MCP_TOOL_ERROR_CODE,
  ATTR_MCP_TOOL_INPUT_BYTES,
  ATTR_MCP_TOOL_MEMORY_HEAP_USED_AFTER,
  ATTR_MCP_TOOL_MEMORY_HEAP_USED_BEFORE,
  ATTR_MCP_TOOL_MEMORY_HEAP_USED_DELTA,
  ATTR_MCP_TOOL_MEMORY_RSS_AFTER,
  ATTR_MCP_TOOL_MEMORY_RSS_BEFORE,
  ATTR_MCP_TOOL_MEMORY_RSS_DELTA,
  ATTR_MCP_TOOL_OUTPUT_BYTES,
  ATTR_MCP_TOOL_SUCCESS,
} from '@/utils/telemetry/semconv.js';
import { logger } from '@/utils/internal/logger.js';
import type { RequestContext } from '@/utils/internal/requestContext.js';

// Environment-aware high-resolution timer
let performanceNow: () => number = () => Date.now(); // Fallback

/**
 * Initializes the high-resolution timer based on the environment.
 * In a browser-like environment, it uses `globalThis.performance`.
 * In Node.js, it dynamically imports `perf_hooks`.
 */
/**
 * Dynamically loads Node's perf_hooks module. Exposed for testing to allow
 * mocking the dynamic import path.
 *
 * @returns The Node.js perf_hooks performance interface promise.
 */
export async function loadPerfHooks(): Promise<{
  performance: typeof PerfHooksPerformance;
}> {
  return import('perf_hooks') as Promise<{
    performance: typeof PerfHooksPerformance;
  }>;
}

export async function initializePerformance_Hrt(): Promise<void> {
  // Use a type assertion to safely access `performance` on `globalThis`,
  // which is present in browser-like environments (e.g., Cloudflare Workers)
  // but not in Node.js's default global type.
  const globalWithPerf = globalThis as {
    performance?: { now: () => number };
  };

  if (typeof globalWithPerf.performance?.now === 'function') {
    const perf = globalWithPerf.performance;
    performanceNow = () => perf?.now() ?? Date.now();
  } else {
    try {
      const { performance: nodePerformance } = await loadPerfHooks();
      performanceNow = () => nodePerformance.now();
    } catch (_e) {
      performanceNow = () => Date.now();
      logger.warning(
        'Could not import perf_hooks, falling back to Date.now() for performance timing.',
      );
    }
  }
}

export const nowMs = (): number => performanceNow();

const toBytes = (payload: unknown): number => {
  if (payload == null) return 0;
  try {
    const json = JSON.stringify(payload);
    // Prefer Buffer when available (Node), otherwise TextEncoder (Web/Workers)
    if (
      typeof Buffer !== 'undefined' &&
      typeof Buffer.byteLength === 'function'
    ) {
      const bytes = Buffer.byteLength(json, 'utf8');
      return bytes;
    }
    if (typeof TextEncoder !== 'undefined') {
      return new TextEncoder().encode(json).length;
    }
    return json.length;
  } catch {
    return 0;
  }
};

export async function measureToolExecution<T>(
  toolLogicFn: () => Promise<T>,
  context: RequestContext & { toolName: string },
  inputPayload: unknown,
): Promise<T> {
  const tracer = trace.getTracer(
    config.openTelemetry.serviceName,
    config.openTelemetry.serviceVersion,
  );

  const { toolName } = context;

  return tracer.startActiveSpan(
    `tool_execution:${toolName}` as const,
    async (span) => {
      // Pre-capture lightweight metrics
      const memBefore =
        typeof process !== 'undefined' &&
        typeof process.memoryUsage === 'function'
          ? process.memoryUsage()
          : ({ rss: 0, heapUsed: 0 } as unknown as NodeJS.MemoryUsage);
      const t0 = nowMs();

      span.setAttributes({
        [ATTR_CODE_FUNCTION]: toolName,
        [ATTR_CODE_NAMESPACE]: 'mcp-tools',
        [ATTR_MCP_TOOL_INPUT_BYTES]: toBytes(inputPayload),
        [ATTR_MCP_TOOL_MEMORY_RSS_BEFORE]: memBefore.rss,
        [ATTR_MCP_TOOL_MEMORY_HEAP_USED_BEFORE]: memBefore.heapUsed,
      });

      let ok = false;
      let errorCode: string | undefined;
      let output: T | undefined;

      try {
        const result = await toolLogicFn();
        ok = true;
        output = result;
        span.setStatus({ code: SpanStatusCode.OK });
        span.setAttribute(ATTR_MCP_TOOL_OUTPUT_BYTES, toBytes(output));
        return result;
      } catch (err) {
        if (err instanceof McpError) errorCode = String(err.code);
        else if (err instanceof Error) errorCode = 'UNHANDLED_ERROR';
        else errorCode = 'UNKNOWN_ERROR';

        if (err instanceof Error) span.recordException(err);
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: err instanceof Error ? err.message : String(err),
        });
        throw err;
      } finally {
        const t1 = nowMs();
        const durationMs = Number((t1 - t0).toFixed(2));
        const memAfter =
          typeof process !== 'undefined' &&
          typeof process.memoryUsage === 'function'
            ? process.memoryUsage()
            : ({ rss: 0, heapUsed: 0 } as unknown as NodeJS.MemoryUsage);

        const rssDelta = memAfter.rss - memBefore.rss;
        const heapUsedDelta = memAfter.heapUsed - memBefore.heapUsed;

        span.setAttributes({
          [ATTR_MCP_TOOL_DURATION_MS]: durationMs,
          [ATTR_MCP_TOOL_SUCCESS]: ok,
          [ATTR_MCP_TOOL_MEMORY_RSS_AFTER]: memAfter.rss,
          [ATTR_MCP_TOOL_MEMORY_HEAP_USED_AFTER]: memAfter.heapUsed,
          [ATTR_MCP_TOOL_MEMORY_RSS_DELTA]: rssDelta,
          [ATTR_MCP_TOOL_MEMORY_HEAP_USED_DELTA]: heapUsedDelta,
        });
        if (errorCode) span.setAttribute(ATTR_MCP_TOOL_ERROR_CODE, errorCode);
        span.end();

        logger.info('Tool execution finished.', {
          ...context,
          metrics: {
            durationMs,
            isSuccess: ok,
            errorCode,
            inputBytes: toBytes(inputPayload),
            outputBytes: toBytes(output),
            memory: {
              rss: {
                before: memBefore.rss,
                after: memAfter.rss,
                delta: rssDelta,
              },
              heapUsed: {
                before: memBefore.heapUsed,
                after: memAfter.heapUsed,
                delta: heapUsedDelta,
              },
            },
          },
        });
      }
    },
  );
}
