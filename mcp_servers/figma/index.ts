#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import { createServer } from './mcp.js';
import { AsyncLocalStorage } from 'async_hooks';

dotenv.config();

// Added: Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  figmaApiKey: string;
}>();

// Get Figma API key from environment
const FIGMA_API_KEY = process.env.FIGMA_API_KEY;

// Initialize Express app
const app = express();
const port = process.env.PORT || 5000;

// Get server type from command line arguments
const serverType = process.argv[2] || 'stdio';

// For stdio mode, just create and serve a single instance
if (serverType === 'stdio') {
  const stdioServer = createServer(FIGMA_API_KEY || '');
  stdioServer.serve(new StdioServerTransport());
} else {
  // For HTTP modes, set up the express endpoints

  // Map to store SSE transports by session ID
  const transports = new Map<string, SSEServerTransport>();

  //=============================================================================
  // STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
  //=============================================================================
  
  app.post('/mcp', async (req: Request, res: Response) => {
    // Extract API key from environment or header
    const apiKey = process.env.FIGMA_API_KEY || 
                  req.headers['x-auth-token'] as string || 
                  req.headers['access_token'] as string;
    
    if (!apiKey) {
      console.error('Error: Figma API key is missing. Provide it via FIGMA_API_KEY env var, x-auth-token or access_token header.');
      res.status(401).json({ error: 'API key is required' });
      return;
    }
    
    try {
      // Create a new server instance for this request
      const server = createServer(apiKey, { isHTTP: true });
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });
      
      await server.connect(transport);
      
      // Run within AsyncLocalStorage context
      asyncLocalStorage.run({ figmaApiKey: apiKey }, async () => {
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
    res.status(405).json({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    });
  });

  //=============================================================================
  // DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
  //=============================================================================
  
  app.get("/sse", async (req: Request, res: Response) => {
    const transport = new SSEServerTransport(`/messages`, res);
    
    // Set up cleanup when connection closes
    res.on('close', async () => {
      console.log(`SSE connection closed for transport: ${transport.sessionId}`);
      transports.delete(transport.sessionId);
    });
    
    transports.set(transport.sessionId, transport);
    
    // Create a new server for this SSE connection
    const apiKey = process.env.FIGMA_API_KEY || '';
    const server = createServer(apiKey, { isHTTP: true });
    await server.connect(transport);
    
    console.log(`SSE connection established with transport: ${transport.sessionId}`);
  });
  
  app.post("/messages", async (req: Request, res: Response) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    
    if (transport) {
      // Extract API key from environment or header
      const apiKey = process.env.FIGMA_API_KEY || 
                    req.headers['x-auth-token'] as string || 
                    req.headers['access_token'] as string;
      
      if (!apiKey) {
        console.error('Error: Figma API key is missing. Provide it via FIGMA_API_KEY env var, x-auth-token or access_token header.');
        res.status(401).json({ error: 'API key is required' });
        return;
      }
      
      // Run within AsyncLocalStorage context
      asyncLocalStorage.run({ figmaApiKey: apiKey }, async () => {
        await transport.handlePostMessage(req, res);
      });
    } else {
      console.error(`Transport not found for session ID: ${sessionId}`);
      res.status(404).send({ error: "Transport not found" });
    }
  });
  
  // Start the server
  app.listen(port, () => {
    console.log(`Figma MCP server is running on port ${port}`);
  });
}
