/**
 * @fileoverview Main ErrorHandler implementation with logging and telemetry integration.
 * Enhanced with Result types, breadcrumb tracking, error sanitization, and retry logic.
 * @module src/utils/internal/error-handler/errorHandler
 */

import { SpanStatusCode, trace } from '@opentelemetry/api';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { generateUUID, sanitizeInputForLogging } from '@/utils/index.js';
import { logger } from '@/utils/internal/logger.js';
import type { RequestContext } from '@/utils/internal/requestContext.js';

import {
  COMPILED_ERROR_PATTERNS,
  COMPILED_PROVIDER_PATTERNS,
  ERROR_TYPE_MAPPINGS,
} from './mappings.js';
import {
  createSafeRegex,
  extractErrorCauseChain,
  getErrorMessage,
  getErrorName,
} from './helpers.js';
import type {
  EnhancedErrorContext,
  ErrorHandlerOptions,
  ErrorMapping,
  ErrorRecoveryStrategy,
  Result,
} from './types.js';

/**
 * A utility class providing static methods for comprehensive error handling.
 */
export class ErrorHandler {
  /**
   * Determines an appropriate `JsonRpcErrorCode` for a given error.
   * Checks `McpError` instances, `ERROR_TYPE_MAPPINGS`, and pre-compiled error patterns.
   * Now includes provider-specific patterns for better external service error classification.
   * Defaults to `JsonRpcErrorCode.InternalError`.
   * @param error - The error instance or value to classify.
   * @returns The determined error code.
   */
  public static determineErrorCode(error: unknown): JsonRpcErrorCode {
    if (error instanceof McpError) {
      return error.code;
    }

    const errorName = getErrorName(error);
    const errorMessage = getErrorMessage(error);

    // Check against standard JavaScript error types
    const mappedFromType = (
      ERROR_TYPE_MAPPINGS as Record<string, JsonRpcErrorCode>
    )[errorName];
    if (mappedFromType) {
      return mappedFromType;
    }

    // Check provider-specific patterns first (more specific)
    for (const mapping of COMPILED_PROVIDER_PATTERNS) {
      if (
        mapping.compiledPattern.test(errorMessage) ||
        mapping.compiledPattern.test(errorName)
      ) {
        return mapping.errorCode;
      }
    }

    // Then check common error patterns (using pre-compiled patterns for performance)
    for (const mapping of COMPILED_ERROR_PATTERNS) {
      if (
        mapping.compiledPattern.test(errorMessage) ||
        mapping.compiledPattern.test(errorName)
      ) {
        return mapping.errorCode;
      }
    }
    // Special-case common platform errors
    if (
      typeof error === 'object' &&
      error !== null &&
      'name' in error &&
      (error as { name?: string }).name === 'AbortError'
    ) {
      return JsonRpcErrorCode.Timeout;
    }
    return JsonRpcErrorCode.InternalError;
  }

  /**
   * Handles an error with consistent logging and optional transformation.
   * Sanitizes input, determines error code, logs details, and can rethrow.
   * @param error - The error instance or value that occurred.
   * @param options - Configuration for handling the error.
   * @returns The handled (and potentially transformed) error instance.
   */
  public static handleError(
    error: unknown,
    options: ErrorHandlerOptions,
  ): Error {
    // --- OpenTelemetry Integration ---
    const activeSpan = trace.getActiveSpan();
    if (activeSpan) {
      if (error instanceof Error) {
        activeSpan.recordException(error);
      }
      activeSpan.setStatus({
        code: SpanStatusCode.ERROR,
        message: error instanceof Error ? error.message : String(error),
      });
    }
    // --- End OpenTelemetry Integration ---

    const {
      context = {},
      operation,
      input,
      rethrow = false,
      errorCode: explicitErrorCode,
      includeStack = true,
      critical = false,
      errorMapper,
    } = options;

    const sanitizedInput =
      input !== undefined ? sanitizeInputForLogging(input) : undefined;
    const originalErrorName = getErrorName(error);
    const originalErrorMessage = getErrorMessage(error);
    const originalStack = error instanceof Error ? error.stack : undefined;

    let finalError: Error;
    let loggedErrorCode: JsonRpcErrorCode;

    const errorDataSeed =
      error instanceof McpError &&
      typeof error.data === 'object' &&
      error.data !== null
        ? { ...error.data }
        : {};

    const consolidatedData: Record<string, unknown> = {
      ...errorDataSeed,
      ...context,
      originalErrorName,
      originalMessage: originalErrorMessage,
    };
    if (
      originalStack &&
      !(error instanceof McpError && error.data?.originalStack)
    ) {
      consolidatedData.originalStack = originalStack;
    }

    const cause = error instanceof Error ? error : undefined;

    // Extract full cause chain with circular reference detection
    const causeChain = extractErrorCauseChain(error);
    if (causeChain.length > 0) {
      const rootCause = causeChain[causeChain.length - 1];
      if (rootCause) {
        consolidatedData['rootCause'] = {
          name: rootCause.name,
          message: rootCause.message,
        };
      }
      consolidatedData['causeChain'] = causeChain;
    }

    // Add breadcrumbs from enhanced context if present
    if (
      context &&
      'metadata' in context &&
      context.metadata &&
      typeof context.metadata === 'object' &&
      'breadcrumbs' in context.metadata
    ) {
      consolidatedData['breadcrumbs'] = context.metadata.breadcrumbs;
    }

    if (error instanceof McpError) {
      loggedErrorCode = error.code;
      finalError = errorMapper
        ? errorMapper(error)
        : new McpError(error.code, error.message, consolidatedData, {
            cause,
          });
    } else {
      loggedErrorCode =
        explicitErrorCode || ErrorHandler.determineErrorCode(error);
      const message = `Error in ${operation}: ${originalErrorMessage}`;
      finalError = errorMapper
        ? errorMapper(error)
        : new McpError(loggedErrorCode, message, consolidatedData, {
            cause,
          });
    }

    if (
      finalError !== error &&
      error instanceof Error &&
      finalError instanceof Error &&
      !finalError.stack &&
      error.stack
    ) {
      finalError.stack = error.stack;
    }

    const logRequestId =
      typeof context.requestId === 'string' && context.requestId
        ? context.requestId
        : generateUUID();

    const logTimestamp =
      typeof context.timestamp === 'string' && context.timestamp
        ? context.timestamp
        : new Date().toISOString();

    const stack =
      finalError instanceof Error ? finalError.stack : originalStack;
    const logContext: RequestContext = {
      requestId: logRequestId,
      timestamp: logTimestamp,
      operation,
      input: sanitizedInput,
      critical,
      errorCode: loggedErrorCode,
      originalErrorType: originalErrorName,
      finalErrorType: getErrorName(finalError),
      ...Object.fromEntries(
        Object.entries(context).filter(
          ([key]) => key !== 'requestId' && key !== 'timestamp',
        ),
      ),
      errorData:
        finalError instanceof McpError && finalError.data
          ? finalError.data
          : consolidatedData,
      ...(includeStack && stack ? { stack } : {}),
    };

    logger.error(
      `Error in ${operation}: ${finalError.message || originalErrorMessage}`,
      logContext,
    );

    if (rethrow) {
      throw finalError;
    }
    return finalError;
  }

  /**
   * Maps an error to a specific error type `T` based on `ErrorMapping` rules.
   * Returns original/default error if no mapping matches.
   * @template T The target error type, extending `Error`.
   * @param error - The error instance or value to map.
   * @param mappings - An array of mapping rules to apply.
   * @param defaultFactory - Optional factory for a default error if no mapping matches.
   * @returns The mapped error of type `T`, or the original/defaulted error.
   */
  public static mapError<T extends Error>(
    error: unknown,
    mappings: ReadonlyArray<ErrorMapping<T>>,
    defaultFactory?: (error: unknown, context?: Record<string, unknown>) => T,
  ): T | Error {
    const errorMessage = getErrorMessage(error);
    const errorName = getErrorName(error);

    for (const mapping of mappings) {
      const regex = createSafeRegex(mapping.pattern);
      if (regex.test(errorMessage) || regex.test(errorName)) {
        // c8 ignore next
        return mapping.factory(error, mapping.additionalContext);
      }
    }

    if (defaultFactory) {
      return defaultFactory(error);
    }
    return error instanceof Error ? error : new Error(String(error));
  }

  /**
   * Formats an error into a consistent object structure for API responses or structured logging.
   * @param error - The error instance or value to format.
   * @returns A structured representation of the error.
   */
  public static formatError(error: unknown): Record<string, unknown> {
    if (error instanceof McpError) {
      return {
        code: error.code,
        message: error.message,
        data:
          typeof error.data === 'object' && error.data !== null
            ? error.data
            : {},
      };
    }

    if (error instanceof Error) {
      return {
        code: ErrorHandler.determineErrorCode(error),
        message: error.message,
        data: { errorType: error.name || 'Error' },
      };
    }

    return {
      code: JsonRpcErrorCode.UnknownError,
      message: getErrorMessage(error),
      data: { errorType: getErrorName(error) },
    };
  }

  /**
   * Safely executes a function (sync or async) and handles errors using `ErrorHandler.handleError`.
   * The error is always rethrown.
   * @template T The expected return type of the function `fn`.
   * @param fn - The function to execute.
   * @param options - Error handling options (excluding `rethrow`).
   * @returns A promise resolving with the result of `fn` if successful.
   * @throws {McpError | Error} The error processed by `ErrorHandler.handleError`.
   */
  public static async tryCatch<T>(
    fn: () => Promise<T> | T,
    options: Omit<ErrorHandlerOptions, 'rethrow'>,
  ): Promise<T> {
    try {
      return await Promise.resolve(fn());
    } catch (caughtError) {
      // ErrorHandler.handleError will return the error to be thrown.
      throw ErrorHandler.handleError(caughtError, {
        ...options,
        rethrow: true,
      });
    }
  }

  /**
   * Executes a function and returns a Result type instead of throwing.
   * Enables functional error handling following Railway Oriented Programming pattern.
   * @template T The expected return type
   * @param fn - The function to execute
   * @param options - Error handling options (excluding `rethrow`)
   * @returns Result<T, McpError> - Success or error wrapped in Result type
   *
   * @example
   * ```typescript
   * const result = await ErrorHandler.tryAsResult(
   *   () => dangerousOperation(),
   *   { operation: 'dangerousOp', context }
   * );
   *
   * if (result.ok) {
   *   console.log('Success:', result.value);
   * } else {
   *   console.error('Error:', result.error.message);
   * }
   * ```
   */
  public static async tryAsResult<T>(
    fn: () => Promise<T> | T,
    options: Omit<ErrorHandlerOptions, 'rethrow'>,
  ): Promise<Result<T, McpError>> {
    try {
      const value = await Promise.resolve(fn());
      return { ok: true, value };
    } catch (caughtError) {
      const error = ErrorHandler.handleError(caughtError, {
        ...options,
        rethrow: false,
      }) as McpError;
      return { ok: false, error };
    }
  }

  /**
   * Helper to map a Result value through a transformation function.
   * @template T Input type
   * @template U Output type
   * @param result - The result to map
   * @param fn - Transformation function
   * @returns Mapped result
   *
   * @example
   * ```typescript
   * const userResult = await getUserById(id);
   * const nameResult = ErrorHandler.mapResult(userResult, user => user.name);
   * ```
   */
  public static mapResult<T, U>(
    result: Result<T, McpError>,
    fn: (value: T) => U,
  ): Result<U, McpError> {
    if (result.ok) {
      try {
        return { ok: true, value: fn(result.value) };
      } catch (error) {
        return {
          ok: false,
          error: new McpError(
            JsonRpcErrorCode.InternalError,
            `Error mapping result: ${getErrorMessage(error)}`,
          ),
        };
      }
    }
    return result;
  }

  /**
   * Helper to chain Result-returning operations (flatMap / bind).
   * @template T Input type
   * @template U Output type
   * @param result - The result to chain
   * @param fn - Function that returns a new Result
   * @returns Chained result
   *
   * @example
   * ```typescript
   * const userResult = await getUserById(id);
   * const postsResult = ErrorHandler.flatMapResult(
   *   userResult,
   *   user => getPostsByUserId(user.id)
   * );
   * ```
   */
  public static flatMapResult<T, U>(
    result: Result<T, McpError>,
    fn: (value: T) => Result<U, McpError>,
  ): Result<U, McpError> {
    if (result.ok) {
      return fn(result.value);
    }
    return result;
  }

  /**
   * Provides a fallback value if Result is an error.
   * @template T Value type
   * @param result - The result to recover from
   * @param fallback - Fallback value or function
   * @returns T value (either success value or fallback)
   *
   * @example
   * ```typescript
   * const user = ErrorHandler.recoverResult(
   *   userResult,
   *   { id: 'guest', name: 'Guest User' }
   * );
   * ```
   */
  public static recoverResult<T>(
    result: Result<T, McpError>,
    fallback: T | ((error: McpError) => T),
  ): T {
    if (result.ok) {
      return result.value;
    }
    return typeof fallback === 'function'
      ? (fallback as (error: McpError) => T)(result.error)
      : fallback;
  }

  /**
   * Adds a breadcrumb to the error context for tracking execution path.
   * @param context - The request context to add breadcrumb to
   * @param operation - Operation name
   * @param additionalData - Optional additional context
   * @returns Updated context with breadcrumb
   *
   * @example
   * ```typescript
   * let context = requestContextService.createRequestContext({ operation: 'initial' });
   * context = ErrorHandler.addBreadcrumb(context as EnhancedErrorContext, 'step1');
   * context = ErrorHandler.addBreadcrumb(context, 'step2', { userId: '123' });
   * ```
   */
  public static addBreadcrumb(
    context: EnhancedErrorContext,
    operation: string,
    additionalData?: Record<string, unknown>,
  ): EnhancedErrorContext {
    const breadcrumbs = context.metadata?.breadcrumbs || [];

    breadcrumbs.push({
      timestamp: new Date().toISOString(),
      operation,
      // Only include context if it exists (exact optional property types)
      ...(additionalData !== undefined ? { context: additionalData } : {}),
    });

    return {
      ...context,
      metadata: {
        ...context.metadata,
        breadcrumbs,
      },
    };
  }

  /**
   * Executes a function with automatic retry logic and exponential backoff.
   * Implements resilience patterns for distributed systems.
   * @template T Return type
   * @param fn - Function to execute
   * @param options - Error handling options
   * @param strategy - Retry strategy configuration
   * @returns Promise resolving to result or throwing after exhausting retries
   *
   * @example
   * ```typescript
   * const strategy = ErrorHandler.createExponentialBackoffStrategy(3);
   * const result = await ErrorHandler.tryCatchWithRetry(
   *   () => fetchFromUnreliableAPI(),
   *   { operation: 'fetchAPI', context },
   *   strategy
   * );
   * ```
   */
  public static async tryCatchWithRetry<T>(
    fn: () => Promise<T> | T,
    options: Omit<ErrorHandlerOptions, 'rethrow'>,
    strategy: ErrorRecoveryStrategy,
  ): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= strategy.maxAttempts; attempt++) {
      try {
        return await Promise.resolve(fn());
      } catch (caughtError) {
        lastError =
          caughtError instanceof Error
            ? caughtError
            : new Error(String(caughtError));

        if (
          attempt < strategy.maxAttempts &&
          strategy.shouldRetry(lastError, attempt)
        ) {
          const delay = strategy.getRetryDelay(attempt);

          const retryContext: RequestContext = {
            ...options.context,
            requestId: (options.context?.requestId as string) || generateUUID(),
            timestamp: new Date().toISOString(),
            operation: options.operation,
            error: lastError.message,
            attempt,
          };

          logger.warning(
            `Retry attempt ${attempt}/${strategy.maxAttempts} after ${delay}ms`,
            retryContext,
          );

          strategy.onRetry?.(lastError, attempt);

          // Wait before retry
          await new Promise((resolve) => setTimeout(resolve, delay));
        } else {
          // Max attempts reached or error not retryable
          throw ErrorHandler.handleError(lastError, {
            ...options,
            rethrow: true,
            context: {
              ...options.context,
              retryAttempts: attempt,
              finalAttempt: true,
            },
          });
        }
      }
    }

    // Should never reach here, but TypeScript requires it
    throw ErrorHandler.handleError(lastError!, {
      ...options,
      rethrow: true,
    });
  }

  /**
   * Creates a default exponential backoff retry strategy.
   * @param maxAttempts - Maximum retry attempts (default: 3)
   * @param baseDelay - Base delay in ms (default: 1000)
   * @param maxDelay - Maximum delay in ms (default: 30000)
   * @returns ErrorRecoveryStrategy
   *
   * @example
   * ```typescript
   * const strategy = ErrorHandler.createExponentialBackoffStrategy(5, 500, 10000);
   * ```
   */
  public static createExponentialBackoffStrategy(
    maxAttempts = 3,
    baseDelay = 1000,
    maxDelay = 30000,
  ): ErrorRecoveryStrategy {
    return {
      maxAttempts,
      shouldRetry: (error: Error) => {
        // Don't retry on validation errors or unauthorized
        if (error instanceof McpError) {
          const nonRetryableCodes = [
            JsonRpcErrorCode.ValidationError,
            JsonRpcErrorCode.Unauthorized,
            JsonRpcErrorCode.Forbidden,
            JsonRpcErrorCode.NotFound,
          ];
          return !nonRetryableCodes.includes(error.code);
        }
        return true;
      },
      getRetryDelay: (attemptNumber: number) => {
        // Exponential backoff: baseDelay * 2^(attempt - 1) with jitter
        const exponentialDelay = baseDelay * Math.pow(2, attemptNumber - 1);
        const jitter = Math.random() * 0.3 * exponentialDelay; // 30% jitter
        return Math.min(exponentialDelay + jitter, maxDelay);
      },
    };
  }
}
