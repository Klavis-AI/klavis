import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    Tool,
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

dotenv.config();

// Attio API configuration
const ATTIO_API_URL = 'https://api.attio.com/v2';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    attioClient: AttioClient;
}>();

// Attio API Client
class AttioClient {
    private apiKey: string;
    private baseUrl: string;

    constructor(apiKey: string, baseUrl: string = ATTIO_API_URL) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Attio API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    async searchPeople(filters: any = {}, limit: number = 25): Promise<any> {
        return this.makeRequest('/objects/people/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchCompanies(filters: any = {}, limit: number = 25): Promise<any> {
        return this.makeRequest('/objects/companies/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchDeals(filters: any = {}, limit: number = 25): Promise<any> {
        return this.makeRequest('/objects/deals/records/query', {
            method: 'POST',
            body: JSON.stringify({
                filter: filters,
                limit
            }),
        });
    }

    async searchNotes(query: string, limit: number = 50): Promise<any> {
        // First, get all notes (up to the limit)
        const allNotes = await this.makeRequest(`/notes?limit=${limit}`, {
            method: 'GET',
        });

        // If no query provided, return all notes
        if (!query || query.trim() === '') {
            return allNotes;
        }

        // Filter notes based on query matching title or content
        const queryLower = query.toLowerCase();
        const filteredNotes = allNotes.data.filter((note: any) => {
            const titleMatch = note.title?.toLowerCase().includes(queryLower);
            const contentPlaintextMatch = note.content_plaintext?.toLowerCase().includes(queryLower);
            const contentMarkdownMatch = note.content_markdown?.toLowerCase().includes(queryLower);

            return titleMatch || contentPlaintextMatch || contentMarkdownMatch;
        });

        return {
            ...allNotes,
            data: filteredNotes
        };
    }

    async createNote(data: {
        parent_object: string;
        parent_record_id: string;
        title: string;
        content: string;
        format?: 'plaintext' | 'markdown';
    }): Promise<any> {
        return this.makeRequest('/notes', {
            method: 'POST',
            body: JSON.stringify({
                data: {
                    parent_object: data.parent_object,
                    parent_record_id: data.parent_record_id,
                    title: data.title,
                    format: data.format || 'plaintext',
                    content: data.content
                }
            }),
        });
    }
}

// Getter function for the client
function getAttioClient() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Attio client not found in AsyncLocalStorage');
    }
    return store.attioClient;
}

// Tool definitions
const SEARCH_PEOPLE_TOOL: Tool = {
    name: 'attio_search_people',
    description: 'Search for people in your Attio workspace with advanced filtering options.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for people (searches across name, email, company, job title, description, etc.)',
            },
            email: {
                type: 'string',
                description: 'Filter by email address',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
};

const SEARCH_COMPANIES_TOOL: Tool = {
    name: 'attio_search_companies',
    description: 'Search for companies in your Attio workspace with filtering and sorting.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for companies (searches across name, domain, description, employees names, employees descriptions, etc.)',
            },
            domain: {
                type: 'string',
                description: 'Filter by company domain',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
};

const SEARCH_DEALS_TOOL: Tool = {
    name: 'attio_search_deals',
    description: 'Search for deals in your Attio workspace with stage and value filtering.',
    inputSchema: {
        type: 'object',
        properties: {
            name: {
                type: 'string',
                description: 'Filter by deal name',
            },
            stage: {
                type: 'string',
                description: 'Filter by deal stage (one of "Lead", "In Progress", "Won 🎉", "Lost")',
            },
            minValue: {
                type: 'number',
                description: 'Minimum deal value',
            },
            maxValue: {
                type: 'number',
                description: 'Maximum deal value',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 25, max: 50)',
                default: 25,
            },
        },
    },
};

const SEARCH_NOTES_TOOL: Tool = {
    name: 'attio_search_notes',
    description: 'Search for notes across all objects in your Attio workspace by fetching all notes and filtering by content.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query for notes content (searches title, plaintext content, and markdown content). Leave empty to get all notes.',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of notes to fetch and search through (default: 50, max: 50)',
                default: 50,
            },
        },
    },
};

const CREATE_NOTE_TOOL: Tool = {
    name: 'attio_create_note',
    description: 'Create a new note for a given record in Attio.',
    inputSchema: {
        type: 'object',
        properties: {
            parent_object: {
                type: 'string',
                description: 'The object type to attach the note to (e.g., "people", "companies", "deals")',
                enum: ['people', 'companies', 'deals']
            },
            parent_record_id: {
                type: 'string',
                description: 'The ID of the record to attach the note to'
            },
            title: {
                type: 'string',
                description: 'Title of the note'
            },
            content: {
                type: 'string',
                description: 'Content of the note'
            },
            format: {
                type: 'string',
                description: 'Format of the note content',
                enum: ['plaintext', 'markdown'],
                default: 'plaintext'
            }
        },
        required: ['parent_object', 'parent_record_id', 'title', 'content'],
    },
};

// Utility functions
function safeLog(level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency', data: any): void {
    try {
        const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
        console.log(`[${level.toUpperCase()}] ${logData}`);
    } catch (error) {
        console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
    }
}

// Main server function
const getAttioMcpServer = () => {
    const server = new Server(
        {
            name: 'attio-mcp-server',
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
                SEARCH_PEOPLE_TOOL,
                SEARCH_COMPANIES_TOOL,
                SEARCH_DEALS_TOOL,
                SEARCH_NOTES_TOOL,
                CREATE_NOTE_TOOL,
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'attio_search_people': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.query) {
                        filters.$or = [
                            { name: { $contains: args.query } },
                            { email_addresses: { $contains: args.query } },
                            { description: { $contains: args.query } },
                            { job_title: { $contains: args.query } },
                            {
                                path: [
                                    ["people", "company"],
                                    ["companies", "name"]
                                ],
                                constraints: {
                                    $contains: args.query
                                }
                            },
                            {
                                path: [
                                    ["people", "company"],
                                    ["companies", "description"]
                                ],
                                constraints: {
                                    $contains: args.query
                                }
                            },
                            { primary_location: { locality: { $contains: args.query } } },
                        ];
                    }
                    if (args?.email) {
                        filters.email_addresses = args.email;
                    }

                    const result = await client.searchPeople(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_companies': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.query) {
                        filters.$or = [
                            { name: { $contains: args.query } },
                            { domains: { domain: { $contains: args.query } } },
                            { description: { $contains: args.query } },
                            { primary_location: { locality: { $contains: args.query } } },
                            {
                                path: [
                                    ["companies", "team"],
                                    ["people", "name"]
                                ],
                                constraints: {
                                    $contains: args.query
                                }
                            },
                            {
                                path: [
                                    ["companies", "team"],
                                    ["people", "description"]
                                ],
                                constraints: {
                                    $contains: args.query
                                }
                            },
                        ];
                    }
                    if (args?.domain) {
                        filters.domains = { domain: args.domain };
                    }

                    const result = await client.searchCompanies(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_deals': {
                    const client = getAttioClient();
                    const filters: any = {};

                    if (args?.name) {
                        filters.name = { $contains: args.name };
                    }
                    if (args?.stage) {
                        filters.stage = args.stage;
                    }
                    if (args?.minValue !== undefined || args?.maxValue !== undefined) {
                        filters.value = {};
                        if (args?.minValue !== undefined) {
                            filters.value.$gte = args.minValue;
                        }
                        if (args?.maxValue !== undefined) {
                            filters.value.$lte = args.maxValue;
                        }
                    }

                    const result = await client.searchDeals(filters, (args?.limit as number) || 25);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_search_notes': {
                    const client = getAttioClient();
                    const result = await client.searchNotes((args as any)?.query || '', (args?.limit as number) || 50);

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'attio_create_note': {
                    const client = getAttioClient();

                    const result = await client.createNote({
                        parent_object: (args as any)?.parent_object,
                        parent_record_id: (args as any)?.parent_record_id,
                        title: (args as any)?.title,
                        content: (args as any)?.content,
                        format: (args as any)?.format || 'plaintext'
                    });

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            safeLog('error', `Tool ${name} failed: ${error.message}`);
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


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const apiKey = process.env.ATTIO_API_KEY || req.headers['x-auth-token'] as string;

    if (!apiKey) {
        console.error('Error: Attio API key is missing. Provide it via ATTIO_API_KEY env var or x-auth-token header.');
    }

    const attioClient = new AttioClient(apiKey);

    const server = getAttioMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ attioClient }, async () => {
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

    const server = getAttioMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        const apiKey = process.env.ATTIO_API_KEY || req.headers['x-auth-token'] as string;

        if (!apiKey) {
            console.error('Error: Attio API key is missing. Provide it via ATTIO_API_KEY env var or x-auth-token header.');
        }

        const attioClient = new AttioClient(apiKey);

        asyncLocalStorage.run({ attioClient }, async () => {
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