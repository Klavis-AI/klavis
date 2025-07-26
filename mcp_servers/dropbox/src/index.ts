#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    ListResourceTemplatesRequestSchema,
    ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Dropbox } from 'dropbox';
import dotenv from 'dotenv';

dotenv.config();
const DROPBOX_ACCESS_TOKEN = process.env.DROPBOX_ACCESS_TOKEN;

// Import utilities
import { patchFetchResponse } from './utils/fetch-polyfill.js';
import { formatDropboxError, addCommonErrorGuidance } from './utils/error-handling.js';
import { asyncLocalStorage } from './utils/context.js';

// Import tool definitions
import { toolDefinitions } from './tools.js';

// Import handlers
import {
    handleFilesOperation,
    handleFileOperation,
    handleSharingOperation,
    handleFileRequestOperation,
    handleBatchOperation,
    handleAccountOperation,
    handleReadResource
} from './handlers/index.js';

// Apply the fetch polyfill immediately
patchFetchResponse();

/**
 * Create Dropbox client with access token
 * TODO: Implement OAuth flow instead of using direct access tokens
 * Reference: https://github.com/dropbox/dropbox-sdk-js/tree/main?tab=readme-ov-file#examples
 * Current implementation expects pre-generated access tokens
 */
function createDropboxClient(accessToken: string): Dropbox {
    return new Dropbox({
        fetch: fetch,
        accessToken
    });
}

// Get Dropbox MCP Server
const getDropboxMcpServer = () => {
    // Server implementation
    const server = new Server({
        name: "dropbox",
        version: "1.0.0",
    }, {
        capabilities: {
            tools: {},
            resources: {},
        },
    });

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: toolDefinitions,
    }));

    // Resource handlers
    server.setRequestHandler(ListResourceTemplatesRequestSchema, async () => ({
        resourceTemplates: [
            {
                uriTemplate: 'dropbox://{path}',
                name: 'Dropbox File',
                description: 'Access files from Dropbox storage',
            },
        ],
    }));

    server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
        const uri = request.params.uri;
        return await handleReadResource(uri);
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            // Determine which handler to use based on the tool name
            if (['list_folder', 'list_folder_continue', 'create_folder', 'delete_file', 'move_file', 'copy_file', 'search_files', 'search_files_continue', 'get_file_info'].includes(name)) {
                return await handleFilesOperation(request);
            }

            if (['upload_file', 'download_file', 'get_thumbnail', 'list_revisions', 'restore_file', 'get_temporary_link', 'save_url', 'save_url_check_job_status'].includes(name)) {
                return await handleFileOperation(request);
            }

            if (['add_file_member', 'list_file_members', 'remove_file_member', 'share_folder', 'list_folder_members', 'add_folder_member', 'remove_folder_member', 'list_shared_folders', 'list_shared_folders_continue', 'list_received_files', 'check_job_status', 'unshare_file', 'unshare_folder', 'share_file', 'get_shared_links'].includes(name)) {
                return await handleSharingOperation(request);
            }

            if (['create_file_request', 'get_file_request', 'list_file_requests', 'delete_file_request', 'update_file_request'].includes(name)) {
                return await handleFileRequestOperation(request);
            }

            if (['batch_delete', 'batch_move', 'batch_copy', 'check_batch_job_status', 'lock_file_batch', 'unlock_file_batch'].includes(name)) {
                return await handleBatchOperation(request);
            }

            if (['get_current_account', 'get_space_usage'].includes(name)) {
                return await handleAccountOperation(request);
            }

            // If no handler matches, return error
            return {
                content: [
                    {
                        type: "text",
                        text: `Unknown tool: ${name}. This tool has not been implemented yet.`,
                    },
                ],
            };
        } catch (error: any) {
            console.error(`Error executing tool ${name}:`, error);
            const errorMessage = addCommonErrorGuidance(
                formatDropboxError(error, name, "request"),
                error
            );

            return {
                content: [
                    {
                        type: "text",
                        text: errorMessage,
                    },
                ],
            };
        }
    });

    return server;
};

// Export the server factory for use
export { getDropboxMcpServer };

// If this file is run directly, start the HTTP+SSE server
if (import.meta.url === `file://${process.argv[1]}`) {
    const app = express();
    app.use(express.json());

    //=============================================================================
    // STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
    //=============================================================================
    app.post('/mcp', (req: Request, res: Response) => {
        handleMcpRequest(req, res);
    });

    async function handleMcpRequest(req: Request, res: Response) {
        const accessToken = req.headers['x-auth-token'] || DROPBOX_ACCESS_TOKEN;

        // Initialize Dropbox client only if access token is available
        const dropboxClient = accessToken ? createDropboxClient(accessToken as string) : null;

        const server = getDropboxMcpServer();
        try {
            const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
                sessionIdGenerator: undefined,
            });
            await server.connect(transport);
            asyncLocalStorage.run({ dropboxClient }, async () => {
                await transport.handleRequest(req, res, req.body);
            });
            res.on('close', () => {
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
    }

    app.get('/mcp', async (req: Request, res: Response) => {
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

    // Map to store SSE transports
    const transports = new Map<string, SSEServerTransport>();

    app.get("/sse", (req: Request, res: Response) => {
        handleSseRequest(req, res);
    });

    async function handleSseRequest(req: Request, res: Response) {
        const accessToken = req.headers['x-auth-token'] || DROPBOX_ACCESS_TOKEN;

        const transport = new SSEServerTransport(`/messages`, res);

        // Set up cleanup when connection closes
        res.on('close', async () => {
            try {
                transports.delete(transport.sessionId);
            } finally {
            }
        });

        transports.set(transport.sessionId, transport);

        const server = getDropboxMcpServer();
        await server.connect(transport);

        console.log(`SSE connection established with transport: ${transport.sessionId}`);
    }

    app.post("/messages", (req: Request, res: Response) => {
        handleMessagesRequest(req, res);
    });

    async function handleMessagesRequest(req: Request, res: Response) {
        const sessionId = req.query.sessionId as string;
        const accessToken = req.headers['x-auth-token'] || DROPBOX_ACCESS_TOKEN;

        let transport: SSEServerTransport | undefined;
        transport = sessionId ? transports.get(sessionId) : undefined;
        if (transport) {
            // Initialize Dropbox client only if access token is available
            const dropboxClient = accessToken ? createDropboxClient(accessToken as string) : null;

            asyncLocalStorage.run({ dropboxClient }, async () => {
                await transport!.handlePostMessage(req, res);
            });
        } else {
            console.error(`Transport not found for session ID: ${sessionId}`);
            res.status(404).send({ error: "Transport not found" });
        }
    }

    // Start the server
    const PORT = process.env.PORT || 5000;
    app.listen(PORT, () => {
        console.log(`Dropbox MCP server running on port ${PORT}`);
    });
}
