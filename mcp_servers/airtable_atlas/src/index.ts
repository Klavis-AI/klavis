#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import axios, { AxiosInstance } from "axios";
import { AsyncLocalStorage } from 'async_hooks';
import { FieldOption, fieldRequiresOptions, getDefaultOptions, FieldType } from "./types.js";

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  accessToken: string;
}>();

/**
 * Extract access token from AUTH_DATA environment variable or x-auth-data header.
 * This follows the same pattern as other MCP servers.
 */
function extractAccessToken(req?: Request | null): string {
  // First check AUTH_DATA environment variable (for local testing or pre-configured environments)
  let authData = process.env.AUTH_DATA;

  if (!authData) {
    // Fallback to AIRTABLE_API_KEY for backward compatibility
    const apiKey = process.env.AIRTABLE_API_KEY;
    if (apiKey) {
      return apiKey;
    }
  }

  // If no environment variable, try to extract from request headers
  if (!authData && req?.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error decoding x-auth-data header:', error);
    }
  }

  if (!authData) {
    console.error('Error: Airtable access token is missing. Provide it via AUTH_DATA env var, AIRTABLE_API_KEY env var, or x-auth-data header.');
    return '';
  }

  // Parse the JSON auth data
  try {
    const authDataJson = JSON.parse(authData);
    return authDataJson.access_token ?? authDataJson.token ?? authDataJson.api_key ?? '';
  } catch (error) {
    console.error('Error parsing auth data JSON:', error);
    // If it's not JSON, it might be the token directly
    return authData;
  }
}

/**
 * Get the current access token from AsyncLocalStorage or environment
 */
function getAccessToken(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.accessToken) {
    return store.accessToken;
  }
  // Fallback to extracting from environment for stdio transport
  return extractAccessToken(null);
}

/**
 * Create an axios instance with the current access token
 */
function getAxiosInstance(): AxiosInstance {
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Access token not found');
  }
  return axios.create({
    baseURL: "https://api.airtable.com/v0",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

class AirtableServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "airtable-server",
        version: "0.2.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    
    // Error handling
    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  getServer(): Server {
    return this.server;
  }

  private validateField(field: FieldOption): FieldOption {
    const { type } = field;

    // Remove options for fields that don't need them
    if (!fieldRequiresOptions(type as FieldType)) {
      const { options, ...rest } = field;
      return rest;
    }

    // Add default options for fields that require them
    if (!field.options) {
      return {
        ...field,
        options: getDefaultOptions(type as FieldType),
      };
    }

    return field;
  }

  private setupToolHandlers() {
    // Register available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "list_bases",
          description: "List all accessible Airtable bases",
          inputSchema: {
            type: "object",
            properties: {},
            required: [],
          },
        },
        {
          name: "list_tables",
          description: "List all tables in a base",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
            },
            required: ["base_id"],
          },
        },
        {
          name: "create_table",
          description: "Create a new table in a base",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the new table",
              },
              description: {
                type: "string",
                description: "Description of the table",
              },
              fields: {
                type: "array",
                description: "Initial fields for the table",
                items: {
                  type: "object",
                  properties: {
                    name: {
                      type: "string",
                      description: "Name of the field",
                    },
                    type: {
                      type: "string",
                      description: "Type of the field (e.g., singleLineText, multilineText, number, etc.)",
                    },
                    description: {
                      type: "string",
                      description: "Description of the field",
                    },
                    options: {
                      type: "object",
                      description: "Field-specific options",
                    },
                  },
                  required: ["name", "type"],
                },
              },
            },
            required: ["base_id", "table_name"],
          },
        },
        {
          name: "update_table",
          description: "Update a table's schema",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_id: {
                type: "string",
                description: "ID of the table to update",
              },
              name: {
                type: "string",
                description: "New name for the table",
              },
              description: {
                type: "string",
                description: "New description for the table",
              },
            },
            required: ["base_id", "table_id"],
          },
        },
        {
          name: "create_field",
          description: "Create a new field in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_id: {
                type: "string",
                description: "ID of the table",
              },
              field: {
                type: "object",
                properties: {
                  name: {
                    type: "string",
                    description: "Name of the field",
                  },
                  type: {
                    type: "string",
                    description: "Type of the field",
                  },
                  description: {
                    type: "string",
                    description: "Description of the field",
                  },
                  options: {
                    type: "object",
                    description: "Field-specific options",
                  },
                },
                required: ["name", "type"],
              },
            },
            required: ["base_id", "table_id", "field"],
          },
        },
        {
          name: "update_field",
          description: "Update a field in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_id: {
                type: "string",
                description: "ID of the table",
              },
              field_id: {
                type: "string",
                description: "ID of the field to update",
              },
              updates: {
                type: "object",
                properties: {
                  name: {
                    type: "string",
                    description: "New name for the field",
                  },
                  description: {
                    type: "string",
                    description: "New description for the field",
                  },
                  options: {
                    type: "object",
                    description: "New field-specific options",
                  },
                },
              },
            },
            required: ["base_id", "table_id", "field_id", "updates"],
          },
        },
        {
          name: "list_records",
          description: "List records in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              max_records: {
                type: "number",
                description: "Maximum number of records to return",
              },
            },
            required: ["base_id", "table_name"],
          },
        },
        {
          name: "create_record",
          description: "Create a new record in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              fields: {
                type: "object",
                description: "Record fields as key-value pairs",
              },
            },
            required: ["base_id", "table_name", "fields"],
          },
        },
        {
          name: "update_record",
          description: "Update an existing record in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              record_id: {
                type: "string",
                description: "ID of the record to update",
              },
              fields: {
                type: "object",
                description: "Record fields to update as key-value pairs",
              },
            },
            required: ["base_id", "table_name", "record_id", "fields"],
          },
        },
        {
          name: "delete_record",
          description: "Delete a record from a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              record_id: {
                type: "string",
                description: "ID of the record to delete",
              },
            },
            required: ["base_id", "table_name", "record_id"],
          },
        },
        {
          name: "search_records",
          description: "Search for records in a table",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              field_name: {
                type: "string",
                description: "Name of the field to search in",
              },
              value: {
                type: "string",
                description: "Value to search for",
              },
            },
            required: ["base_id", "table_name", "field_name", "value"],
          },
        },
        {
          name: "get_record",
          description: "Get a single record by its ID",
          inputSchema: {
            type: "object",
            properties: {
              base_id: {
                type: "string",
                description: "ID of the base",
              },
              table_name: {
                type: "string",
                description: "Name of the table",
              },
              record_id: {
                type: "string",
                description: "ID of the record to retrieve",
              },
            },
            required: ["base_id", "table_name", "record_id"],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        switch (request.params.name) {
          case "list_bases": {
            const response = await getAxiosInstance().get("/meta/bases");
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data.bases, null, 2),
              }],
            };
          }

          case "list_tables": {
            const { base_id } = request.params.arguments as { base_id: string };
            const response = await getAxiosInstance().get(`/meta/bases/${base_id}/tables`);
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data.tables, null, 2),
              }],
            };
          }

          case "create_table": {
            const { base_id, table_name, description, fields } = request.params.arguments as {
              base_id: string;
              table_name: string;
              description?: string;
              fields?: FieldOption[];
            };
            
            // Validate and prepare fields
            const validatedFields = fields?.map(field => this.validateField(field));
            
            const response = await getAxiosInstance().post(`/meta/bases/${base_id}/tables`, {
              name: table_name,
              description,
              fields: validatedFields,
            });
            
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "update_table": {
            const { base_id, table_id, name, description } = request.params.arguments as {
              base_id: string;
              table_id: string;
              name?: string;
              description?: string;
            };
            
            const response = await getAxiosInstance().patch(`/meta/bases/${base_id}/tables/${table_id}`, {
              name,
              description,
            });
            
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "create_field": {
            const { base_id, table_id, field } = request.params.arguments as {
              base_id: string;
              table_id: string;
              field: FieldOption;
            };
            
            // Validate field before creation
            const validatedField = this.validateField(field);
            
            const response = await getAxiosInstance().post(
              `/meta/bases/${base_id}/tables/${table_id}/fields`,
              validatedField
            );
            
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "update_field": {
            const { base_id, table_id, field_id, updates } = request.params.arguments as {
              base_id: string;
              table_id: string;
              field_id: string;
              updates: Partial<FieldOption>;
            };
            
            const response = await getAxiosInstance().patch(
              `/meta/bases/${base_id}/tables/${table_id}/fields/${field_id}`,
              updates
            );
            
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "list_records": {
            const { base_id, table_name, max_records } = request.params.arguments as {
              base_id: string;
              table_name: string;
              max_records?: number;
            };
            const response = await getAxiosInstance().get(`/${base_id}/${table_name}`, {
              params: max_records ? { maxRecords: max_records } : undefined,
            });
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data.records, null, 2),
              }],
            };
          }

          case "create_record": {
            const { base_id, table_name, fields } = request.params.arguments as {
              base_id: string;
              table_name: string;
              fields: Record<string, any>;
            };
            const response = await getAxiosInstance().post(`/${base_id}/${table_name}`, {
              fields,
            });
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "update_record": {
            const { base_id, table_name, record_id, fields } = request.params.arguments as {
              base_id: string;
              table_name: string;
              record_id: string;
              fields: Record<string, any>;
            };
            const response = await getAxiosInstance().patch(
              `/${base_id}/${table_name}/${record_id}`,
              { fields }
            );
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "delete_record": {
            const { base_id, table_name, record_id } = request.params.arguments as {
              base_id: string;
              table_name: string;
              record_id: string;
            };
            const response = await getAxiosInstance().delete(
              `/${base_id}/${table_name}/${record_id}`
            );
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          case "search_records": {
            const { base_id, table_name, field_name, value } = request.params.arguments as {
              base_id: string;
              table_name: string;
              field_name: string;
              value: string;
            };
            const response = await getAxiosInstance().get(`/${base_id}/${table_name}`, {
              params: {
                filterByFormula: `{${field_name}} = "${value}"`,
              },
            });
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data.records, null, 2),
              }],
            };
          }

          case "get_record": {
            const { base_id, table_name, record_id } = request.params.arguments as {
              base_id: string;
              table_name: string;
              record_id: string;
            };
            const response = await getAxiosInstance().get(
              `/${base_id}/${table_name}/${record_id}`
            );
            return {
              content: [{
                type: "text",
                text: JSON.stringify(response.data, null, 2),
              }],
            };
          }

          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${request.params.name}`);
        }
      } catch (error) {
        if (axios.isAxiosError(error)) {
          throw new McpError(
            ErrorCode.InternalError,
            `Airtable API error: ${error.response?.data?.error?.message ?? error.message}`
          );
        }
        throw error;
      }
    });
  }

  async runStdio() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Airtable MCP server running on stdio");
  }
}

// Factory function to create a new server instance
function createAirtableServer(): AirtableServer {
  return new AirtableServer();
}

//=============================================================================
// HTTP SERVER SETUP
//=============================================================================

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const accessToken = extractAccessToken(req);

  const airtableServer = createAirtableServer();
  const server = airtableServer.getServer();
  
  try {
    const transport = new StreamableHTTPServerTransport({
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

app.get("/sse", async (req: Request, res: Response) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
      // Cleanup complete
    }
  });

  transports.set(transport.sessionId, transport);

  const airtableServer = createAirtableServer();
  const server = airtableServer.getServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req: Request, res: Response) => {
  const sessionId = req.query.sessionId as string;

  const transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const accessToken = extractAccessToken(req);

    asyncLocalStorage.run({ accessToken }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

//=============================================================================
// MAIN ENTRY POINT
//=============================================================================

const PORT = parseInt(process.env.PORT || '5000', 10);
const TRANSPORT = process.env.TRANSPORT || 'http';

if (TRANSPORT === 'stdio') {
  // Run in stdio mode (for local testing with MCP clients)
  const server = createAirtableServer();
  server.runStdio().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
  });
} else {
  // Run in HTTP mode (for production with SSE and Streamable HTTP)
  app.listen(PORT, () => {
    console.log(`Airtable MCP server running on port ${PORT}`);
    console.log(`  - Streamable HTTP: POST /mcp`);
    console.log(`  - SSE: GET /sse, POST /messages`);
  });
}
