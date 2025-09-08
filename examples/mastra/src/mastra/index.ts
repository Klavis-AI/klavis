import { Mastra } from '@mastra/core/mastra';
import { Agent } from '@mastra/core/agent';
import { openai } from '@ai-sdk/openai';
import { MCPClient } from '@mastra/mcp';
import { KlavisClient, Klavis } from 'klavis';
import open from 'open';

/**
 * Creates a Gmail MCP Agent with tools from a Klavis-hosted server
 */
export const createGmailMcpAgent = async (userId: string = 'test-user'): Promise<Agent> => {
  const klavis = new KlavisClient({ apiKey: process.env.KLAVIS_API_KEY! });

  // Create a new Gmail MCP server instance
  const instance = await klavis.mcpServer.createServerInstance({
    serverName: Klavis.McpServerName.Gmail,
    userId,
    platformName
  });

  // Redirect user to authorize
  const response = await klavis.mcpServer.getOAuthUrl({
    serverName: Klavis.McpServerName.Gmail,
    instanceId: instance.instanceId
  });
  open(response.oauthUrl);

  // Initialize the MCP client
  const mcpClient = new MCPClient({
    servers: {
      gmail: {
        url: new URL(instance.serverUrl)
      }
    }
  });

  // Get tools from the server
  const tools = await mcpClient.getTools();

  // Create agent
  return new Agent({
    name: 'Gmail MCP Agent',
    instructions: `You are a Gmail agent with access to Gmail tools: read, send, search emails, and manage labels.`,
    model: openai('gpt-4o-mini'),
    tools
  });
};

const agent = await createGmailMcpAgent();

export const mastra = new Mastra({
  agents: { agent }
});
