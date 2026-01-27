/**
 * @fileoverview Shared type definitions for the error handler utilities.
 * Enhanced with 2025 best practices including Result types, error metadata,
 * severity levels, and recovery strategies for robust error handling.
 * @module src/utils/internal/error-handler/types
 */

import type { JsonRpcErrorCode } from '@/types-global/errors.js';
import type { McpError } from '@/types-global/errors.js';

/**
 * Severity levels for errors, extending beyond basic logging levels.
 * Enables fine-grained categorization and alerting based on error impact.
 */
export enum ErrorSeverity {
  /** Informational errors that don't require action */
  Info = 'info',
  /** Warnings that should be monitored */
  Warning = 'warning',
  /** Errors requiring attention */
  Error = 'error',
  /** Critical errors requiring immediate action */
  Critical = 'critical',
  /** System-threatening errors */
  Fatal = 'fatal',
}

/**
 * Breadcrumb entry for tracking execution path leading to an error.
 * Provides context about operations executed before the error occurred.
 */
export interface ErrorBreadcrumb {
  /** ISO 8601 timestamp when the operation occurred */
  timestamp: string;
  /** Name of the operation that was performed */
  operation: string;
  /** Optional additional context for this breadcrumb */
  context?: Record<string, unknown>;
}

/**
 * Structured metadata attached to errors for enhanced debugging and monitoring.
 * Supports breadcrumbs, metrics, user-facing messages, and error correlation.
 */
export interface ErrorMetadata {
  /** Breadcrumb trail showing error propagation path */
  breadcrumbs?: ErrorBreadcrumb[];
  /** Performance metrics related to the error */
  metrics?: {
    /** Operation duration in milliseconds */
    duration?: number;
    /** Number of retry attempts made */
    retryCount?: number;
  };
  /** User-facing error details (safe for display, sanitized) */
  userFacing?: {
    /** Short title for the error */
    title: string;
    /** Detailed user-friendly message */
    message: string;
    /** Suggested actions the user can take */
    actions?: string[];
  };
  /** Error fingerprint for deduplication in monitoring systems */
  fingerprint?: string;
  /** Related error IDs for correlation across distributed systems */
  relatedErrors?: string[];
}

/**
 * Defines a generic structure for providing context with errors.
 * This context can include identifiers like `requestId` or any other relevant
 * key-value pairs that aid in debugging or understanding the error's circumstances.
 */
export interface ErrorContext {
  /**
   * A unique identifier for the request or operation during which the error occurred.
   * Useful for tracing errors through logs and distributed systems.
   */
  requestId?: string;

  /**
   * Allows for arbitrary additional context information.
   * Keys are strings, and values can be of any type.
   */
  [key: string]: unknown;
}

/**
 * Enhanced error context with metadata support for improved debugging.
 * Extends base ErrorContext with severity, structured metadata, and tags.
 */
export interface EnhancedErrorContext extends ErrorContext {
  /** Severity level of the error */
  severity?: ErrorSeverity;
  /** Structured metadata including breadcrumbs and metrics */
  metadata?: ErrorMetadata;
  /** Arbitrary key-value tags for categorization and filtering */
  tags?: Record<string, string>;
}

/**
 * Configuration options for the `ErrorHandler.handleError` method.
 * These options control how an error is processed, logged, and whether it's rethrown.
 */
export interface ErrorHandlerOptions {
  /**
   * The context of the operation that caused the error.
   * This can include `requestId` and other relevant debugging information.
   */
  context?: ErrorContext;

  /**
   * A descriptive name of the operation being performed when the error occurred.
   * This helps in identifying the source or nature of the error in logs.
   * Example: "UserLogin", "ProcessPayment", "FetchUserProfile".
   */
  operation: string;

  /**
   * The input data or parameters that were being processed when the error occurred.
   * This input will be sanitized before logging to prevent sensitive data exposure.
   */
  input?: unknown;

  /**
   * If true, the (potentially transformed) error will be rethrown after handling.
   * Defaults to `false`.
   */
  rethrow?: boolean;

  /**
   * A specific `JsonRpcErrorCode` to assign to the error, overriding any
   * automatically determined error code.
   */
  errorCode?: JsonRpcErrorCode;

  /**
   * A custom function to map or transform the original error into a new `Error` instance.
   * If provided, this function is used instead of the default `McpError` creation.
   * @param error - The original error that occurred.
   * @returns The transformed error.
   */
  errorMapper?: (error: unknown) => Error;

  /**
   * If true, stack traces will be included in the logs.
   * Defaults to `true`.
   */
  includeStack?: boolean;

  /**
   * If true, indicates that the error is critical and might require immediate attention
   * or could lead to system instability. This is primarily for logging and alerting.
   * Defaults to `false`.
   */
  critical?: boolean;
}

/**
 * Defines a basic rule for mapping errors based on patterns.
 * Used internally by `COMMON_ERROR_PATTERNS` and as a base for `ErrorMapping`.
 */
export interface BaseErrorMapping {
  /**
   * A string or regular expression to match against the error message.
   * If a string is provided, it's typically used for substring matching (case-insensitive).
   */
  pattern: string | RegExp;

  /**
   * The `JsonRpcErrorCode` to assign if the pattern matches.
   */
  errorCode: JsonRpcErrorCode;

  /**
   * An optional custom message template for the mapped error.
   * (Note: This property is defined but not directly used by `ErrorHandler.determineErrorCode`
   * which focuses on `errorCode`. It's more relevant for custom mapping logic.)
   */
  messageTemplate?: string;
}

/**
 * Extends `BaseErrorMapping` to include a factory function for creating
 * specific error instances and additional context for the mapping.
 * Used by `ErrorHandler.mapError`.
 * @template T The type of `Error` this mapping will produce, defaults to `Error`.
 */
export interface ErrorMapping<T extends Error = Error>
  extends BaseErrorMapping {
  /**
   * A factory function that creates and returns an instance of the mapped error type `T`.
   * @param error - The original error that occurred.
   * @param context - Optional additional context provided in the mapping rule.
   * @returns The newly created error instance.
   */
  factory: (error: unknown, context?: Record<string, unknown>) => T;

  /**
   * Additional static context to be merged or passed to the `factory` function
   * when this mapping rule is applied.
   */
  additionalContext?: Record<string, unknown>;
}

/**
 * Result type for functional error handling following Railway Oriented Programming pattern.
 * Explicitly represents success or failure, eliminating implicit exceptions.
 * @template T The success value type
 * @template E The error type, defaults to McpError
 *
 * @example
 * ```typescript
 * const result: Result<User, McpError> = await getUserById(id);
 * if (result.ok) {
 *   console.log('User:', result.value);
 * } else {
 *   console.error('Error:', result.error.message);
 * }
 * ```
 */
export type Result<T, E extends Error = McpError> =
  | { ok: true; value: T; error?: never }
  | { ok: false; value?: never; error: E };

/**
 * Error recovery strategy interface for implementing retry logic and resilience patterns.
 * Defines when and how to retry failed operations with configurable backoff strategies.
 */
export interface ErrorRecoveryStrategy {
  /**
   * Determines if the operation should be retried based on the error and attempt number.
   * @param error - The error that occurred
   * @param attemptNumber - Current attempt number (1-indexed)
   * @returns true if the operation should be retried
   */
  shouldRetry: (error: Error, attemptNumber: number) => boolean;

  /**
   * Calculates the delay before the next retry attempt.
   * Typically implements exponential backoff with optional jitter.
   * @param attemptNumber - Current attempt number (1-indexed)
   * @returns Delay in milliseconds before next retry
   */
  getRetryDelay: (attemptNumber: number) => number;

  /**
   * Maximum number of retry attempts before giving up.
   */
  maxAttempts: number;

  /**
   * Optional callback invoked before each retry attempt.
   * Useful for logging, metrics, or custom retry logic.
   * @param error - The error that triggered the retry
   * @param attemptNumber - Current attempt number (1-indexed)
   */
  onRetry?: (error: Error, attemptNumber: number) => void;
}
