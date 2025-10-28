#!/usr/bin/env node

import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createSupabaseMcpServer, asyncLocalStorage } from './server.js';
import express, { type Request } from 'express';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

function extractAccessToken(req: Request): string {
  let authData = process.env.AUTH_DATA;
  
  if (!authData && req.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data JSON:', error);
    }
  }

  if (!authData) {
    console.error('Error: Supabase access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return '';
  }

  const authDataJson = JSON.parse(authData);
  return authDataJson.access_token ?? '';
}

const getSupabaseMcpServer = () => {
  const server = createSupabaseMcpServer({
    platform: {},
    readOnly: false,
  });
  return server;
}

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req, res) => {
  const accessToken = extractAccessToken(req);

  const server = getSupabaseMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ accessToken }, async () => {
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
    const accessToken = extractAccessToken(req);
    asyncLocalStorage.run({ accessToken }, async () => {
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
