import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

/**
 * Connects the given MCP server to standard IO transport.
 * Logs server status and handles connection errors gracefully.
 *
 * @param server - An instance of McpServer to be connected.
 */
export async function connectServer(server: McpServer): Promise<void> {
  const transport = new StdioServerTransport();
  try {
    await server.connect(transport);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Failed to connect MCP Server:", errorMessage);
  }
}
