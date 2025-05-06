#!/usr/bin/env node
import express from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from 'async_hooks';

const getWordPressMcpServer = () => {
  const server = new Server(
    {
      name: "klavis-ai/wordpress",
      version: "0.1.0",
    },
    {
      capabilities: {
        resources: {},
        tools: {},
      },
    },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: "create_post",
          description: "Create a new WordPress post",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              title: { type: "string", description: "Post title in html format" },
              content: { type: "string", description: "Post content in html format" },
              status: { type: "string", description: "Post status (draft, publish, private, pending etc.)", default: "publish" }
            },
            required: ["site", "title", "content"]
          },
        },
        {
          name: "get_posts",
          description: "Get a list of WordPress posts",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              number: { type: "number", description: "Number of posts to retrieve", default: 10 },
              page: { type: "number", description: "Page number", default: 1 }
            },
            required: ["site"]
          },
        },
        {
          name: "update_post",
          description: "Update an existing WordPress post",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
              postId: { type: "number", description: "ID of the post to update" },
              title: { type: "string", description: "Post title in html format" },
              content: { type: "string", description: "Post content in html format" },
              status: { type: "string", description: "Post status (draft, publish, private, pending etc.)" },
            },
            required: ["site", "postId"]
          },
        },
        {
          name: "get_tagged_posts",
          description: "Get posts with a specific tag",
          inputSchema: {
            type: "object",
            properties: {
              tag: { type: "string", description: "Tag to search for" },
              number: { type: "number", description: "Number of posts to retrieve", default: 10 }
            },
            required: ["tag"]
          }
        },
        {
          name: "get_top_posts",
          description: "Get top posts for a site",
          inputSchema: {
            type: "object",
            properties: {
              site: { type: "string", description: "Site identifier (e.g. example.wordpress.com)" },
            },
            required: ["site"]
          }
        }
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const params = request.params.arguments || {};

    try {
      switch (request.params.name) {
        case 'create_post': {
          if (!params.site || !params.title || !params.content) {
            throw new Error('Site, title, and content are required for creating a post');
          }

          const client = getClient();
          const response = await client.post(`/sites/${params.site}/posts/new`, {
            title: params.title,
            content: params.content,
            status: params.status || 'draft',
          });
          const data = await response.json();

          return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
            isError: false,
          };
        }

        case 'get_posts': {
          if (!params.site) {
            throw new Error('Site is required for getting posts');
          }
          
          const client = getClient();
          const number = params.number || 10;
          const page = params.page || 1;
          const response = await client.get(`/sites/${params.site}/posts/?number=${number}&page=${page}`);
          const data = await response.json();

          return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
            isError: false,
          };
        }

        case 'update_post': {
          if (!params.site || !params.postId) {
            throw new Error('Site and Post ID are required for updating a post');
          }

          const updateData: Record<string, any> = {};
          if (params.title) updateData.title = params.title;
          if (params.content) updateData.content = params.content;
          if (params.status) updateData.status = params.status;

          const client = getClient();
          const response = await client.post(`/sites/${params.site}/posts/${params.postId}`, updateData);
          const data = await response.json();

          return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
            isError: false,
          };
        }

        case 'get_tagged_posts': {
          if (!params.tag) {
            throw new Error('Tag is required for getting tagged posts');
          }
          
          const client = getClient();
          const number = params.number || 10;
          const response = await client.get(`/read/tags/${params.tag}/posts?number=${number}`);
          const data = await response.json();

          return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
            isError: false,
          };
        }

        case 'get_top_posts': {
          if (!params.site) {
            throw new Error('Site is required for getting top posts');
          }
          
          const client = getClient();
          const response = await client.get(`/sites/${params.site}/stats/top-posts`);
          const data = await response.json();

          return {
            content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
            isError: false,
          };
        }

        default:
          throw new Error(`Unknown tool: ${request.params.name}`);
      }
    } catch (error) {
      const err = error as Error;
      throw new Error(`WordPress API error: ${err.message}`);
    }
  });

  return server;
}

const app = express();

const transports = new Map<string, SSEServerTransport>();

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  auth_token: string;
}>();

function getClient() {
  const store = asyncLocalStorage.getStore()!;
  const auth_token = store.auth_token;

  return {
    get: async (path: string) => {
      const response = await fetch(`https://public-api.wordpress.com/rest/v1.1${path}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${auth_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }

      return response;
    },
    post: async (path: string, data: any) => {
      const response = await fetch(`https://public-api.wordpress.com/rest/v1.1${path}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${auth_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error ${response.status}: ${errorText}`);
      }

      return response;
    }
  };
}

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

  const server = getWordPressMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    // Use WordPress credentials from environment or headers
    const auth_token = process.env.WORDPRESS_API_KEY || req.headers['x-auth-token'] as string;

    if (!auth_token) {
      console.error('Error: WordPress credentials are missing. Provide them via environment variables or headers.');
      const errorResponse = {
        jsonrpc: '2.0' as '2.0',
        error: {
          code: -32001,
          message: 'Unauthorized, WordPress credentials are missing. Have you set the WordPress credentials?'
        },
        id: 0
      };
      await transport.send(errorResponse);
      await transport.close();
      res.status(401).end(JSON.stringify({ error: "Unauthorized, WordPress credentials are missing. Have you set the WordPress credentials?" }));
      return;
    }

    asyncLocalStorage.run({
      auth_token
    }, async () => {
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
