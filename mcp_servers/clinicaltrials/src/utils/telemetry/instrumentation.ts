/**
 * @fileoverview OpenTelemetry SDK initialization and lifecycle management.
 * Provides runtime-aware initialization with graceful degradation for Worker/Edge environments.
 * Supports both Node.js (full NodeSDK) and serverless runtimes (lightweight telemetry).
 * @module src/utils/telemetry/instrumentation
 */
import { config } from '@/config/index.js';
import { DiagConsoleLogger, DiagLogLevel, diag } from '@opentelemetry/api';
import type { NodeSDK } from '@opentelemetry/sdk-node';

import { runtimeCaps } from '@/utils/internal/runtime.js';

// Node-specific imports are lazy-loaded to avoid Worker crashes
// SDK instance is exported for internal access if needed
export let sdk: NodeSDK | null = null;

// Initialization state management
let isOtelInitialized = false;
let initializationPromise: Promise<void> | null = null;

/**
 * Determines if the NodeSDK can be used in the current runtime.
 * Returns false in Worker/Edge environments where Node modules are unavailable.
 */
function canUseNodeSDK(): boolean {
  return (
    runtimeCaps.isNode &&
    typeof process?.versions?.node === 'string' &&
    typeof process.env === 'object'
  );
}

/**
 * Detects cloud platform and provider for resource attributes.
 * Enriches telemetry with deployment environment metadata.
 *
 * @returns Record of cloud-related resource attributes
 */
function detectCloudResource(): Record<string, string> {
  const attrs: Record<string, string> = {};

  // Cloudflare Workers
  if (runtimeCaps.isWorkerLike) {
    attrs['cloud.provider'] = 'cloudflare';
    attrs['cloud.platform'] = 'cloudflare_workers';
  }

  // AWS Lambda
  if (typeof process !== 'undefined' && process.env?.AWS_LAMBDA_FUNCTION_NAME) {
    attrs['cloud.provider'] = 'aws';
    attrs['cloud.platform'] = 'aws_lambda';
    if (process.env.AWS_REGION) {
      attrs['cloud.region'] = process.env.AWS_REGION;
    }
  }

  // GCP Cloud Functions/Cloud Run
  if (
    typeof process !== 'undefined' &&
    (process.env?.FUNCTION_TARGET || process.env?.K_SERVICE)
  ) {
    attrs['cloud.provider'] = 'gcp';
    attrs['cloud.platform'] = process.env.FUNCTION_TARGET
      ? 'gcp_cloud_functions'
      : 'gcp_cloud_run';
    if (process.env.GCP_REGION) {
      attrs['cloud.region'] = process.env.GCP_REGION;
    }
  }

  attrs['deployment.environment.name'] = config.environment;

  return attrs;
}

/**
 * Initializes OpenTelemetry SDK with runtime-appropriate configuration.
 * This function is idempotent and safe to call multiple times.
 * Completes successfully even if telemetry is disabled or runtime is incompatible.
 *
 * @returns Promise that resolves when initialization is complete
 *
 * @example
 * ```typescript
 * // In application entry point (src/index.ts)
 * await initializeOpenTelemetry();
 * ```
 */
export async function initializeOpenTelemetry(): Promise<void> {
  // Return existing promise if initialization in progress
  if (initializationPromise) {
    return initializationPromise;
  }

  // Already initialized
  if (isOtelInitialized) {
    return;
  }

  initializationPromise = (async () => {
    if (!config.openTelemetry.enabled) {
      diag.info('OpenTelemetry disabled via configuration.');
      isOtelInitialized = true;
      return;
    }

    if (!canUseNodeSDK()) {
      diag.info(
        'NodeSDK unavailable in this runtime. Using lightweight telemetry mode.',
      );
      isOtelInitialized = true;
      return;
    }

    isOtelInitialized = true;

    try {
      // Lazy-load Node-specific modules
      const [
        { getNodeAutoInstrumentations },
        { OTLPMetricExporter },
        { OTLPTraceExporter },
        { PinoInstrumentation },
        { resourceFromAttributes },
        { PeriodicExportingMetricReader },
        { NodeSDK },
        { BatchSpanProcessor, TraceIdRatioBasedSampler },
        { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION },
      ] = await Promise.all([
        import('@opentelemetry/auto-instrumentations-node'),
        import('@opentelemetry/exporter-metrics-otlp-http'),
        import('@opentelemetry/exporter-trace-otlp-http'),
        import('@opentelemetry/instrumentation-pino'),
        import('@opentelemetry/resources'),
        import('@opentelemetry/sdk-metrics'),
        import('@opentelemetry/sdk-node'),
        import('@opentelemetry/sdk-trace-node'),
        import('@opentelemetry/semantic-conventions/incubating'),
      ]);

      const otelLogLevelString =
        config.openTelemetry.logLevel.toUpperCase() as keyof typeof DiagLogLevel;
      const otelLogLevel =
        DiagLogLevel[otelLogLevelString] ?? DiagLogLevel.INFO;
      diag.setLogger(new DiagConsoleLogger(), otelLogLevel);

      const tracesEndpoint = config.openTelemetry.tracesEndpoint;
      const metricsEndpoint = config.openTelemetry.metricsEndpoint;

      if (!tracesEndpoint && !metricsEndpoint) {
        diag.warn(
          'OTEL_ENABLED is true, but no OTLP endpoint for traces or metrics is configured. OpenTelemetry will not export any telemetry.',
        );
      }

      const resource = resourceFromAttributes({
        [ATTR_SERVICE_NAME]: config.openTelemetry.serviceName,
        [ATTR_SERVICE_VERSION]: config.openTelemetry.serviceVersion,
        ...detectCloudResource(),
      });

      const spanProcessors: InstanceType<typeof BatchSpanProcessor>[] = [];
      if (tracesEndpoint) {
        diag.info(
          `Using OTLP exporter for traces, endpoint: ${tracesEndpoint}`,
        );
        const traceExporter = new OTLPTraceExporter({ url: tracesEndpoint });
        spanProcessors.push(new BatchSpanProcessor(traceExporter));
      } else {
        diag.info(
          'No OTLP traces endpoint configured. Traces will not be exported.',
        );
      }

      const metricReader = metricsEndpoint
        ? new PeriodicExportingMetricReader({
            exporter: new OTLPMetricExporter({ url: metricsEndpoint }),
            exportIntervalMillis: 15000,
          })
        : undefined;

      sdk = new NodeSDK({
        resource,
        spanProcessors,
        ...(metricReader && { metricReader }),
        sampler: new TraceIdRatioBasedSampler(
          config.openTelemetry.samplingRatio,
        ),
        instrumentations: [
          getNodeAutoInstrumentations({
            '@opentelemetry/instrumentation-http': {
              enabled: true,
              ignoreIncomingRequestHook: (req) => req.url === '/healthz',
            },
            '@opentelemetry/instrumentation-fs': { enabled: false },
          }),
          new PinoInstrumentation({
            logHook: (_span, record) => {
              record['trace_id'] = _span.spanContext().traceId;
              record['span_id'] = _span.spanContext().spanId;
            },
          }),
        ],
      });

      sdk.start();
      diag.info(
        `OpenTelemetry NodeSDK initialized for ${config.openTelemetry.serviceName} v${config.openTelemetry.serviceVersion}`,
      );
    } catch (error) {
      diag.error('Error initializing OpenTelemetry', error);
      sdk = null;
      throw error;
    }
  })();

  return initializationPromise;
}

/**
 * Gracefully shuts down the OpenTelemetry SDK with timeout protection.
 * This function is called during the application's shutdown sequence.
 * Prevents hung processes by racing shutdown against a timeout.
 *
 * @param timeoutMs - Maximum time to wait for shutdown in milliseconds (default: 5000)
 * @throws Error if shutdown times out or fails critically
 *
 * @example
 * ```typescript
 * // During application shutdown
 * try {
 *   await shutdownOpenTelemetry();
 * } catch (error) {
 *   console.error('Failed to shutdown telemetry:', error);
 * }
 * ```
 */
export async function shutdownOpenTelemetry(timeoutMs = 5000): Promise<void> {
  if (!sdk) {
    return;
  }

  try {
    const shutdownPromise = sdk.shutdown();
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(
        () => reject(new Error('OpenTelemetry SDK shutdown timeout')),
        timeoutMs,
      ),
    );

    await Promise.race([shutdownPromise, timeoutPromise]);
    diag.info('OpenTelemetry SDK terminated successfully.');
  } catch (error) {
    diag.error('Error terminating OpenTelemetry SDK', error);
    throw error; // Propagate for caller handling
  } finally {
    sdk = null;
    isOtelInitialized = false;
    initializationPromise = null;
  }
}
