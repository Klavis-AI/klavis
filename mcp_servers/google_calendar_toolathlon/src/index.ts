#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import express, { Request, Response } from 'express';
import { google } from 'googleapis';
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { AsyncLocalStorage } from 'async_hooks';

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    calendar: any;
}>();

function getCalendar() {
    return asyncLocalStorage.getStore()!.calendar;
}

const GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token";

interface AuthInfo {
    access_token: string;
    client_id?: string;
    client_secret?: string;
    refresh_token?: string;
}

function extractAuthInfo(req: Request): AuthInfo {
    // First try environment variable
    let authData = process.env.AUTH_DATA;

    // If not in env, try to get from x-auth-data header
    if (!authData) {
        const headerValue = req.headers["x-auth-data"];
        if (headerValue) {
            try {
                // Header value is base64 encoded JSON
                authData = Buffer.from(headerValue as string, "base64").toString("utf8");
            } catch (error) {
                console.error("Error decoding x-auth-data header:", error);
            }
        }
    }

    if (!authData) {
        // No auth data available - this is normal for initialization requests
        return { access_token: "" };
    }

    try {
        // Parse the JSON auth data to extract auth fields
        const authJson = JSON.parse(authData);
        return {
            access_token: authJson.access_token ?? "",
            client_id: authJson.client_id,
            client_secret: authJson.client_secret,
            refresh_token: authJson.refresh_token,
        };
    } catch (error) {
        console.error("Failed to parse auth data JSON:", authData);
        return { access_token: "" };
    }
}

// Schema definitions
const CreateEventSchema = z.object({
    summary: z.string().describe("Event title"),
    start: z.object({
        dateTime: z.string().describe("Start time (ISO format)"),
        timeZone: z.string().optional().describe("Time zone"),
    }),
    end: z.object({
        dateTime: z.string().describe("End time (ISO format)"),
        timeZone: z.string().optional().describe("Time zone"),
    }),
    description: z.string().optional().describe("Event description"),
    location: z.string().optional().describe("Event location"),
});

const GetEventSchema = z.object({
    eventId: z.string().describe("ID of the event to retrieve"),
});

const UpdateEventSchema = z.object({
    eventId: z.string().describe("ID of the event to update"),
    summary: z.string().optional().describe("New event title"),
    start: z.object({
        dateTime: z.string().describe("New start time (ISO format)"),
        timeZone: z.string().optional().describe("Time zone"),
    }).optional(),
    end: z.object({
        dateTime: z.string().describe("New end time (ISO format)"),
        timeZone: z.string().optional().describe("Time zone"),
    }).optional(),
    description: z.string().optional().describe("New event description"),
    location: z.string().optional().describe("New event location"),
});

const DeleteEventSchema = z.object({
    eventId: z.string().describe("ID of the event to delete"),
});

const ListEventsSchema = z.object({
    timeMin: z.string().describe("Start of time range (ISO format)"),
    timeMax: z.string().describe("End of time range (ISO format)"),
    maxResults: z.number().optional().describe("Maximum number of events to return"),
    orderBy: z.enum(['startTime', 'updated']).optional().describe("Sort order"),
});

// Get Google Calendar MCP Server
const getGoogleCalendarMcpServer = () => {
    const calendarId = 'primary';

    const server = new Server(
        {
            name: "google-calendar",
            version: "1.0.0",
        },
        {
            capabilities: {
                tools: {},
            },
        },
    );

    server.onerror = (error) => console.error("[MCP Error]", error);

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            {
                name: "create_event",
                description: "Creates a new event in Google Calendar",
                inputSchema: zodToJsonSchema(CreateEventSchema),
            },
            {
                name: "get_event",
                description: "Retrieves details of a specific event",
                inputSchema: zodToJsonSchema(GetEventSchema),
            },
            {
                name: "update_event",
                description: "Updates an existing event",
                inputSchema: zodToJsonSchema(UpdateEventSchema),
            },
            {
                name: "delete_event",
                description: "Deletes an event from the calendar",
                inputSchema: zodToJsonSchema(DeleteEventSchema),
            },
            {
                name: "list_events",
                description: "Lists events within a specified time range",
                inputSchema: zodToJsonSchema(ListEventsSchema),
            },
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        const calendar = getCalendar();

        try {
            switch (name) {
                case "create_event": {
                    const validatedArgs = CreateEventSchema.parse(args);
                    const response = await calendar.events.insert({
                        calendarId,
                        requestBody: validatedArgs,
                    });
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Event created with ID: ${response.data.id}\n` +
                                      `Title: ${validatedArgs.summary}\n` +
                                      `Start: ${validatedArgs.start.dateTime}\n` +
                                      `End: ${validatedArgs.end.dateTime}`,
                            },
                        ],
                    };
                }

                case "get_event": {
                    const validatedArgs = GetEventSchema.parse(args);
                    const response = await calendar.events.get({
                        calendarId,
                        eventId: validatedArgs.eventId,
                    });
                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(response.data, null, 2),
                            },
                        ],
                    };
                }

                case "update_event": {
                    const validatedArgs = UpdateEventSchema.parse(args);
                    const { eventId, ...updates } = validatedArgs;
                    const response = await calendar.events.patch({
                        calendarId,
                        eventId,
                        requestBody: updates,
                    });
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Event updated: ${eventId}\n` +
                                      `New title: ${updates.summary || '(unchanged)'}\n` +
                                      `New start: ${updates.start?.dateTime || '(unchanged)'}\n` +
                                      `New end: ${updates.end?.dateTime || '(unchanged)'}`,
                            },
                        ],
                    };
                }

                case "delete_event": {
                    const validatedArgs = DeleteEventSchema.parse(args);
                    await calendar.events.delete({
                        calendarId,
                        eventId: validatedArgs.eventId,
                    });
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Event deleted: ${validatedArgs.eventId}`,
                            },
                        ],
                    };
                }

                case "list_events": {
                    const validatedArgs = ListEventsSchema.parse(args);
                    const response = await calendar.events.list({
                        calendarId,
                        timeMin: validatedArgs.timeMin,
                        timeMax: validatedArgs.timeMax,
                        maxResults: validatedArgs.maxResults || 10,
                        orderBy: validatedArgs.orderBy || 'startTime',
                        singleEvents: true,
                    });
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Found ${response.data.items?.length || 0} events:\n` +
                                      JSON.stringify(response.data.items, null, 2),
                            },
                        ],
                    };
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    });

    return server;
};

// Create Express App
const app = express();
app.use(express.json());

app.post("/mcp", async (req: Request, res: Response) => {
    const authInfo = extractAuthInfo(req);

    // Initialize Calendar client with the access token and refresh credentials
    const auth = new google.auth.OAuth2(authInfo.client_id, authInfo.client_secret);
    auth.setCredentials({
        access_token: authInfo.access_token,
        refresh_token: authInfo.refresh_token,
        token_type: "Bearer",
    });
    const calendarClient = google.calendar({ version: 'v3', auth });

    const server = getGoogleCalendarMcpServer();
    try {
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ calendar: calendarClient }, async () => {
            await transport.handleRequest(req, res, req.body);
        });
        res.on("close", () => {
            transport.close();
            server.close();
        });
    } catch (error) {
        console.error("Error handling MCP request:", error);
        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: "2.0",
                error: {
                    code: -32603,
                    message: "Internal server error",
                },
                id: null,
            });
        }
    }
});

app.get("/mcp", async (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null,
    }));
});

app.delete("/mcp", async (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null,
    }));
});

app.get("/health", (_req: Request, res: Response) => {
    res.json({ status: "ok" });
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Google Calendar MCP server running on port ${PORT}`);
});
