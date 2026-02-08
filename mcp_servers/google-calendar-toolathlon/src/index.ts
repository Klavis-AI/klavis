#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from 'googleapis';
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { OAuth2Client } from 'google-auth-library';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import open from 'open';
import os from 'os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Configuration paths
const CONFIG_DIR = path.join(os.homedir(), '.calendar-mcp');
const OAUTH_PATH = process.env.CALENDAR_OAUTH_PATH || path.join(CONFIG_DIR, 'gcp-oauth.keys.json');
const CREDENTIALS_PATH = process.env.CALENDAR_CREDENTIALS_PATH || path.join(CONFIG_DIR, 'credentials.json');

// OAuth2 configuration
let oauth2Client: OAuth2Client;

async function loadCredentials() {
    try {
        // Create config directory if it doesn't exist
        if (!fs.existsSync(CONFIG_DIR)) {
            fs.mkdirSync(CONFIG_DIR, { recursive: true });
        }

        // Check for OAuth keys in current directory first, then in config directory
        const localOAuthPath = path.join(process.cwd(), 'gcp-oauth.keys.json');
        let oauthPath = OAUTH_PATH;
        
        if (fs.existsSync(localOAuthPath)) {
            // If found in current directory, copy to config directory
            fs.copyFileSync(localOAuthPath, OAUTH_PATH);
            console.log('OAuth keys found in current directory, copied to global config.');
        }

        if (!fs.existsSync(OAUTH_PATH)) {
            console.error('Error: OAuth keys file not found. Please place gcp-oauth.keys.json in current directory or', CONFIG_DIR);
            process.exit(1);
        }

        const keysContent = JSON.parse(fs.readFileSync(OAUTH_PATH, 'utf8'));
        const keys = keysContent.installed || keysContent.web;
        
        if (!keys) {
            console.error('Error: Invalid OAuth keys file format. File should contain either "installed" or "web" credentials.');
            process.exit(1);
        }

        oauth2Client = new OAuth2Client(
            keys.client_id,
            keys.client_secret,
            'http://localhost:3000/oauth2callback'
        );

        if (fs.existsSync(CREDENTIALS_PATH)) {
            const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
            oauth2Client.setCredentials(credentials);
        }
    } catch (error) {
        console.error('Error loading credentials:', error);
        process.exit(1);
    }
}

async function authenticate() {
    const server = http.createServer();
    server.listen(3000);

    return new Promise<void>((resolve, reject) => {
        const authUrl = oauth2Client.generateAuthUrl({
            access_type: 'offline',
            scope: ['https://www.googleapis.com/auth/calendar'],
        });

        console.log('Please visit this URL to authenticate:', authUrl);
        open(authUrl);

        server.on('request', async (req, res) => {
            if (!req.url?.startsWith('/oauth2callback')) return;

            const url = new URL(req.url, 'http://localhost:3000');
            const code = url.searchParams.get('code');

            if (!code) {
                res.writeHead(400);
                res.end('No code provided');
                reject(new Error('No code provided'));
                return;
            }

            try {
                const { tokens } = await oauth2Client.getToken(code);
                oauth2Client.setCredentials(tokens);
                fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(tokens));

                res.writeHead(200);
                res.end('Authentication successful! You can close this window.');
                server.close();
                resolve();
            } catch (error) {
                res.writeHead(500);
                res.end('Authentication failed');
                reject(error);
            }
        });
    });
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

// Main function
async function main() {
    await loadCredentials();

    if (process.argv[2] === 'auth') {
        await authenticate();
        console.log('Authentication completed successfully');
        process.exit(0);
    }

    // Initialize Google Calendar API
    const calendar = google.calendar({ version: 'v3', auth: oauth2Client });
    const calendarId = 'primary';

    // Server implementation
    const server = new Server({
        name: "google-calendar",
        version: "1.0.0",
        capabilities: {
            tools: {},
        },
    });

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

    // Start the server
    const transport = new StdioServerTransport();
    server.connect(transport).catch((error) => {
        console.error("Fatal error running server:", error);
        process.exit(1);
    });
    console.error('Google Calendar MCP Server running on stdio');
}

main().catch(console.error);