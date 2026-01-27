/**
 * @fileoverview Shared error classification constants used by the error handler.
 * Enhanced with regex caching for performance and provider-specific error patterns.
 * @module src/utils/internal/error-handler/mappings
 */

import { JsonRpcErrorCode } from '@/types-global/errors.js';
import type { BaseErrorMapping } from './types.js';

/**
 * Compiled regex cache for performance optimization.
 * Prevents repeated regex compilation on every error classification.
 * @private
 */
const COMPILED_PATTERN_CACHE = new Map<string, RegExp>();

/**
 * Compiles and caches regex patterns at first use for faster matching.
 * Automatically adds case-insensitive flag and removes global flag for safety.
 * @param pattern - Pattern to compile (string or RegExp)
 * @returns Compiled and cached RegExp instance
 */
export function getCompiledPattern(pattern: string | RegExp): RegExp {
  // Create a stable cache key
  const cacheKey =
    pattern instanceof RegExp ? pattern.source + pattern.flags : pattern;

  // Return cached pattern if available
  if (COMPILED_PATTERN_CACHE.has(cacheKey)) {
    return COMPILED_PATTERN_CACHE.get(cacheKey)!;
  }

  // Compile new pattern
  let compiled: RegExp;
  if (pattern instanceof RegExp) {
    // Remove global flag, ensure case-insensitive
    let flags = pattern.flags.replace('g', '');
    if (!flags.includes('i')) {
      flags += 'i';
    }
    compiled = new RegExp(pattern.source, flags);
  } else {
    compiled = new RegExp(pattern, 'i');
  }

  // Cache for future use
  COMPILED_PATTERN_CACHE.set(cacheKey, compiled);
  return compiled;
}

/**
 * Extended error mapping interface that includes pre-compiled regex pattern.
 * @private
 */
interface CompiledErrorMapping extends BaseErrorMapping {
  /** Pre-compiled regex pattern for efficient matching */
  compiledPattern: RegExp;
}

/**
 * Maps standard JavaScript error constructor names to `JsonRpcErrorCode` values.
 */
export const ERROR_TYPE_MAPPINGS: Readonly<Record<string, JsonRpcErrorCode>> = {
  SyntaxError: JsonRpcErrorCode.ValidationError,
  TypeError: JsonRpcErrorCode.ValidationError,
  ReferenceError: JsonRpcErrorCode.InternalError,
  RangeError: JsonRpcErrorCode.ValidationError,
  URIError: JsonRpcErrorCode.ValidationError,
  EvalError: JsonRpcErrorCode.InternalError,
  AggregateError: JsonRpcErrorCode.InternalError,
};

/**
 * Array of `BaseErrorMapping` rules to classify errors by message/name patterns.
 * Order matters: more specific patterns should precede generic ones.
 */
export const COMMON_ERROR_PATTERNS: ReadonlyArray<Readonly<BaseErrorMapping>> =
  [
    {
      pattern:
        /auth|unauthorized|unauthenticated|not.*logged.*in|invalid.*token|expired.*token/i,
      errorCode: JsonRpcErrorCode.Unauthorized,
    },
    {
      pattern: /permission|forbidden|access.*denied|not.*allowed/i,
      errorCode: JsonRpcErrorCode.Forbidden,
    },
    {
      pattern: /not found|missing|no such|doesn't exist|couldn't find/i,
      errorCode: JsonRpcErrorCode.NotFound,
    },
    {
      pattern:
        /invalid|validation|malformed|bad request|wrong format|missing required/i,
      errorCode: JsonRpcErrorCode.ValidationError,
    },
    {
      pattern: /conflict|already exists|duplicate|unique constraint/i,
      errorCode: JsonRpcErrorCode.Conflict,
    },
    {
      pattern: /rate limit|too many requests|throttled/i,
      errorCode: JsonRpcErrorCode.RateLimited,
    },
    {
      pattern: /timeout|timed out|deadline exceeded/i,
      errorCode: JsonRpcErrorCode.Timeout,
    },
    {
      pattern: /abort(ed)?|cancell?ed/i,
      errorCode: JsonRpcErrorCode.Timeout,
    },
    {
      pattern:
        /service unavailable|bad gateway|gateway timeout|upstream error/i,
      errorCode: JsonRpcErrorCode.ServiceUnavailable,
    },
    {
      pattern: /zod|zoderror|schema validation/i,
      errorCode: JsonRpcErrorCode.ValidationError,
    },
  ];

/**
 * Pre-compiled error patterns for performance optimization.
 * These patterns are compiled once at module initialization for faster matching.
 * Use these in performance-critical paths instead of COMMON_ERROR_PATTERNS.
 */
export const COMPILED_ERROR_PATTERNS: ReadonlyArray<
  Readonly<CompiledErrorMapping>
> = COMMON_ERROR_PATTERNS.map((mapping) => ({
  ...mapping,
  compiledPattern: getCompiledPattern(mapping.pattern),
}));

/**
 * Provider-specific error patterns for external service integration.
 * Covers common error formats from AWS, HTTP status codes, databases, and LLM providers.
 */
export const PROVIDER_ERROR_PATTERNS: ReadonlyArray<
  Readonly<BaseErrorMapping>
> = [
  // AWS Service Errors
  {
    pattern: /ThrottlingException|TooManyRequestsException/i,
    errorCode: JsonRpcErrorCode.RateLimited,
  },
  {
    pattern: /AccessDenied|UnauthorizedOperation/i,
    errorCode: JsonRpcErrorCode.Forbidden,
  },
  {
    pattern: /ResourceNotFoundException/i,
    errorCode: JsonRpcErrorCode.NotFound,
  },

  // HTTP Status-based errors
  { pattern: /status code 401/i, errorCode: JsonRpcErrorCode.Unauthorized },
  { pattern: /status code 403/i, errorCode: JsonRpcErrorCode.Forbidden },
  { pattern: /status code 404/i, errorCode: JsonRpcErrorCode.NotFound },
  { pattern: /status code 409/i, errorCode: JsonRpcErrorCode.Conflict },
  { pattern: /status code 429/i, errorCode: JsonRpcErrorCode.RateLimited },
  {
    pattern: /status code 5\d\d/i,
    errorCode: JsonRpcErrorCode.ServiceUnavailable,
  },

  // Database connection and constraint errors
  {
    pattern: /ECONNREFUSED|connection refused/i,
    errorCode: JsonRpcErrorCode.ServiceUnavailable,
  },
  {
    pattern: /ETIMEDOUT|connection timeout/i,
    errorCode: JsonRpcErrorCode.Timeout,
  },
  {
    pattern: /unique constraint|duplicate key/i,
    errorCode: JsonRpcErrorCode.Conflict,
  },
  {
    pattern: /foreign key constraint/i,
    errorCode: JsonRpcErrorCode.ValidationError,
  },

  // Supabase-specific errors
  { pattern: /JWT expired/i, errorCode: JsonRpcErrorCode.Unauthorized },
  {
    pattern: /row level security/i,
    errorCode: JsonRpcErrorCode.Forbidden,
  },

  // OpenRouter/LLM provider errors
  {
    pattern: /insufficient_quota|quota exceeded/i,
    errorCode: JsonRpcErrorCode.RateLimited,
  },
  { pattern: /model_not_found/i, errorCode: JsonRpcErrorCode.NotFound },
  {
    pattern: /context_length_exceeded/i,
    errorCode: JsonRpcErrorCode.ValidationError,
  },

  // Network errors
  { pattern: /ENOTFOUND|DNS/i, errorCode: JsonRpcErrorCode.ServiceUnavailable },
  {
    pattern: /ECONNRESET|connection reset/i,
    errorCode: JsonRpcErrorCode.ServiceUnavailable,
  },
];

/**
 * Pre-compiled provider error patterns for performance.
 */
export const COMPILED_PROVIDER_PATTERNS: ReadonlyArray<
  Readonly<CompiledErrorMapping>
> = PROVIDER_ERROR_PATTERNS.map((mapping) => ({
  ...mapping,
  compiledPattern: getCompiledPattern(mapping.pattern),
}));
