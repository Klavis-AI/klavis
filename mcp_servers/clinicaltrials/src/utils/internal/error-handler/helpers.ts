/**
 * @fileoverview Helper utilities for error inspection and normalization.
 * Enhanced with cause chain extraction and circular reference detection.
 * @module src/utils/internal/error-handler/helpers
 */

import { McpError } from '@/types-global/errors.js';
import { getCompiledPattern } from './mappings.js';

/**
 * Creates a "safe" RegExp for testing error messages with caching.
 * Ensures case-insensitivity and removes the global flag.
 * Now delegates to the compiled pattern cache for better performance.
 * @param pattern - The string or RegExp pattern.
 * @returns A cached RegExp instance.
 */
export function createSafeRegex(pattern: string | RegExp): RegExp {
  return getCompiledPattern(pattern);
}

/**
 * Retrieves a descriptive name for an error object or value.
 * @param error - The error object or value.
 * @returns A string representing the error's name or type.
 */
export function getErrorName(error: unknown): string {
  if (error instanceof Error) {
    return error.name || 'Error';
  }
  if (error === null) {
    return 'NullValueEncountered';
  }
  if (error === undefined) {
    return 'UndefinedValueEncountered';
  }
  if (
    typeof error === 'object' &&
    error !== null &&
    error.constructor &&
    typeof error.constructor.name === 'string' &&
    error.constructor.name !== 'Object'
  ) {
    return `${error.constructor.name}Encountered`;
  }
  return `${typeof error}Encountered`;
}

/**
 * Extracts a message string from an error object or value.
 * @param error - The error object or value.
 * @returns The error message string.
 */
export function getErrorMessage(error: unknown): string {
  try {
    if (error instanceof Error) {
      // AggregateError should surface combined messages succinctly
      if (
        'errors' in error &&
        Array.isArray((error as unknown as { errors: unknown[] }).errors)
      ) {
        const inner = (error as unknown as { errors: unknown[] }).errors
          .map((e) => (e instanceof Error ? e.message : String(e)))
          .filter(Boolean)
          .slice(0, 3)
          .join('; ');
        return inner ? `${error.message}: ${inner}` : error.message;
      }
      return error.message;
    }
    if (error === null) {
      return 'Null value encountered as error';
    }
    if (error === undefined) {
      return 'Undefined value encountered as error';
    }
    if (typeof error === 'string') {
      return error;
    }
    if (typeof error === 'number' || typeof error === 'boolean') {
      return String(error);
    }
    if (typeof error === 'bigint') {
      return error.toString();
    }
    if (typeof error === 'function') {
      return `[function ${error.name || 'anonymous'}]`;
    }
    if (typeof error === 'object') {
      try {
        const json = JSON.stringify(error);
        if (json && json !== '{}') return json;
      } catch {
        // fall through
      }
      const ctor = (error as { constructor?: { name?: string } }).constructor
        ?.name;
      return `Non-Error object encountered (constructor: ${ctor || 'Object'})`;
    }
    if (typeof error === 'symbol') {
      return error.toString();
    }
    // c8 ignore next
    return '[unrepresentable error]';
  } catch (conversionError) {
    return `Error converting error to string: ${conversionError instanceof Error ? conversionError.message : 'Unknown conversion error'}`;
  }
}

/**
 * Represents a node in the error cause chain for structured error analysis.
 */
export interface ErrorCauseNode {
  /** Error name/type */
  name: string;
  /** Error message */
  message: string;
  /** Stack trace if available */
  stack?: string;
  /** Depth in the cause chain (0 = original error) */
  depth: number;
  /** Additional data from McpError instances */
  data?: Record<string, unknown>;
}

/**
 * Extracts the complete error cause chain with circular reference detection.
 * Traverses the error.cause chain up to maxDepth, tracking seen errors to prevent infinite loops.
 * @param error - The error to extract causes from
 * @param maxDepth - Maximum depth to traverse (default: 20)
 * @returns Array of error cause nodes from root to leaf
 *
 * @example
 * ```typescript
 * const chain = extractErrorCauseChain(error);
 * console.log(`Root cause: ${chain[chain.length - 1].message}`);
 * console.log(`Error chain depth: ${chain.length}`);
 * ```
 */
export function extractErrorCauseChain(
  error: unknown,
  maxDepth = 20,
): ErrorCauseNode[] {
  const chain: ErrorCauseNode[] = [];
  const seen = new WeakSet<object>();
  let current = error;
  let depth = 0;

  while (current && depth < maxDepth) {
    // Circular reference detection
    if (typeof current === 'object' && current !== null) {
      if (seen.has(current)) {
        chain.push({
          name: 'CircularReference',
          message: 'Circular reference detected in error cause chain',
          depth,
        });
        break;
      }
      seen.add(current);
    }

    if (current instanceof Error) {
      const node: ErrorCauseNode = {
        name: current.name,
        message: current.message,
        depth,
        // Only include stack if it exists (exact optional property types)
        ...(current.stack !== undefined ? { stack: current.stack } : {}),
      };

      // Extract data from McpError instances
      if (current instanceof McpError && current.data) {
        node.data = current.data;
      }

      chain.push(node);

      // Continue traversing cause chain
      current = current.cause;
    } else if (typeof current === 'string') {
      chain.push({
        name: 'StringError',
        message: current,
        depth,
      });
      break;
    } else {
      chain.push({
        name: getErrorName(current),
        message: getErrorMessage(current),
        depth,
      });
      break;
    }

    depth++;
  }

  if (depth >= maxDepth) {
    chain.push({
      name: 'MaxDepthExceeded',
      message: `Error cause chain exceeded maximum depth of ${maxDepth}`,
      depth,
    });
  }

  return chain;
}

/**
 * Serializes an error cause chain to a structured format for logging and monitoring.
 * @param error - The error to serialize
 * @returns Serialized cause chain object with root cause and full chain
 *
 * @example
 * ```typescript
 * const serialized = serializeErrorCauseChain(error);
 * logger.error('Error occurred', {
 *   rootCause: serialized.rootCause.message,
 *   chainDepth: serialized.totalDepth,
 * });
 * ```
 */
export function serializeErrorCauseChain(error: unknown): {
  rootCause: ErrorCauseNode;
  chain: ErrorCauseNode[];
  totalDepth: number;
} {
  const chain = extractErrorCauseChain(error);
  const rootCause = chain[chain.length - 1] || {
    name: 'Unknown',
    message: 'No error information available',
    depth: 0,
  };

  return {
    rootCause,
    chain,
    totalDepth: chain.length,
  };
}
