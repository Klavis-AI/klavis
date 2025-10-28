/**
 * Initializes and returns the MCP server instance.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SERVER_NAME, SERVER_VERSION } from "./settings.js";
import type { Config } from "./config.js";

export function initialize(config: Config): McpServer {
  console.error("Initializing MCP Server...", config);
  const server = new McpServer({
    name: SERVER_NAME,
    version: SERVER_VERSION,
  });
  return server;
}
