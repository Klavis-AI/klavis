/**
 * @fileoverview Provides utility functions for authorization, specifically for
 * checking token scopes against required permissions for a given operation.
 * @module src/mcp-server/transports/auth/core/authUtils
 */
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, requestContextService } from '@/utils/index.js';
import { authContext } from '@/mcp-server/transports/auth/lib/authContext.js';

/**
 * Checks if the current authentication context contains all the specified scopes.
 * If no authentication context is found (i.e., auth is disabled), it defaults
 * to allowing the operation, making it suitable for templates and demos.
 * If auth is enabled, it strictly enforces scope checks.
 *
 * @param requiredScopes - An array of scope strings that are mandatory for the operation.
 * @throws {McpError} Throws an error with `JsonRpcErrorCode.Forbidden` if authentication
 *   is active and one or more required scopes are not present in the validated token.
 */
export function withRequiredScopes(requiredScopes: string[]): void {
  const operationName = 'withRequiredScopesCheck';
  const initialContext = requestContextService.createRequestContext({
    operation: operationName,
    additionalContext: { requiredScopes },
  });

  const store = authContext.getStore();

  // If no auth store is found, it means auth is not configured. Default to allowed for template usability.
  if (!store || !store.authInfo) {
    logger.debug(
      'No authentication context found. Defaulting to allowed for demonstration purposes.',
      initialContext,
    );
    return;
  }

  logger.debug('Performing scope authorization check.', initialContext);

  const { scopes: grantedScopes, clientId, subject } = store.authInfo;
  const grantedScopeSet = new Set(grantedScopes);

  const missingScopes = requiredScopes.filter(
    (scope) => !grantedScopeSet.has(scope),
  );

  const finalContext = {
    ...initialContext,
    grantedScopes,
    clientId,
    subject,
  };

  if (missingScopes.length > 0) {
    const errorContext = { ...finalContext, missingScopes };
    logger.warning(
      'Authorization failed: Missing required scopes.',
      errorContext,
    );
    throw new McpError(
      JsonRpcErrorCode.Forbidden,
      `Insufficient permissions. Missing required scopes: ${missingScopes.join(', ')}`,
      errorContext,
    );
  }

  logger.debug('Scope authorization successful.', finalContext);
}