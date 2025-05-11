#!/usr/bin/env node

import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createSupabaseMcpServer, setManagementApiClient, asyncLocalStorage } from './server.js';
import express from 'express';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const getSupabaseMcpServer = () => {
  const server = createSupabaseMcpServer({
    platform: {},
    readOnly: true,
  });
  return server;
}

const app = express();
app.use(express.json());

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req, res) => {
  const accessToken = req.headers['x-auth-token'] as string;
  if (!accessToken) {
    console.error('Error: Supabase Access Token is missing. Provide it via x-auth-token header.');
    const errorResponse = {
      jsonrpc: '2.0' as '2.0',
      error: {
        code: -32001,
        message: 'Unauthorized, Supabase Access Token is missing. Have you set the Supabase Access Token?'
      },
      id: 0
    };
    res.status(401).json(errorResponse);
    return;
  }

  const server = getSupabaseMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ managementApiClient: setManagementApiClient(accessToken) }, async () => {
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

app.get('/mcp', async (req, res) => {
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

app.delete('/mcp', async (req, res) => {
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

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports: { [sessionId: string]: SSEServerTransport } = {};

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport('/messages', res);
  transports[transport.sessionId] = transport;
  res.on("close", () => {
    delete transports[transport.sessionId];
  });
  const server = getSupabaseMcpServer();
  await server.connect(transport);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports[sessionId];
  if (transport) {
    // Use environment variable for auth token if set, otherwise use header
    const envAuthToken = process.env.SUPABASE_AUTH_TOKEN;
    const accessToken = envAuthToken || req.headers['x-auth-token'] as string;
    if (!accessToken) {
      console.error('Error: Supabase Access Token is missing. Provide it via x-auth-token header.');
      const errorResponse = {
        jsonrpc: '2.0' as '2.0',
        error: {
          code: -32001,
          message: 'Unauthorized, Supabase Access Token is missing. Have you set the Supabase Access Token?'
        },
        id: 0
      };
      await transport.send(errorResponse);
      await transport.close();
      res.status(401).end(JSON.stringify({ error: "Unauthorized, Supabase Access Token is missing. Have you set the Supabase Access Token?" }));
      return;
    }
    asyncLocalStorage.run({ managementApiClient: setManagementApiClient(accessToken) }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    res.status(400).send('No transport found for sessionId');
  }
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Supabase MCP Server running on port ${PORT}`);
}); 
