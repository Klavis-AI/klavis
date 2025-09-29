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

function extractAccessToken(req: Request): string {
    let authData = process.env.AUTH_DATA;
    
    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data JSON:', error);
        }
    }

    if (!authData) {
        console.error('Error: Dropbox access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.access_token ?? '';
}

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
            if (['dropbox_list_folder', 'dropbox_list_folder_continue', 'dropbox_create_folder', 'dropbox_delete_file', 'dropbox_move_file', 'dropbox_copy_file', 'dropbox_search_files', 'dropbox_search_files_continue', 'dropbox_get_file_info'].includes(name)) {
                return await handleFilesOperation(request);
            }

            if (['dropbox_upload_file', 'dropbox_download_file', 'dropbox_get_thumbnail', 'dropbox_list_revisions', 'dropbox_restore_file', 'dropbox_get_temporary_link', 'dropbox_save_url', 'dropbox_save_url_check_job_status'].includes(name)) {
                return await handleFileOperation(request);
            }

            if (['dropbox_add_file_member', 'dropbox_list_file_members', 'dropbox_remove_file_member', 'dropbox_share_folder', 'dropbox_list_folder_members', 'dropbox_add_folder_member', 'dropbox_remove_folder_member', 'dropbox_list_shared_folders', 'dropbox_list_shared_folders_continue', 'dropbox_list_received_files', 'dropbox_check_job_status', 'dropbox_unshare_file', 'dropbox_unshare_folder', 'dropbox_share_file', 'dropbox_get_shared_links'].includes(name)) {
                return await handleSharingOperation(request);
            }

            if (['dropbox_create_file_request', 'dropbox_get_file_request', 'dropbox_list_file_requests', 'dropbox_delete_file_request', 'dropbox_update_file_request'].includes(name)) {
                return await handleFileRequestOperation(request);
            }

            if (['dropbox_batch_delete', 'dropbox_batch_move', 'dropbox_batch_copy', 'dropbox_check_batch_job_status', 'dropbox_lock_file_batch', 'dropbox_unlock_file_batch'].includes(name)) {
                return await handleBatchOperation(request);
            }

            if (['dropbox_get_current_account', 'dropbox_get_space_usage'].includes(name)) {
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
        const accessToken = extractAccessToken(req);

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
        const accessToken = extractAccessToken(req);

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
        const accessToken = extractAccessToken(req);

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
