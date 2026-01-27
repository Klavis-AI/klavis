/**
 * @fileoverview Defines a unified Hono middleware for authentication.
 * This middleware is strategy-agnostic. It extracts a Bearer token,
 * delegates verification to the provided authentication strategy, and
 * populates the async-local storage context with the resulting auth info.
 * @module src/mcp-server/transports/auth/authMiddleware
 */
import { trace } from '@opentelemetry/api';
import type { HttpBindings } from '@hono/node-server';
import type { Context, Next } from 'hono';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { ErrorHandler, logger, requestContextService } from '@/utils/index.js';
import { authContext } from '@/mcp-server/transports/auth/lib/authContext.js';
import type { AuthStrategy } from '@/mcp-server/transports/auth/strategies/authStrategy.js';

/**
 * Creates a Hono middleware function that enforces authentication using a given strategy.
 *
 * @param strategy - An instance of a class that implements the `AuthStrategy` interface.
 * @returns A Hono middleware function.
 */
export function createAuthMiddleware(strategy: AuthStrategy) {
  return async function authMiddleware(
    c: Context<{ Bindings: HttpBindings }>,
    next: Next,
  ) {
    const context = requestContextService.createRequestContext({
      operation: 'authMiddleware',
      additionalContext: {
        method: c.req.method,
        path: c.req.path,
      },
    });

    logger.debug('Initiating authentication check.', context);

    const authHeader = c.req.header('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      logger.warning('Authorization header missing or invalid.', context);
      throw new McpError(
        JsonRpcErrorCode.Unauthorized,
        'Missing or invalid Authorization header. Bearer scheme required.',
        context,
      );
    }

    const token = authHeader.substring(7);
    if (!token) {
      logger.warning(
        'Bearer token is missing from Authorization header.',
        context,
      );
      throw new McpError(
        JsonRpcErrorCode.Unauthorized,
        'Authentication token is missing.',
        context,
      );
    }

    logger.debug(
      'Extracted Bearer token, proceeding to verification.',
      context,
    );

    try {
      const authInfo = await strategy.verify(token);

      const authLogContext = {
        ...context,
        ...(authInfo.tenantId ? { tenantId: authInfo.tenantId } : {}),
        clientId: authInfo.clientId,
        subject: authInfo.subject,
        scopes: authInfo.scopes,
      };
      logger.info(
        'Authentication successful. Auth context populated.',
        authLogContext,
      );

      // Add authentication context to OpenTelemetry span for distributed tracing
      const activeSpan = trace.getActiveSpan();
      if (activeSpan) {
        activeSpan.setAttributes({
          'auth.client_id': authInfo.clientId,
          'auth.tenant_id': authInfo.tenantId ?? 'none',
          'auth.scopes': authInfo.scopes.join(','),
          'auth.subject': authInfo.subject ?? 'unknown',
          'auth.method': 'bearer',
        });
        logger.debug('Added auth context to OpenTelemetry span', {
          ...authLogContext,
          spanId: activeSpan.spanContext().spanId,
        });
      }

      // Run the next middleware in the chain within the populated auth context.
      await authContext.run({ authInfo }, next);
    } catch (error) {
      // The strategy is expected to throw an McpError.
      // We re-throw it here to be caught by the global httpErrorHandler.
      logger.warning('Authentication verification failed.', {
        ...context,
        error: error instanceof Error ? error.message : String(error),
      });

      // Ensure consistent error handling
      throw ErrorHandler.handleError(error, {
        operation: 'authMiddlewareVerification',
        context,
        rethrow: true, // Rethrow to be caught by Hono's global error handler
        errorCode: JsonRpcErrorCode.Unauthorized, // Default to unauthorized if not more specific
      });
    }
  };
}
