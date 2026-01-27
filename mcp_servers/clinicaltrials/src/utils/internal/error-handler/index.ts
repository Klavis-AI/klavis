/**
 * @fileoverview Barrel exports for the error handler utilities.
 * Enhanced with new 2025 patterns including Result types, cause chain extraction,
 * and compiled error patterns for performance.
 * @module src/utils/internal/error-handler/index
 */

export { ErrorHandler } from './errorHandler.js';
export {
  extractErrorCauseChain,
  serializeErrorCauseChain,
  type ErrorCauseNode,
} from './helpers.js';
export {
  getCompiledPattern,
  COMPILED_ERROR_PATTERNS,
  COMPILED_PROVIDER_PATTERNS,
  PROVIDER_ERROR_PATTERNS,
} from './mappings.js';
export {
  ErrorSeverity,
  type BaseErrorMapping,
  type EnhancedErrorContext,
  type ErrorBreadcrumb,
  type ErrorContext,
  type ErrorHandlerOptions,
  type ErrorMapping,
  type ErrorMetadata,
  type ErrorRecoveryStrategy,
  type Result,
} from './types.js';
