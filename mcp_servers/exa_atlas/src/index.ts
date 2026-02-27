#!/usr/bin/env node
import express, { Request, Response } from 'express';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import dotenv from "dotenv";
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

import { toolRegistry, asyncLocalStorage } from "./tools/index.js";
import { log } from "./utils/logger.js";

dotenv.config();

const argv = yargs(hideBin(process.argv))
  .option('tools', {
    type: 'string',
    description: 'Comma-separated list of tools to enable (if not specified, all enabled-by-default tools are used)',
    default: ''
  })
  .option('list-tools', {
    type: 'boolean',
    description: 'List all available tools and exit',
    default: false
  })
  .help()
  .argv;

const argvObj = argv as any;
const toolsString = argvObj['tools'] || '';
const specifiedTools = new Set<string>(
  toolsString ? toolsString.split(',').map((tool: string) => tool.trim()) : []
);

if (argvObj['list-tools']) {
  console.log("Available tools:");
  Object.entries(toolRegistry).forEach(([id, tool]) => {
    console.log(`- ${id}: ${tool.name}`);
    console.log(`  Description: ${tool.description}`);
    console.log(`  Enabled by default: ${tool.enabled ? 'Yes' : 'No'}`);
    console.log();
  });
  process.exit(0);
}

/**
 * Extract API key from AUTH_DATA env var or x-auth-data header (base64-encoded JSON).
 */
function extractApiKey(req?: Request | null): string {
  let authData = process.env.AUTH_DATA;

  if (!authData) {
    const envKey = process.env.EXA_API_KEY;
    if (envKey) return envKey;
  }

  if (!authData && req?.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error decoding x-auth-data header:', error);
    }
  }

  if (!authData) {
    console.error('Error: Exa API key missing. Provide via AUTH_DATA env var, EXA_API_KEY env var, or x-auth-data header.');
    return '';
  }

  try {
    const json = JSON.parse(authData);
    return json.api_key ?? json.EXA_API_KEY ?? '';
  } catch {
    return authData;
  }
}

class ExaServer {
  private server: McpServer;

  constructor() {
    this.server = new McpServer({
      name: "exa-search-server",
      version: "0.3.10"
    });
    log("Server initialized");
  }

  getMcpServer(): McpServer {
    return this.server;
  }

  setupTools(): string[] {
    const registeredTools: string[] = [];
    Object.entries(toolRegistry).forEach(([toolId, tool]) => {
      const shouldRegister = specifiedTools.size > 0
        ? specifiedTools.has(toolId)
        : tool.enabled;

      if (shouldRegister) {
        (this.server.tool as Function)(
          tool.name,
          tool.description,
          tool.schema,
          tool.handler
        );
        registeredTools.push(toolId);
      }
    });
    return registeredTools;
  }

  async runStdio(): Promise<void> {
    const registeredTools = this.setupTools();
    log(`Starting Exa MCP server with ${registeredTools.length} tools: ${registeredTools.join(', ')}`);
    const transport = new StdioServerTransport();
    transport.onerror = (error) => {
      log(`Transport error: ${error.message}`);
    };
    await this.server.connect(transport);
    log("Exa Search MCP server running on stdio");
  }
}

function createExaServer(): ExaServer {
  return new ExaServer();
}

//=============================================================================
// HTTP SERVER SETUP
//=============================================================================

const app = express();

app.post('/mcp', async (req: Request, res: Response) => {
  const apiKey = extractApiKey(req);

  const exaServer = createExaServer();
  exaServer.setupTools();
  const server = exaServer.getMcpServer();

  try {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);

    asyncLocalStorage.run({ apiKey }, async () => {
      await transport.handleRequest(req, res, req.body);
    });

    res.on('close', () => {
      console.log('Request closed');
      transport.close();
      server.close();
    });
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: Response) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Method not allowed." },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Method not allowed." },
    id: null
  }));
});

//=============================================================================
// MAIN ENTRY POINT
//=============================================================================

const PORT = parseInt(process.env.PORT || '5000', 10);
const TRANSPORT = process.env.TRANSPORT || 'http';

if (TRANSPORT === 'stdio') {
  const server = createExaServer();
  server.runStdio().catch((error) => {
    log(`Fatal server error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  });
} else {
  app.listen(PORT, () => {
    console.log(`Exa MCP server running on port ${PORT}`);
    console.log(`  - Streamable HTTP: POST /mcp`);
  });
}
