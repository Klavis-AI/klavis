#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequest,
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from 'zod';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';
import fetch, { RequestInit } from 'node-fetch';

// Load environment variables
dotenv.config();

// Default fields for Confluence content
const DEFAULT_READ_CONFLUENCE_FIELDS = [
  "id",
  "type",
  "status", 
  "title",
  "space",
  "version",
  "body",
  "metadata",
  "extensions"
];

// Define interfaces for Confluence API client
interface ConfluenceClient {
  baseUrl: string;
  cloudId: string;
  authToken: string;
  fetch: <T>(path: string, options?: RequestInit) => Promise<T>;
}

// Type definitions for tool arguments
interface ConfluenceSearchContentArgs {
  cql: string;
  limit?: number;
  start?: number;
  expand?: string;
  space_key?: string;
}

interface ConfluenceGetContentArgs {
  content_id: string;
  expand?: string;
  version?: number;
}

interface ConfluenceGetSpaceArgs {
  space_key: string;
  expand?: string;
}

interface ConfluenceListSpacesArgs {
  limit?: number;
  start?: number;
  type?: string;
  status?: string;
  expand?: string;
}

interface ConfluenceCreatePageArgs {
  space_key: string;
  title: string;
  body: string;
  parent_id?: string;
  status?: string;
  labels?: string[];
}

interface ConfluenceUpdatePageArgs {
  content_id: string;
  title?: string;
  body?: string;
  version?: number;
  status?: string;
  labels?: string[];
}

interface ConfluenceDeleteContentArgs {
  content_id: string;
}

interface ConfluenceGetChildContentArgs {
  content_id: string;
  type?: string;
  limit?: number;
  start?: number;
  expand?: string;
}

interface ConfluenceGetLabelArgs {
  content_id: string;
  prefix?: string;
  start?: number;
  limit?: number;
}

interface ConfluenceAddLabelArgs {
  content_id: string;
  labels: string[];
}

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  confluenceClient: ConfluenceClient;
}>();

// Helper function to get Confluence client from async local storage
function getConfluenceClient(): ConfluenceClient {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('Confluence client not found in AsyncLocalStorage');
  }
  return store.confluenceClient;
}

// Create a Confluence API client
async function createConfluenceClient(authToken: string): Promise<ConfluenceClient> {
  // First, fetch the accessible resources to get the correct baseUrl
  const accessibleResourcesUrl = 'https://api.atlassian.com/oauth/token/accessible-resources';

  try {
    const response = await fetch(accessibleResourcesUrl, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch accessible resources: ${response.statusText}`);
    }

    interface ConfluenceResource {
      id: string;
      name: string;
      url: string;
      scopes: string[];
      avatarUrl: string;
    }

    const resources = await response.json() as ConfluenceResource[];

    if (!resources || resources.length === 0) {
      throw new Error('No accessible Confluence resources found');
    }

    // Use the first resource by default
    const cloudId = resources[0].id;
    const baseUrl = `https://api.atlassian.com/ex/confluence/${cloudId}`;

    console.log(`Using Confluence cloud ID: ${cloudId}`);
    console.log(`Using Confluence base URL: ${baseUrl}`);

    return {
      baseUrl,
      cloudId,
      authToken,
      async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
        const url = `${baseUrl}${path}`;
        
        const requestOptions: RequestInit = {
          ...options,
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            ...options.headers,
          },
        };

        console.log(`Fetching ${options.method || 'GET'} ${url}`);
        
        const response = await fetch(url, requestOptions);
        
        if (response.status === 204) {
          // No content response
          return {} as T;
        }

        if (!response.ok) {
          console.error(`Error from Confluence API: ${response.status} ${response.statusText}`);
          const errorText = await response.text();
          console.error(`Error details: ${errorText}`);
          throw new Error(`Confluence API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        // Some endpoints return no content (204) but fetch still tries to parse JSON
        if (response.headers.get('content-length') === '0') {
          return {} as T;
        }

        try {
          const data = await response.json();
          return data as T;
        } catch (error) {
          console.error('Error parsing JSON response:', error);
          throw new Error(`Failed to parse JSON response: ${error}`);
        }
      },
    };
  } catch (error) {
    console.error('Error creating Confluence client:', error);
    throw error;
  }
}

// Define the available tools
const searchContentTool: Tool = {
  name: "confluence_search_content",
  description: "Search for content in Confluence using CQL (Confluence Query Language)",
  inputSchema: {
    type: "object",
    properties: {
      cql: {
        type: "string",
        description: "Confluence Query Language (CQL) search query",
      },
      limit: {
        type: "number",
        description: "Maximum number of results to return",
      },
      start: {
        type: "number",
        description: "Index of the first result to return (0-based)",
      },
      expand: {
        type: "string",
        description: "A comma-separated list of properties to expand in the response",
      },
      space_key: {
        type: "string",
        description: "Key of the space to search in",
      },
    },
    required: ["cql"],
  },
};

const getContentTool: Tool = {
  name: "confluence_get_content",
  description: "Get Confluence content by ID",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the content to retrieve",
      },
      expand: {
        type: "string",
        description: "A comma-separated list of properties to expand in the response",
      },
      version: {
        type: "number",
        description: "Version number to retrieve",
      },
    },
    required: ["content_id"],
  },
};

const getSpaceTool: Tool = {
  name: "confluence_get_space",
  description: "Get information about a Confluence space",
  inputSchema: {
    type: "object",
    properties: {
      space_key: {
        type: "string",
        description: "Key of the space to retrieve",
      },
      expand: {
        type: "string",
        description: "A comma-separated list of properties to expand in the response",
      },
    },
    required: ["space_key"],
  },
};

const listSpacesTool: Tool = {
  name: "confluence_list_spaces",
  description: "List available Confluence spaces",
  inputSchema: {
    type: "object",
    properties: {
      limit: {
        type: "number",
        description: "Maximum number of results to return",
      },
      start: {
        type: "number",
        description: "Index of the first result to return (0-based)",
      },
      type: {
        type: "string",
        description: "Type of spaces to return (e.g., 'global', 'personal')",
      },
      status: {
        type: "string",
        description: "Status of spaces to return (e.g., 'current', 'archived')",
      },
      expand: {
        type: "string",
        description: "A comma-separated list of properties to expand in the response",
      },
    },
    required: [],
  },
};

const createPageTool: Tool = {
  name: "confluence_create_page",
  description: "Create a new page in Confluence",
  inputSchema: {
    type: "object",
    properties: {
      space_key: {
        type: "string",
        description: "Key of the space to create the page in",
      },
      title: {
        type: "string",
        description: "Title of the page",
      },
      body: {
        type: "string",
        description: "Body content of the page (can be plain text or Atlassian Document Format JSON)",
      },
      parent_id: {
        type: "string",
        description: "ID of the parent page (for creating child pages)",
      },
      status: {
        type: "string",
        description: "Status of the page (e.g., 'current', 'draft')",
      },
      labels: {
        type: "array",
        items: {
          type: "string",
        },
        description: "Labels to add to the page",
      },
    },
    required: ["space_key", "title", "body"],
  },
};

const updatePageTool: Tool = {
  name: "confluence_update_page",
  description: "Update an existing page in Confluence",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the content to update",
      },
      title: {
        type: "string",
        description: "New title for the page",
      },
      body: {
        type: "string",
        description: "New body content for the page (can be plain text or Atlassian Document Format JSON)",
      },
      version: {
        type: "number",
        description: "Current version number of the page (required for updates)",
      },
      status: {
        type: "string",
        description: "New status for the page (e.g., 'current', 'draft')",
      },
      labels: {
        type: "array",
        items: {
          type: "string",
        },
        description: "Labels to set on the page",
      },
    },
    required: ["content_id"],
  },
};

const deleteContentTool: Tool = {
  name: "confluence_delete_content",
  description: "Delete content from Confluence",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the content to delete",
      },
    },
    required: ["content_id"],
  },
};

const getChildContentTool: Tool = {
  name: "confluence_get_child_content",
  description: "Get child content for a specific piece of content",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the parent content",
      },
      type: {
        type: "string",
        description: "Type of children to return (e.g., 'page', 'comment', 'attachment')",
      },
      limit: {
        type: "number",
        description: "Maximum number of results to return",
      },
      start: {
        type: "number",
        description: "Index of the first result to return (0-based)",
      },
      expand: {
        type: "string",
        description: "A comma-separated list of properties to expand in the response",
      },
    },
    required: ["content_id"],
  },
};

const getLabelsTool: Tool = {
  name: "confluence_get_labels",
  description: "Get labels for a specific piece of content",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the content",
      },
      prefix: {
        type: "string",
        description: "Filter labels by prefix",
      },
      start: {
        type: "number",
        description: "Index of the first result to return (0-based)",
      },
      limit: {
        type: "number",
        description: "Maximum number of results to return",
      },
    },
    required: ["content_id"],
  },
};

const addLabelsTool: Tool = {
  name: "confluence_add_labels",
  description: "Add labels to a specific piece of content",
  inputSchema: {
    type: "object",
    properties: {
      content_id: {
        type: "string",
        description: "ID of the content",
      },
      labels: {
        type: "array",
        items: {
          type: "string",
        },
        description: "Labels to add to the content",
      },
    },
    required: ["content_id", "labels"],
  },
};

const getConfluenceMcpServer = () => {
  const server = new Server(
    {
      name: "confluence-service",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(
    ListToolsRequestSchema,
    async () => {
      return {
        tools: [
          searchContentTool,
          getContentTool,
          getSpaceTool,
          listSpacesTool,
          createPageTool,
          updatePageTool,
          deleteContentTool,
          getChildContentTool,
          getLabelsTool,
          addLabelsTool,
        ],
      };
    }
  );

  server.setRequestHandler(
    CallToolRequestSchema,
    async (request: CallToolRequest) => {
      try {
        // Validate the request parameters
        if (!request.params?.name) {
          throw new Error("Missing tool name");
        }

        const confluence = getConfluenceClient();

        console.log("--- request.params.name", request.params.name);

        // Process the tool call based on the tool name
        switch (request.params.name) {
          case "confluence_search_content": {
            const args = request.params.arguments as unknown as ConfluenceSearchContentArgs;
            if (!args.cql) {
              throw new Error("Missing required argument: cql");
            }

            const searchParams = new URLSearchParams();
            searchParams.append('cql', args.cql);

            if (args.limit) {
              searchParams.append('limit', String(args.limit));
            } else {
              searchParams.append('limit', "10");
            }

            if (args.start !== undefined) {
              searchParams.append('start', String(args.start));
            }

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            // Filter by space if specified
            const spaceKey = args.space_key || process.env.CONFLUENCE_SPACE_KEY;
            if (spaceKey && !args.cql.toLowerCase().includes("space =")) {
              args.cql = `${args.cql} AND space = "${spaceKey}"`;
              searchParams.set('cql', args.cql);
            }

            const response = await confluence.fetch<any>(`/wiki/rest/api/search?${searchParams.toString()}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_get_content": {
            const args = request.params.arguments as unknown as ConfluenceGetContentArgs;
            if (!args.content_id) {
              throw new Error("Missing required argument: content_id");
            }

            const searchParams = new URLSearchParams();

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            if (args.version) {
              searchParams.append('version', String(args.version));
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_get_space": {
            const args = request.params.arguments as unknown as ConfluenceGetSpaceArgs;
            if (!args.space_key) {
              throw new Error("Missing required argument: space_key");
            }

            const searchParams = new URLSearchParams();

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await confluence.fetch<any>(`/wiki/rest/api/space/${args.space_key}${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_list_spaces": {
            const args = request.params.arguments as unknown as ConfluenceListSpacesArgs;
            
            const searchParams = new URLSearchParams();

            if (args.limit) {
              searchParams.append('limit', String(args.limit));
            } else {
              searchParams.append('limit', "10");
            }

            if (args.start !== undefined) {
              searchParams.append('start', String(args.start));
            }

            if (args.type) {
              searchParams.append('type', args.type);
            }

            if (args.status) {
              searchParams.append('status', args.status);
            }

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await confluence.fetch<any>(`/wiki/rest/api/space${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_create_page": {
            const args = request.params.arguments as unknown as ConfluenceCreatePageArgs;
            if (!args.space_key || !args.title || !args.body) {
              throw new Error("Missing required arguments: space_key, title, and body");
            }

            // Check if body is plain text or already in Atlassian Document Format
            let bodyContent;
            try {
              const parsedBody = JSON.parse(args.body);
              // If parsing succeeds, body is likely already in ADF
              bodyContent = parsedBody;
            } catch (error) {
              // If parsing fails, body is plain text, convert to ADF
              bodyContent = {
                type: "doc",
                version: 1,
                content: [
                  {
                    type: "paragraph",
                    content: [
                      {
                        type: "text",
                        text: args.body,
                      },
                    ],
                  },
                ],
              };
            }

            const payload: any = {
              type: "page",
              title: args.title,
              space: {
                key: args.space_key,
              },
              body: {
                storage: {
                  value: JSON.stringify(bodyContent),
                  representation: "atlas_doc_format",
                },
              },
            };

            if (args.parent_id) {
              payload.ancestors = [
                {
                  id: args.parent_id,
                },
              ];
            }

            if (args.status) {
              payload.status = args.status;
            }

            const response = await confluence.fetch<any>(`/wiki/rest/api/content`, {
              method: 'POST',
              body: JSON.stringify(payload),
            });

            // Add labels if provided
            if (args.labels && args.labels.length > 0 && response.id) {
              const labelPayload = args.labels.map(label => ({ name: label }));
              
              await confluence.fetch<any>(`/wiki/rest/api/content/${response.id}/label`, {
                method: 'POST',
                body: JSON.stringify(labelPayload),
              });
            }

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_update_page": {
            const args = request.params.arguments as unknown as ConfluenceUpdatePageArgs;
            if (!args.content_id) {
              throw new Error("Missing required argument: content_id");
            }

            // First, get the current page to get the version number if not provided
            let currentVersion = args.version;
            if (!currentVersion) {
              const currentPage = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}`);
              currentVersion = currentPage.version.number;
            }

            // Build the update payload
            const payload: any = {
              version: {
                number: currentVersion + 1,
              },
            };

            if (args.title) {
              payload.title = args.title;
            }

            if (args.body) {
              // Check if body is plain text or already in Atlassian Document Format
              let bodyContent;
              try {
                const parsedBody = JSON.parse(args.body);
                // If parsing succeeds, body is likely already in ADF
                bodyContent = parsedBody;
              } catch (error) {
                // If parsing fails, body is plain text, convert to ADF
                bodyContent = {
                  type: "doc",
                  version: 1,
                  content: [
                    {
                      type: "paragraph",
                      content: [
                        {
                          type: "text",
                          text: args.body,
                        },
                      ],
                    },
                  ],
                };
              }

              payload.body = {
                storage: {
                  value: JSON.stringify(bodyContent),
                  representation: "atlas_doc_format",
                },
              };
            }

            if (args.status) {
              payload.status = args.status;
            }

            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}`, {
              method: 'PUT',
              body: JSON.stringify(payload),
            });

            // Update labels if provided
            if (args.labels && args.labels.length > 0) {
              // First, delete existing labels
              await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}/label`, {
                method: 'DELETE',
              });

              // Then add new labels
              const labelPayload = args.labels.map(label => ({ name: label }));
              
              await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}/label`, {
                method: 'POST',
                body: JSON.stringify(labelPayload),
              });
            }

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_delete_content": {
            const args = request.params.arguments as unknown as ConfluenceDeleteContentArgs;
            if (!args.content_id) {
              throw new Error("Missing required argument: content_id");
            }

            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}`, {
              method: 'DELETE'
            });

            // Note: Confluence DELETE content often returns 204 No Content on success.
            // If the response is empty or undefined, return a success message.
            // Otherwise, return the actual response.
            const responseText = response ? JSON.stringify(response) : JSON.stringify({ message: `Content ${args.content_id} deleted successfully (status 204)` });

            return {
              content: [
                {
                  type: "text",
                  text: responseText,
                },
              ],
            };
          }

          case "confluence_get_child_content": {
            const args = request.params.arguments as unknown as ConfluenceGetChildContentArgs;
            if (!args.content_id) {
              throw new Error("Missing required argument: content_id");
            }

            const searchParams = new URLSearchParams();

            if (args.type) {
              searchParams.append('type', args.type);
            }

            if (args.limit) {
              searchParams.append('limit', String(args.limit));
            } else {
              searchParams.append('limit', "10");
            }

            if (args.start !== undefined) {
              searchParams.append('start', String(args.start));
            }

            if (args.expand) {
              searchParams.append('expand', args.expand);
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}/child${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_get_labels": {
            const args = request.params.arguments as unknown as ConfluenceGetLabelArgs;
            if (!args.content_id) {
              throw new Error("Missing required argument: content_id");
            }

            const searchParams = new URLSearchParams();

            if (args.prefix) {
              searchParams.append('prefix', args.prefix);
            }

            if (args.limit) {
              searchParams.append('limit', String(args.limit));
            } else {
              searchParams.append('limit', "10");
            }

            if (args.start !== undefined) {
              searchParams.append('start', String(args.start));
            }

            const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}/label${query}`);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          case "confluence_add_labels": {
            const args = request.params.arguments as unknown as ConfluenceAddLabelArgs;
            if (!args.content_id || !args.labels || args.labels.length === 0) {
              throw new Error("Missing required arguments: content_id and labels");
            }

            const labelPayload = args.labels.map(label => ({ name: label }));
            
            const response = await confluence.fetch<any>(`/wiki/rest/api/content/${args.content_id}/label`, {
              method: 'POST',
              body: JSON.stringify(labelPayload),
            });

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response),
                },
              ],
            };
          }

          default:
            throw new Error(`Unknown tool: ${request.params.name}`);
        }
      } catch (error) {
        console.error("Error executing tool:", error);

        if (error instanceof z.ZodError) {
          throw new Error(`Invalid input: ${JSON.stringify(error.errors)}`);
        }

        throw error;
      }
    }
  );

  return server;
};

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const authToken = req.headers['x-auth-token'] as string;

  if (!authToken) {
    console.error('Error: Confluence API token is missing. Provide it via x-auth-token header.');
  }

  const confluenceClient = await createConfluenceClient(authToken);
  const server = getConfluenceMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ confluenceClient }, async () => {
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
    transports.delete(transport.sessionId);
  });

  transports.set(transport.sessionId, transport);

  const server = getConfluenceMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const authToken = req.headers['x-auth-token'] as string;

    if (!authToken) {
      console.error('Error: Confluence API token is missing. Provide it via x-auth-token header.');
    }

    const confluenceClient = await createConfluenceClient(authToken);

    asyncLocalStorage.run({ confluenceClient }, async () => {
      await transport!.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Confluence MCP Server running on port ${PORT}`);
}); 