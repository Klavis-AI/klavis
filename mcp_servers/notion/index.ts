import express, { Request, Response } from 'express';
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import dotenv from 'dotenv';
import { initProxy } from './src/init-server.js';
import path from 'path';
import { asyncLocalStorage } from './src/openapi-mcp-server/mcp/proxy.js';

// Load environment variables
dotenv.config();

// Get the Notion MCP server
const getNotionMcpServer = async () => {
  // Initialize the MCP proxy with OpenAPI spec
  const specPath = process.env.OPENAPI_SPEC_PATH || path.join(process.cwd(), 'scripts', 'notion-openapi.json');
  const baseUrl = process.env.BASE_URL ?? undefined;
  
  const server = await initProxy(specPath, baseUrl);
  return server;
};

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const apiKey = process.env.NOTION_API_KEY || req.headers['x-auth-token'] as string;
  
  if (!apiKey) {
    console.error('Error: Notion API key is missing. Provide it via NOTION_API_KEY env var or x-auth-token header.');
  }

  // Create headers for Notion API
  const headers = JSON.stringify({
    'Authorization': `Bearer ${apiKey}`,
    'Notion-Version': process.env.NOTION_VERSION || '2022-06-28',
    'Content-Type': 'application/json'
  });

  const server = await getNotionMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    
    // Run handler within AsyncLocalStorage context
    asyncLocalStorage.run({ 
      openapi_mcp_headers: headers
    }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
    
    res.on('close', () => {
      console.log('Request closed');
      transport.close();
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

  const server = await getNotionMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports.get(sessionId);
  if (transport) {
    // Get API key from env or header
    const apiKey = process.env.NOTION_API_KEY || req.headers['x-auth-token'] as string;
    
    if (!apiKey) {
      console.error('Error: Notion API key is missing. Provide it via NOTION_API_KEY env var or x-auth-token header.');
    }

    // Create headers for Notion API
    const headers = JSON.stringify({
      'Authorization': `Bearer ${apiKey}`,
      'Notion-Version': process.env.NOTION_VERSION || '2022-06-28',
      'Content-Type': 'application/json'
    });

    // Run handler within AsyncLocalStorage context
    asyncLocalStorage.run({ 
      openapi_mcp_headers: headers
    }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

const port = process.env.PORT || 5000;
app.listen(port, () => {
  console.log(`Notion MCP server running on port ${port}`);
}); 