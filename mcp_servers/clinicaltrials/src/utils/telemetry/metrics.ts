/**
 * @fileoverview OpenTelemetry metrics utilities for custom instrumentation.
 * Provides simplified interfaces for creating and managing counters, histograms,
 * gauges, and observable metrics. Supports both Node and Worker environments.
 * @module src/utils/telemetry/metrics
 */
import {
  metrics,
  type Counter,
  type Histogram,
  type ObservableGauge,
} from '@opentelemetry/api';

import { config } from '@/config/index.js';

/**
 * Gets or creates a meter for custom metrics.
 * Uses application service name and version from config by default.
 *
 * @param name - Optional custom meter name (defaults to service name)
 * @returns Meter instance for creating metrics
 *
 * @example
 * ```typescript
 * const meter = getMeter('database-metrics');
 * const queryCounter = meter.createCounter('db.queries');
 * ```
 */
export function getMeter(name?: string) {
  return metrics.getMeter(
    name ?? config.openTelemetry.serviceName,
    config.openTelemetry.serviceVersion,
  );
}

/**
 * Creates a counter metric (monotonically increasing).
 * Counters are suitable for measuring event counts, request totals, errors, etc.
 *
 * @param name - Metric name (should use dot notation, e.g., 'http.requests')
 * @param description - Human-readable description of what the metric measures
 * @param unit - Optional unit of measurement (e.g., '1', 'requests', 'bytes')
 * @returns Counter instance for recording values
 *
 * @example
 * ```typescript
 * const requestCounter = createCounter(
 *   'api.requests',
 *   'Total number of API requests',
 *   '1'
 * );
 *
 * // Later in code
 * requestCounter.add(1, {
 *   'http.method': 'GET',
 *   'http.route': '/api/users'
 * });
 * ```
 */
export function createCounter(
  name: string,
  description: string,
  unit = '1',
): Counter {
  const meter = getMeter();
  return meter.createCounter(name, { description, unit });
}

/**
 * Creates an up-down counter metric (can increase or decrease).
 * Suitable for tracking values that can go up and down, like active connections.
 *
 * @param name - Metric name (should use dot notation)
 * @param description - Human-readable description
 * @param unit - Optional unit of measurement
 * @returns UpDownCounter instance
 *
 * @example
 * ```typescript
 * const activeConnections = createUpDownCounter(
 *   'connections.active',
 *   'Number of active connections',
 *   '{connections}'
 * );
 *
 * activeConnections.add(1); // New connection
 * activeConnections.add(-1); // Connection closed
 * ```
 */
export function createUpDownCounter(
  name: string,
  description: string,
  unit = '1',
) {
  const meter = getMeter();
  return meter.createUpDownCounter(name, { description, unit });
}

/**
 * Creates a histogram metric for recording distributions.
 * Histograms are ideal for latency, response times, payload sizes, etc.
 *
 * @param name - Metric name (should use dot notation)
 * @param description - Human-readable description
 * @param unit - Optional unit (e.g., 'ms', 'bytes', 's')
 * @returns Histogram instance
 *
 * @example
 * ```typescript
 * const requestDuration = createHistogram(
 *   'http.request.duration',
 *   'HTTP request duration',
 *   'ms'
 * );
 *
 * const startTime = Date.now();
 * // ... handle request ...
 * requestDuration.record(Date.now() - startTime, {
 *   'http.method': 'POST',
 *   'http.status_code': 200
 * });
 * ```
 */
export function createHistogram(
  name: string,
  description: string,
  unit?: string,
): Histogram {
  const meter = getMeter();
  const options = unit ? { description, unit } : { description };
  return meter.createHistogram(name, options);
}

/**
 * Creates an observable gauge for async/callback-based measurements.
 * Gauges are polled periodically by the metrics SDK and report current values.
 * Use for measuring things like memory usage, queue depth, temperature, etc.
 *
 * @param name - Metric name (should use dot notation)
 * @param description - Human-readable description
 * @param callback - Async function returning the current metric value
 * @param unit - Optional unit of measurement
 * @returns ObservableGauge instance
 *
 * @example
 * ```typescript
 * // Monitor heap memory usage
 * createObservableGauge(
 *   'process.memory.heap_used',
 *   'Current heap memory usage',
 *   () => {
 *     if (typeof process !== 'undefined') {
 *       return process.memoryUsage().heapUsed;
 *     }
 *     return 0;
 *   },
 *   'bytes'
 * );
 * ```
 */
export function createObservableGauge(
  name: string,
  description: string,
  _callback: () => Promise<number> | number,
  unit?: string,
): ObservableGauge {
  const meter = getMeter();
  const options = unit ? { description, unit } : { description };
  return meter.createObservableGauge(name, options);
}

/**
 * Creates an observable counter for async/callback-based cumulative measurements.
 * Similar to ObservableGauge but for monotonically increasing values.
 *
 * @param name - Metric name
 * @param description - Human-readable description
 * @param _callback - Async function returning the cumulative count (unused in current implementation)
 * @param unit - Optional unit of measurement
 * @returns ObservableCounter instance
 *
 * @example
 * ```typescript
 * let totalProcessed = 0;
 *
 * createObservableCounter(
 *   'jobs.processed',
 *   'Total jobs processed since startup',
 *   () => totalProcessed,
 *   '{jobs}'
 * );
 * ```
 */
export function createObservableCounter(
  name: string,
  description: string,
  _callback: () => Promise<number> | number,
  unit = '1',
) {
  const meter = getMeter();
  return meter.createObservableCounter(name, { description, unit });
}

/**
 * Creates an observable up-down counter for async/callback-based measurements
 * that can increase or decrease.
 *
 * @param name - Metric name
 * @param description - Human-readable description
 * @param _callback - Async function returning the current value (unused in current implementation)
 * @param unit - Optional unit of measurement
 * @returns ObservableUpDownCounter instance
 *
 * @example
 * ```typescript
 * // Track current queue size
 * createObservableUpDownCounter(
 *   'queue.size',
 *   'Current number of items in queue',
 *   async () => await getQueueSize(),
 *   '{items}'
 * );
 * ```
 */
export function createObservableUpDownCounter(
  name: string,
  description: string,
  _callback: () => Promise<number> | number,
  unit = '1',
) {
  const meter = getMeter();
  return meter.createObservableUpDownCounter(name, { description, unit });
}
