#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  Tool,
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { Fetcher } from "./Fetcher.js";
import { RequestPayload } from "./types.js";

process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  process.exit(1);
});

// Tool definitions
const FETCH_HTML_TOOL: Tool = {
  name: 'fetch_html',
  description: 'Fetch a website and return the content as HTML',
  inputSchema: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'URL of the website to fetch',
      },
      headers: {
        type: 'object',
        additionalProperties: { type: 'string' },
        description: 'Optional headers to include in the request',
      },
    },
    required: ['url'],
  },
  annotations: {
    readOnlyHint: true,
    category: 'FETCH_URL',
  } as Tool['annotations'],
};

const FETCH_MARKDOWN_TOOL: Tool = {
  name: 'fetch_markdown',
  description: 'Fetch a website and return the content as Markdown',
  inputSchema: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'URL of the website to fetch',
      },
      headers: {
        type: 'object',
        additionalProperties: { type: 'string' },
        description: 'Optional headers to include in the request',
      },
    },
    required: ['url'],
  },
  annotations: {
    readOnlyHint: true,
    category: 'FETCH_URL',
  } as Tool['annotations'],
};

const FETCH_TXT_TOOL: Tool = {
  name: 'fetch_txt',
  description: 'Fetch a website, return the content as plain text (no HTML)',
  inputSchema: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'URL of the website to fetch',
      },
      headers: {
        type: 'object',
        additionalProperties: { type: 'string' },
        description: 'Optional headers to include in the request',
      },
    },
    required: ['url'],
  },
  annotations: {
    readOnlyHint: true,
    category: 'FETCH_URL',
  } as Tool['annotations'],
};

const FETCH_JSON_TOOL: Tool = {
  name: 'fetch_json',
  description: 'Fetch a JSON file from a URL',
  inputSchema: {
    type: 'object',
    properties: {
      url: {
        type: 'string',
        description: 'URL of the website to fetch',
      },
      headers: {
        type: 'object',
        additionalProperties: { type: 'string' },
        description: 'Optional headers to include in the request',
      },
    },
    required: ['url'],
  },
  annotations: {
    readOnlyHint: true,
    category: 'FETCH_URL',
  } as Tool['annotations'],
};

// Main server function - creates a new server instance for each request
const getFetchMcpServer = () => {
  const server = new Server(
    {
      name: 'fetch-url-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        FETCH_HTML_TOOL,
        FETCH_MARKDOWN_TOOL,
        FETCH_TXT_TOOL,
        FETCH_JSON_TOOL,
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'fetch_html': {
          const result = await Fetcher.html(args as unknown as RequestPayload);
          return result;
        }

        case 'fetch_markdown': {
          const result = await Fetcher.markdown(args as unknown as RequestPayload);
          return result;
        }

        case 'fetch_txt': {
          const result = await Fetcher.txt(args as unknown as RequestPayload);
          return result;
        }

        case 'fetch_json': {
          const result = await Fetcher.json(args as unknown as RequestPayload);
          return result;
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error: any) {
      console.error(`Tool ${name} failed: ${error.message}`);
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  });

  return server;
};

const app = express();
const PORT = process.env.PORT || 5000;

app.use(express.json());

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  console.log('MCP connection request received');

  const server = getFetchMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
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

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
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

  const server = getFetchMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports.get(sessionId);
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.get("/health", (req: Request, res: Response) => {
  res.json({ status: "ok", name: "fetch-url-mcp" });
});

app.listen(PORT, () => {
  console.log(`MCP server listening on http://localhost:${PORT}`);
  console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
  console.log(`SSE endpoint: http://localhost:${PORT}/sse`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
