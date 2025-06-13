import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { KlavisAPI } from "./klavis-api.js";

async function connectToMcpServer(url: string): Promise<Client> {
  let client: Client | undefined = undefined;
  const baseUrl = new URL(url);

  try {
    client = new Client({
      name: 'streamable-http-client',
      version: '1.0.0'
    });
    const transport = new StreamableHTTPClientTransport(
      new URL(baseUrl)
    );
    await client.connect(transport);
    console.log("Connected using Streamable HTTP transport");
    return client;
  } catch (error) {
    console.error("Failed to connect to MCP server:", error);
    throw error;
  }
}

// Example usage
async function main(): Promise<void> {
  try {
    // Initialize Klavis API client
    const apiKey = process.env.KLAVIS_API_KEY;
    if (!apiKey) {
      throw new Error("KLAVIS_API_KEY environment variable is required");
    }
    
    const klavisApi = new KlavisAPI(apiKey);
    
    // Create MCP instance and get server URL
    const { serverUrl } = await klavisApi.createMcpInstance(
      "Confluence", // Example server name
      "12345", // Example user ID
      "demo", // Example platform name
      "StreamableHttp" // Connection type
    );
    
    console.log("Created MCP instance with URL:", serverUrl);
    
    const client = await connectToMcpServer(serverUrl);
    
    // Example: List available tools
    const tools = await client.listTools();
    console.log("Available tools:", tools);

    await client.close();    
  } catch (error) {
    console.error("Failed to connect to MCP server:", error);
  }
}

main().catch(console.error);
