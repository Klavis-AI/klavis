#!/usr/bin/env node

import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { createSupabaseMcpServer, setManagementApiClient, asyncLocalStorage } from './server.js';
import express from 'express';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const server = createSupabaseMcpServer({
  platform: {},
  readOnly: true,
});

const app = express();

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport('/messages', res);
  transports.set(transport.sessionId, transport);
  res.on("close", () => {
    transports.delete(transport.sessionId);
    console.log(`Transport closed for sessionId: ${transport.sessionId}`);
  });
  await server.connect(transport);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports.get(sessionId);
  if (transport) {
    // Use environment variable for auth token if set, otherwise use header
    const envAuthToken = process.env.SUPABASE_AUTH_TOKEN;
    const accessToken = envAuthToken || req.headers['x-auth-token'] as string;
    asyncLocalStorage.run({ managementApiClient: setManagementApiClient(accessToken) }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`No transport found for sessionId: ${sessionId}`);
    res.status(400).send('No transport found for sessionId');
  }
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Supabase MCP Server running on port ${PORT}`);
}); 
