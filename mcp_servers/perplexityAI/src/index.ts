#!/usr/bin/env node
import express, { Request, Response } from 'express';
// @ts-ignore
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
// @ts-ignore
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
// @ts-ignore
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
// @ts-ignore
import { ListToolsRequestSchema, CallToolRequestSchema, CallToolRequest } from "@modelcontextprotocol/sdk/types.js";

import { ALL_TOOLS } from './schemas.js';
import { PerplexityClient, getPerplexityToken, asyncLocalStorage } from './client.js';
import { 
  AskTool, 
  SearchTool, 
  ResearchTool, 
  ReasonTool, 
  SummaryTool, 
  CodeAssistantTool 
} from './tools/index.js';

const getPerplexityMcpServer = () => {
  const server = new Server(
    {
      name: "perplexityAI-mcp-server",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: ALL_TOOLS,
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request: CallToolRequest) => {
    try {
      const { name, arguments: args } = request.params;
      if (!args) throw new Error("No arguments provided");
      
      const perplexityToken = getPerplexityToken();
      if (!perplexityToken) {
        throw new Error("No valid Perplexity token found for this instance");
      }

      const perplexityClient = new PerplexityClient(perplexityToken);
      
      // Create tool instances
      const tools = {
        perplexity_ask: new AskTool(perplexityClient),
        perplexity_search: new SearchTool(perplexityClient),
        perplexity_research: new ResearchTool(perplexityClient),
        perplexity_reason: new ReasonTool(perplexityClient),
        perplexity_summary: new SummaryTool(perplexityClient),
        perplexity_code_assistant: new CodeAssistantTool(perplexityClient),
      };

      const tool = tools[name as keyof typeof tools];
      if (!tool) {
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
      }

      return await tool.execute(args);
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  });

  return server;
}

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const perplexity_token = req.headers['x-auth-token'] as string;

  if (!perplexity_token) {
    console.error('Error: Perplexity token is missing. Provide it via x-auth-token header.');
  }

    const server = getPerplexityMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ perplexity_token }, async () => {
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
    console.log('Received GET MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    console.log('Received DELETE MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
    }
  });

  transports.set(transport.sessionId, transport);

  const server = getPerplexityMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const perplexity_token = req.headers['x-auth-token'] as string;

    if (!perplexity_token) {
      console.error('Error: Perplexity token is missing. Provide it via x-auth-token header.');
    }

    asyncLocalStorage.run({ perplexity_token }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(5000, () => {
  console.log('Perplexity MCP server running on port 5000');
});
