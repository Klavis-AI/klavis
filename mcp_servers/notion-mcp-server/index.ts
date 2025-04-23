#!/usr/bin/env node

import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import dotenv from 'dotenv';
import { initProxy } from './src/init-server.js';
import path from 'path';
import { asyncLocalStorage } from './src/openapi-mcp-server/mcp/proxy.js';

// Load environment variables
dotenv.config();

async function startServer() {
  const app = express();
  const transports = new Map<string, SSEServerTransport>();

  // Initialize the MCP proxy with OpenAPI spec
  const specPath = process.env.OPENAPI_SPEC_PATH || path.join(process.cwd(), 'scripts', 'notion-openapi.json');
  const baseUrl = process.env.BASE_URL ?? undefined;
  
  const proxy = await initProxy(specPath, baseUrl);

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

    await proxy.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
  });

  app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;

    let transport: SSEServerTransport | undefined;
    transport = sessionId ? transports.get(sessionId) : undefined;
    if (transport) {
      // Use NOTION_API_KEY from environment if available, otherwise use header
      const apiKey = process.env.NOTION_API_KEY || req.headers['x-auth-token'] as string;
      
      if (!apiKey) {
        console.error('No Notion API key provided in environment or headers');
        res.status(400).send({ error: "No Notion API key provided" });
        return;
      }

      asyncLocalStorage.run({ openapi_mcp_headers: JSON.stringify({
        'Authorization': `Bearer ${apiKey}`,
        'Notion-Version': process.env.NOTION_VERSION || '2022-06-28',
        'Content-Type': 'application/json'
      }) }, async () => {
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
}

startServer().catch(error => {
  console.error('Failed to start server:', error);
  process.exit(1);
}); 