import { Mastra } from '@mastra/core/mastra';
import { Agent } from '@mastra/core/agent';
import { openai } from '@ai-sdk/openai';
import { MCPClient } from '@mastra/mcp';
import { KlavisClient, Klavis } from 'klavis';

/**
 * Creates a Gmail MCP Agent with tools from a Klavis-hosted server
 */
export const createGmailMcpAgent = async (userId: string = 'test-user'): Promise<Agent> => {
  const klavis = new KlavisClient({ apiKey: process.env.KLAVIS_API_KEY! });

  // Create a new Gmail MCP server instance
  console.log('---- Creating Gmail MCP server instance');
  console.log('---- Klavis API Key:', process.env.KLAVIS_API_KEY);
  const instance = await klavis.mcpServer.createServerInstance({
    serverName: Klavis.McpServerName.Gmail,
    userId,
    platformName: 'test-platform',
  });

  // Construct OAuth URL for user authentication
  const oauthUrl = `https://api.klavis.ai/oauth/gmail/authorize?instance_id=${instance.instanceId}&client_id=${process.env.GOOGLE_CLIENT_ID}`;
  console.log('[Gmail MCP Agent] Authorize at:', oauthUrl);

  // Initialize the MCP client
  const mcpClient = new MCPClient({
    servers: {
      gmail: {
        url: new URL(instance.serverUrl),
        requestInit: {
          headers: {
            Authorization: `Bearer ${process.env.KLAVIS_API_KEY!}`,
          },
        },
      },
    },
  });

  // Get tools from the server
  const tools = await mcpClient.getTools();

  // Create agent with Gmail capabilities
  const instructions = `You are a Gmail agent with access to Gmail tools: read, send, search emails, and manage labels. If authentication is required, direct users to: ${oauthUrl}`;

  return new Agent({
    name: 'Gmail MCP Agent',
    instructions,
    model: openai('gpt-4o-mini'),
    tools,
  });
};

const agent = await createGmailMcpAgent();

export const mastra = new Mastra({
  agents: { agent },
});
