/**
 * @fileoverview Defines custom types for the Hono HTTP transport layer.
 * @module src/mcp-server/transports/http/httpTypes
 */
import type { IncomingMessage, ServerResponse } from 'http';

/**
 * Extends Hono's Bindings to include the raw Node.js request and response objects.
 * This is necessary for integrating with libraries like the MCP SDK that
 * need to write directly to the response stream.
 *
 * As per `@hono/node-server`, the response object is available on `c.env.outgoing`.
 */
export type HonoNodeBindings = {
  incoming: IncomingMessage;
  outgoing: ServerResponse;
};

/**
 * Defines the custom variables that can be set on the Hono context.
 * Used for passing strongly-typed data between middleware.
 */
export type HonoVariables = {
  mcpSessionId?: string;
};
