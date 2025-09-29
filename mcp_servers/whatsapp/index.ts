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

// WhatsApp Business API configuration
const WHATSAPP_API_URL = 'https://graph.facebook.com';
const API_VERSION = 'v23.0';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    accessToken: string;
}>();

// WhatsApp Business API Client
class WhatsAppClient {
    private accessToken: string;
    private phoneNumberId: string;
    private baseUrl: string;

    constructor(accessToken: string, phoneNumberId: string, baseUrl: string = WHATSAPP_API_URL) {
        this.accessToken = accessToken;
        this.phoneNumberId = phoneNumberId;
        this.baseUrl = baseUrl;
    }

    private async makeRequest(endpoint: string, data: any): Promise<any> {
        const url = `${this.baseUrl}/${API_VERSION}/${this.phoneNumberId}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
        };

        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`WhatsApp API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    async sendTextMessage(data: {
        to: string;
        text: string;
        preview_url?: boolean;
    }): Promise<any> {
        const messageData = {
            messaging_product: "whatsapp",
            recipient_type: "individual",
            to: data.to,
            type: "text",
            text: {
                preview_url: data.preview_url || false,
                body: data.text
            }
        };

        return this.makeRequest('/messages', messageData);
    }
}

function getAccessToken() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Access token not found in AsyncLocalStorage');
    }
    return store.accessToken;
}

// Tool definitions
const SEND_TEXT_MESSAGE_TOOL: Tool = {
    name: 'whatsapp_send_text',
    description: 'Send a text message to a WhatsApp user using the WhatsApp Business API.',
    inputSchema: {
        type: 'object',
        properties: {
            phone_number_id: {
                type: 'string',
                description: 'WhatsApp Business phone number ID (e.g., 123456789012345)',
            },
            to: {
                type: 'string',
                description: 'WhatsApp user phone number in international format (e.g., +16505551234)',
            },
            text: {
                type: 'string',
                description: 'Body text of the message. URLs are automatically hyperlinked. Maximum 1024 characters.',
            },
            preview_url: {
                type: 'boolean',
                description: 'Set to true to have the WhatsApp client attempt to render a link preview of any URL in the body text string.',
                default: false,
            },
        },
        required: ['phone_number_id', 'to', 'text'],
    },
    annotations: {
        category: 'WHATSAPP_MESSAGE',
    },
};

function safeLog(level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency', data: any): void {
    try {
        console.log(`[${level.toUpperCase()}]`, typeof data === 'string' ? data : JSON.stringify(data, null, 2));
    } catch (error) {
        console.log(`[${level.toUpperCase()}] [LOG_ERROR]`, data);
    }
}

const getWhatsAppMcpServer = () => {
    const server = new Server(
        {
            name: 'whatsapp-mcp-server',
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
                SEND_TEXT_MESSAGE_TOOL,
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'whatsapp_send_text': {
                    const accessToken = getAccessToken();
                    const phoneNumberId = (args as any)?.phone_number_id;
                    const client = new WhatsAppClient(accessToken, phoneNumberId);
                    const result = await client.sendTextMessage({
                        to: (args as any)?.to,
                        text: (args as any)?.text,
                        preview_url: (args as any)?.preview_url,
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

function extractApiKey(req: Request): string {
    let authData = process.env.API_KEY;

    if (authData) {
        return authData;
    }
    
    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data JSON:', error);
        }
    }

    if (!authData) {
        console.error('Error: WhatsApp API key is missing. Provide it via API_KEY env var or x-auth-data header with token field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.token ?? authDataJson.api_key ?? '';
}

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const accessToken = extractApiKey(req);

    const server = getWhatsAppMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
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

    const server = getWhatsAppMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        const accessToken = extractApiKey(req);

        asyncLocalStorage.run({ accessToken }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

app.listen(5000, () => {
    console.log('WhatsApp MCP server running on port 5000');
}); 