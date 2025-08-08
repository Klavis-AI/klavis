import dotenv from "dotenv";
import express, { Request, Response } from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from "async_hooks";

dotenv.config();

// Mixpanel API configuration
const MIXPANEL_API_URL = 'https://mixpanel.com/api';
const MIXPANEL_TRACK_URL = 'https://api.mixpanel.com';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    mixpanelClient: MixpanelClient;
}>();

// Mixpanel API Client
class MixpanelClient {
    private projectToken: string;
    private username: string;
    private secret: string;
    private apiUrl: string;
    private trackUrl: string;

    constructor(projectToken: string, username: string, secret: string) {
        this.projectToken = projectToken;
        this.username = username;
        this.secret = secret;
        this.apiUrl = MIXPANEL_API_URL;
        this.trackUrl = MIXPANEL_TRACK_URL;
    }

    private async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
        const url = `${this.apiUrl}${endpoint}`;
        const auth = Buffer.from(`${this.username}:${this.secret}`).toString('base64');
        
        const headers = {
            'Authorization': `Basic ${auth}`,
            'Content-Type': 'application/json',
            ...options.headers,
        };

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Mixpanel API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    private async makeTrackRequest(endpoint: string, data: any): Promise<any> {
        const url = `${this.trackUrl}${endpoint}`;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Mixpanel Track API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return response.json();
    }

    async trackEvent(distinctId: string, eventName: string, properties: any = {}): Promise<any> {
        const eventData = {
            event: eventName,
            properties: {
                token: this.projectToken,
                distinct_id: distinctId,
                time: Math.floor(Date.now() / 1000),
                ...properties,
            },
        };

        return this.makeTrackRequest('/track', [eventData]);
    }

    async updateUserProfile(distinctId: string, properties: any = {}): Promise<any> {
        const profileData = {
            $token: this.projectToken,
            $distinct_id: distinctId,
            $set: properties,
        };

        return this.makeTrackRequest('/engage', [profileData]);
    }

    async incrementUserProperty(distinctId: string, property: string, value: number = 1): Promise<any> {
        const profileData = {
            $token: this.projectToken,
            $distinct_id: distinctId,
            $add: {
                [property]: value,
            },
        };

        return this.makeTrackRequest('/engage', [profileData]);
    }

    async getEvents(eventNames: string[], fromDate: string, toDate: string, unit?: string): Promise<any> {
        const params = new URLSearchParams({
            event: JSON.stringify(eventNames),
            from_date: fromDate,
            to_date: toDate,
            ...(unit && { unit }),
        });

        return this.makeRequest(`/2.0/events?${params}`);
    }

    async getEventProperties(eventName: string, name: string, values?: string[], fromDate?: string, toDate?: string): Promise<any> {
        const params = new URLSearchParams({
            event: eventName,
            name,
            ...(values && { values: JSON.stringify(values) }),
            ...(fromDate && { from_date: fromDate }),
            ...(toDate && { to_date: toDate }),
        });

        return this.makeRequest(`/2.0/events/properties?${params}`);
    }

    async getFunnelData(funnelId: string, fromDate: string, toDate: string, unit?: string): Promise<any> {
        const params = new URLSearchParams({
            funnel_id: funnelId,
            from_date: fromDate,
            to_date: toDate,
            ...(unit && { unit }),
        });

        return this.makeRequest(`/2.0/funnels?${params}`);
    }

    async getRetentionData(fromDate: string, toDate: string, retentionType?: string, bornEvent?: string): Promise<any> {
        const params = new URLSearchParams({
            from_date: fromDate,
            to_date: toDate,
            ...(retentionType && { retention_type: retentionType }),
            ...(bornEvent && { born_event: bornEvent }),
        });

        return this.makeRequest(`/2.0/retention?${params}`);
    }

    async getSegmentationData(event: string, fromDate: string, toDate: string, on?: string, unit?: string): Promise<any> {
        const params = new URLSearchParams({
            event,
            from_date: fromDate,
            to_date: toDate,
            ...(on && { on }),
            ...(unit && { unit }),
        });

        return this.makeRequest(`/2.0/segmentation?${params}`);
    }

    async exportEvents(fromDate: string, toDate: string, event?: string[]): Promise<any> {
        const params = new URLSearchParams({
            from_date: fromDate,
            to_date: toDate,
            ...(event && { event: JSON.stringify(event) }),
        });

        return this.makeRequest(`/2.0/export?${params}`);
    }
}

// Getter function for the client
function getMixpanelClient() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Mixpanel client not found in AsyncLocalStorage');
    }
    return store.mixpanelClient;
}

// Tool definitions
const TRACK_EVENT_TOOL: Tool = {
    name: 'mixpanel_track_event',
    description: 'Track an event in Mixpanel with optional properties.',
    inputSchema: {
        type: 'object',
        properties: {
            distinct_id: {
                type: 'string',
                description: 'Unique identifier for the user performing the event',
            },
            event_name: {
                type: 'string',
                description: 'Name of the event to track',
            },
            properties: {
                type: 'object',
                description: 'Additional properties to include with the event',
                additionalProperties: true,
            },
        },
        required: ['distinct_id', 'event_name'],
    },
};

const UPDATE_USER_PROFILE_TOOL: Tool = {
    name: 'mixpanel_update_user_profile',
    description: 'Update user profile properties in Mixpanel.',
    inputSchema: {
        type: 'object',
        properties: {
            distinct_id: {
                type: 'string',
                description: 'Unique identifier for the user',
            },
            properties: {
                type: 'object',
                description: 'User properties to set or update',
                additionalProperties: true,
            },
        },
        required: ['distinct_id', 'properties'],
    },
};

const INCREMENT_USER_PROPERTY_TOOL: Tool = {
    name: 'mixpanel_increment_user_property',
    description: 'Increment a numerical property in a user profile.',
    inputSchema: {
        type: 'object',
        properties: {
            distinct_id: {
                type: 'string',
                description: 'Unique identifier for the user',
            },
            property: {
                type: 'string',
                description: 'Name of the property to increment',
            },
            value: {
                type: 'number',
                description: 'Value to increment by (default: 1)',
                default: 1,
            },
        },
        required: ['distinct_id', 'property'],
    },
};

const GET_EVENTS_TOOL: Tool = {
    name: 'mixpanel_get_events',
    description: 'Get event data for specific events within a date range.',
    inputSchema: {
        type: 'object',
        properties: {
            event_names: {
                type: 'array',
                items: { type: 'string' },
                description: 'Array of event names to retrieve data for',
            },
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
            unit: {
                type: 'string',
                description: 'Time unit for aggregation (hour, day, week, month)',
                enum: ['hour', 'day', 'week', 'month'],
            },
        },
        required: ['event_names', 'from_date', 'to_date'],
    },
};

const GET_EVENT_PROPERTIES_TOOL: Tool = {
    name: 'mixpanel_get_event_properties',
    description: 'Get property data for a specific event.',
    inputSchema: {
        type: 'object',
        properties: {
            event_name: {
                type: 'string',
                description: 'Name of the event',
            },
            property_name: {
                type: 'string',
                description: 'Name of the property to analyze',
            },
            values: {
                type: 'array',
                items: { type: 'string' },
                description: 'Specific property values to filter by',
            },
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
        },
        required: ['event_name', 'property_name'],
    },
};

const GET_FUNNEL_DATA_TOOL: Tool = {
    name: 'mixpanel_get_funnel_data',
    description: 'Get funnel analysis data for a specific funnel.',
    inputSchema: {
        type: 'object',
        properties: {
            funnel_id: {
                type: 'string',
                description: 'ID of the funnel to analyze',
            },
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
            unit: {
                type: 'string',
                description: 'Time unit for aggregation (day, week, month)',
                enum: ['day', 'week', 'month'],
            },
        },
        required: ['funnel_id', 'from_date', 'to_date'],
    },
};

const GET_RETENTION_DATA_TOOL: Tool = {
    name: 'mixpanel_get_retention_data',
    description: 'Get retention analysis data.',
    inputSchema: {
        type: 'object',
        properties: {
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
            retention_type: {
                type: 'string',
                description: 'Type of retention analysis',
                enum: ['birth', 'compounded'],
            },
            born_event: {
                type: 'string',
                description: 'Event that defines user birth',
            },
        },
        required: ['from_date', 'to_date'],
    },
};

const GET_SEGMENTATION_DATA_TOOL: Tool = {
    name: 'mixpanel_get_segmentation_data',
    description: 'Get segmentation analysis data for an event.',
    inputSchema: {
        type: 'object',
        properties: {
            event: {
                type: 'string',
                description: 'Event name to analyze',
            },
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
            on: {
                type: 'string',
                description: 'Property to segment on',
            },
            unit: {
                type: 'string',
                description: 'Time unit for aggregation (hour, day, week, month)',
                enum: ['hour', 'day', 'week', 'month'],
            },
        },
        required: ['event', 'from_date', 'to_date'],
    },
};

const EXPORT_EVENTS_TOOL: Tool = {
    name: 'mixpanel_export_events',
    description: 'Export raw event data from Mixpanel.',
    inputSchema: {
        type: 'object',
        properties: {
            from_date: {
                type: 'string',
                description: 'Start date in YYYY-MM-DD format',
            },
            to_date: {
                type: 'string',
                description: 'End date in YYYY-MM-DD format',
            },
            events: {
                type: 'array',
                items: { type: 'string' },
                description: 'Specific events to export (optional)',
            },
        },
        required: ['from_date', 'to_date'],
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
const getMixpanelMcpServer = () => {
    const server = new Server(
        {
            name: 'mixpanel-mcp-server',
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
                TRACK_EVENT_TOOL,
                UPDATE_USER_PROFILE_TOOL,
                INCREMENT_USER_PROPERTY_TOOL,
                GET_EVENTS_TOOL,
                GET_EVENT_PROPERTIES_TOOL,
                GET_FUNNEL_DATA_TOOL,
                GET_RETENTION_DATA_TOOL,
                GET_SEGMENTATION_DATA_TOOL,
                EXPORT_EVENTS_TOOL,
            ],
        };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'mixpanel_track_event': {
                    const client = getMixpanelClient();
                    const result = await client.trackEvent(
                        (args as any)?.distinct_id,
                        (args as any)?.event_name,
                        (args as any)?.properties || {}
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_update_user_profile': {
                    const client = getMixpanelClient();
                    const result = await client.updateUserProfile(
                        (args as any)?.distinct_id,
                        (args as any)?.properties
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_increment_user_property': {
                    const client = getMixpanelClient();
                    const result = await client.incrementUserProperty(
                        (args as any)?.distinct_id,
                        (args as any)?.property,
                        (args as any)?.value || 1
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_get_events': {
                    const client = getMixpanelClient();
                    const result = await client.getEvents(
                        (args as any)?.event_names,
                        (args as any)?.from_date,
                        (args as any)?.to_date,
                        (args as any)?.unit
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_get_event_properties': {
                    const client = getMixpanelClient();
                    const result = await client.getEventProperties(
                        (args as any)?.event_name,
                        (args as any)?.property_name,
                        (args as any)?.values,
                        (args as any)?.from_date,
                        (args as any)?.to_date
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_get_funnel_data': {
                    const client = getMixpanelClient();
                    const result = await client.getFunnelData(
                        (args as any)?.funnel_id,
                        (args as any)?.from_date,
                        (args as any)?.to_date,
                        (args as any)?.unit
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_get_retention_data': {
                    const client = getMixpanelClient();
                    const result = await client.getRetentionData(
                        (args as any)?.from_date,
                        (args as any)?.to_date,
                        (args as any)?.retention_type,
                        (args as any)?.born_event
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_get_segmentation_data': {
                    const client = getMixpanelClient();
                    const result = await client.getSegmentationData(
                        (args as any)?.event,
                        (args as any)?.from_date,
                        (args as any)?.to_date,
                        (args as any)?.on,
                        (args as any)?.unit
                    );

                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify(result, null, 2),
                            },
                        ],
                    };
                }

                case 'mixpanel_export_events': {
                    const client = getMixpanelClient();
                    const result = await client.exportEvents(
                        (args as any)?.from_date,
                        (args as any)?.to_date,
                        (args as any)?.events
                    );

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

    const server = getMixpanelMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        const projectToken = process.env.MIXPANEL_PROJECT_TOKEN || req.headers['x-project-token'] as string;
        const username = process.env.MIXPANEL_USERNAME || req.headers['x-username'] as string;
        const secret = process.env.MIXPANEL_SECRET || req.headers['x-secret'] as string;

        if (!projectToken || !username || !secret) {
            console.error('Error: Mixpanel credentials are missing. Provide them via environment variables or headers.');
            res.status(401).json({
                error: 'Mixpanel credentials (project token, username, secret) are required',
            });
            return;
        }

        const mixpanelClient = new MixpanelClient(projectToken, username, secret);

        asyncLocalStorage.run({ mixpanelClient }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

app.listen(5000, () => {
    console.log('Mixpanel MCP server running on port 5000');
});