/**
 * @fileoverview Handles the setup and connection for the Stdio MCP transport.
 * Implements the MCP Specification 2025-06-18 for stdio transport.
 * This transport communicates directly over standard input (stdin) and
 * standard output (stdout), typically used when the MCP server is launched
 * as a child process by a host application.
 *
 * Specification Reference:
 * https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#stdio
 *
 * --- Authentication Note ---
 * As per the MCP Authorization Specification (2025-06-18, Section 1.2),
 * STDIO transports SHOULD NOT implement HTTP-based authentication flows.
 * Authorization is typically handled implicitly by the host application
 * controlling the server process. This implementation follows that guideline.
 *
 * @see {@link https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization | MCP Authorization Specification}
 * @module src/mcp-server/transports/stdioTransport
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

import {
  ErrorHandler,
  type RequestContext,
  logger,
  logStartupBanner,
} from '@/utils/index.js';

/**
 * Connects a given `McpServer` instance to the Stdio transport.
 * This function initializes the SDK's `StdioServerTransport`, which manages
 * communication over `process.stdin` and `process.stdout` according to the
 * MCP stdio transport specification.
 *
 * MCP Spec Points Covered by SDK's `StdioServerTransport`:
 * - Reads JSON-RPC messages (requests, notifications, responses, batches) from stdin.
 * - Writes JSON-RPC messages to stdout.
 * - Handles newline delimiters and ensures no embedded newlines in output messages.
 * - Ensures only valid MCP messages are written to stdout.
 *
 * Logging via the `logger` utility MAY result in output to stderr, which is
 * permitted by the spec for logging purposes.
 *
 * @param server - The `McpServer` instance.
 * @param parentContext - The logging and tracing context from the calling function.
 * @returns A promise that resolves when the Stdio transport is successfully connected.
 * @throws {Error} If the connection fails during setup.
 */
export async function startStdioTransport(
  server: McpServer,
  parentContext: RequestContext,
): Promise<McpServer> {
  const operationContext = {
    ...parentContext,
    operation: 'connectStdioTransport',
    transportType: 'Stdio',
  };
  logger.info('Attempting to connect stdio transport...', operationContext);

  try {
    logger.debug('Creating StdioServerTransport instance...', operationContext);
    const transport = new StdioServerTransport();

    logger.debug(
      'Connecting McpServer instance to StdioServerTransport...',
      operationContext,
    );
    await server.connect(transport);

    logger.info(
      'MCP Server connected and listening via stdio transport.',
      operationContext,
    );
    logStartupBanner(
      `\n🚀 MCP Server running in STDIO mode.\n   (MCP Spec: 2025-06-18 Stdio Transport)\n`,
    );
    return server;
  } catch (err) {
    // Let the ErrorHandler log the error with all context, then rethrow.
    throw ErrorHandler.handleError(err, {
      operation: 'connectStdioTransport',
      context: operationContext,
      critical: true,
      rethrow: true,
    });
  }
}

export async function stopStdioTransport(
  server: McpServer,
  parentContext: RequestContext,
): Promise<void> {
  const operationContext = {
    ...parentContext,
    operation: 'stopStdioTransport',
    transportType: 'Stdio',
  };
  logger.info('Attempting to stop stdio transport...', operationContext);
  if (server) {
    await server.close();
    logger.info('Stdio transport stopped successfully.', operationContext);
  }
}
