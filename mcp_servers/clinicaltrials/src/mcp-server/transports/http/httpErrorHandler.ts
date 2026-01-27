/**
 * @fileoverview Centralized error handler for the Hono HTTP transport.
 * This middleware intercepts errors that occur during request processing,
 * standardizes them using the application's ErrorHandler utility, and
 * formats them into a consistent JSON-RPC error response.
 * @module src/mcp-server/transports/http/httpErrorHandler
 */
import type { Context } from 'hono';
import type { StatusCode } from 'hono/utils/http-status';

import { config } from '@/config/index.js';
import type { HonoNodeBindings } from '@/mcp-server/transports/http/httpTypes.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { ErrorHandler, logger, requestContextService } from '@/utils/index.js';

/**
 * A centralized error handling middleware for Hono.
 * This function is registered with `app.onError()` and will catch any errors
 * thrown from preceding middleware or route handlers.
 *
 * @param err - The error that was thrown.
 * @param c - The Hono context object for the request.
 * @returns A Response object containing the formatted JSON-RPC error.
 */
export const httpErrorHandler = async (
  err: Error,
  c: Context<{ Bindings: HonoNodeBindings }>,
): Promise<Response> => {
  const context = requestContextService.createRequestContext({
    operation: 'httpErrorHandler',
    additionalContext: {
      path: c.req.path,
      method: c.req.method,
    },
  });
  logger.debug('HTTP error handler invoked.', context);

  const handledError = ErrorHandler.handleError(err, {
    operation: 'httpTransport',
    context,
  });

  let status: StatusCode = 500;
  if (handledError instanceof McpError) {
    switch (handledError.code) {
      case JsonRpcErrorCode.NotFound:
        status = 404;
        break;
      case JsonRpcErrorCode.Unauthorized:
        status = 401;
        // MCP Spec 2025-06-18: Add WWW-Authenticate header per RFC 9728 Section 5.1
        // https://datatracker.ietf.org/doc/html/rfc9728#section-5.1
        if (config.oauthIssuerUrl) {
          const origin = new URL(c.req.url).origin;
          const resourceMetadataUrl = `${origin}/.well-known/oauth-protected-resource`;

          // Build WWW-Authenticate header per RFC 9728
          const wwwAuthValue = [
            `Bearer realm="${config.mcpServerName}"`,
            `resource_metadata="${resourceMetadataUrl}"`,
          ].join(', ');

          c.header('WWW-Authenticate', wwwAuthValue);

          logger.debug('Added WWW-Authenticate header for 401 response', {
            ...context,
            resourceMetadataUrl,
          });
        }
        break;
      case JsonRpcErrorCode.Forbidden:
        status = 403;
        break;
      case JsonRpcErrorCode.ValidationError:
      case JsonRpcErrorCode.InvalidRequest:
        status = 400;
        break;
      case JsonRpcErrorCode.Conflict:
        status = 409;
        break;
      case JsonRpcErrorCode.RateLimited:
        status = 429;
        break;
      default:
        status = 500;
    }
  }
  logger.debug(`Mapping error to HTTP status ${status}.`, {
    ...context,
    status,
    errorCode: (handledError as McpError).code,
  });

  // Attempt to get the request ID from the body, but don't fail if it's not there or unreadable.
  let requestId: string | number | null = null;
  // Only attempt to read the body if it hasn't been consumed already.
  if (c.req.raw.bodyUsed === false) {
    try {
      const body: unknown = await c.req.json();
      if (body && typeof body === 'object' && 'id' in body) {
        const id = (body as Record<string, unknown>).id;
        requestId =
          typeof id === 'string' || typeof id === 'number' ? id : null;
      } else {
        requestId = null;
      }
      logger.debug('Extracted JSON-RPC request ID from body.', {
        ...context,
        jsonRpcId: requestId,
      });
    } catch {
      logger.warning(
        'Could not parse request body to extract JSON-RPC ID.',
        context,
      );
      // Ignore parsing errors, requestId will remain null
    }
  } else {
    logger.debug(
      'Request body already consumed, cannot extract JSON-RPC ID.',
      context,
    );
  }

  const errorCode =
    handledError instanceof McpError ? handledError.code : -32603;

  c.status(status);
  const errorResponse = {
    jsonrpc: '2.0',
    error: {
      code: errorCode,
      message: handledError.message,
    },
    id: requestId,
  };
  logger.info(`Sending formatted error response for request.`, {
    ...context,
    status,
    errorCode,
    jsonRpcId: requestId,
  });
  return c.json(errorResponse);
};
