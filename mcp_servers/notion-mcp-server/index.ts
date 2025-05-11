#!/usr/bin/env node

import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
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
      const errorResponse = {
        jsonrpc: '2.0' as '2.0',
        error: {
          code: -32001,
          message: 'Unauthorized, Notion API key is missing. Have you set the Notion API key?'
        },
        id: 0
      };
      await transport.send(errorResponse);
      await transport.close();
      res.status(401).end(JSON.stringify({ error: "Unauthorized, Notion API key is missing. Have you set the Notion API key?" }));
      return;
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