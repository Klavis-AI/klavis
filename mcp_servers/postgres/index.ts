#!/usr/bin/env node
import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import pg from "pg";
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const SCHEMA_PATH = "schema";

const getPostgresMcpServer = () => {
  const server = new Server(
    {
      name: "klavis-ai/postgres",
      version: "0.1.0",
    },
    {
      capabilities: {
        resources: {},
        tools: {},
      },
    },
  );
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    const client = await getPool().connect();
    try {
      const result = await client.query(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
      );
      return {
        resources: result.rows.map((row) => ({
          uri: new URL(`${row.table_name}/${SCHEMA_PATH}`, getResourceBaseUrl()).href,
          mimeType: "application/json",
          name: `"${row.table_name}" database schema`,
        })),
      };
    } finally {
      client.release();
    }
  });

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const resourceUrl = new URL(request.params.uri);

    const pathComponents = resourceUrl.pathname.split("/");
    const schema = pathComponents.pop();
    const tableName = pathComponents.pop();

    if (schema !== SCHEMA_PATH) {
      throw new Error("Invalid resource URI");
    }

    const client = await getPool().connect();
    try {
      const result = await client.query(
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1",
        [tableName],
      );

      return {
        contents: [
          {
            uri: request.params.uri,
            mimeType: "application/json",
            text: JSON.stringify(result.rows, null, 2),
          },
        ],
      };
    } finally {
      client.release();
    }
  });

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "query",
          description: "Run a read-only SQL query",
          inputSchema: {
            type: "object",
            properties: {
              sql: { type: "string" },
            },
          },
        },
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    if (request.params.name === "query") {
      const sql = request.params.arguments?.sql as string;

      const client = await getPool().connect();
      try {
        await client.query("BEGIN TRANSACTION READ ONLY");
        const result = await client.query(sql);
        return {
          content: [{ type: "text", text: JSON.stringify(result.rows, null, 2) }],
          isError: false,
        };
      } catch (error) {
        throw error;
      } finally {
        client
          .query("ROLLBACK")
          .catch((error) =>
            console.warn("Could not roll back transaction:", error),
          );

        client.release();
      }
    }
    throw new Error(`Unknown tool: ${request.params.name}`);
  });

  return server;
}

// Create AsyncLocalStorage for request context - now only storing databaseUrl
const asyncLocalStorage = new AsyncLocalStorage<{
  databaseUrl: string;
}>();

// Create resourceBaseUrl when needed
function getResourceBaseUrl() {
  const databaseUrl = asyncLocalStorage.getStore()!.databaseUrl;
  const resourceBaseUrl = new URL(databaseUrl);
  resourceBaseUrl.protocol = "postgres:";
  resourceBaseUrl.password = "";
  return resourceBaseUrl;
}

// Create pool when needed
function getPool() {
  const databaseUrl = asyncLocalStorage.getStore()!.databaseUrl;
  return new pg.Pool({
    connectionString: databaseUrl,
  });
}

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const databaseUrl = process.env.DATABASE_URL || req.headers['x-auth-token'] as string;

  if (!databaseUrl) {
    console.error('Error: Postgres database URL is missing. Provide it via DATABASE_URL env var or x-auth-token header.');
  }

  const server = getPostgresMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ databaseUrl }, async () => {
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

  const server = getPostgresMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    // Use DATABASE_URL from environment if available, otherwise fall back to header
    const databaseUrl = process.env.DATABASE_URL || req.headers['x-auth-token'] as string;

    if (!databaseUrl) {
      console.error('Error: Postgres database URL is missing. Provide it via DATABASE_URL env var or x-auth-token header.');
    }

    asyncLocalStorage.run({ databaseUrl }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(5000, () => {
  console.log('server running on port 5000');
});
