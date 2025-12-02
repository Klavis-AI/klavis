#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { SandboxService } from './sandbox-manager.js';
import { E2BTools } from './tools.js';
import { logger } from './logger.js';

// Validate environment
if (!process.env.E2B_API_KEY) {
  console.error('E2B_API_KEY environment variable is required');
  process.exit(1);
}

// Initialize services
const sandboxService = new SandboxService();
const e2bTools = new E2BTools(sandboxService);

const server = new Server(
  {
    name: 'e2b-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  logger.info('Received ListTools request');
  return {
    tools: e2bTools.getToolDefinitions()
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  logger.info(`Received CallTool request for ${name}`);
  
  try {
    return await e2bTools.executeTool(name, args);
  } catch (error) {
    logger.error(`Tool execution failed for ${name}:`, error);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
      }],
      isError: true
    };
  }
});

async function main() {
  try {
    logger.info('Starting E2B MCP Server');
    const transport = new StdioServerTransport();
    await server.connect(transport);
    logger.info('Server connected successfully');
  } catch (error) {
    logger.error('Failed to start server:', error);
    throw error;
  }
}

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Received SIGINT, shutting down gracefully');
  await sandboxService.cleanup();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM, shutting down gracefully');
  await sandboxService.cleanup();
  process.exit(0);
});

main().catch(async (error) => {
  logger.error('Server error:', error);
  await sandboxService.cleanup();
  process.exit(1);
});