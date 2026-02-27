#!/usr/bin/env node
import express, { Request, Response } from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMcpServer, startMcpServer } from './server.js';
import { asyncLocalStorage, extractAuthData } from './services/base.js';

//=============================================================================
// HTTP SERVER SETUP
//=============================================================================

const app = express();

app.post('/mcp', async (req: Request, res: Response) => {
    const auth = extractAuthData(req);
    const server = createMcpServer();

    try {
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);

        asyncLocalStorage.run(auth, async () => {
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
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed." },
        id: null
    }));
});

//=============================================================================
// MAIN ENTRY POINT
//=============================================================================

const PORT = parseInt(process.env.PORT || '5000', 10);
const TRANSPORT = process.env.TRANSPORT || 'http';

if (TRANSPORT === 'stdio') {
    const requiredEnvVars = [
        'WORDPRESS_SITE_URL',
        'WOOCOMMERCE_CONSUMER_KEY',
        'WOOCOMMERCE_CONSUMER_SECRET'
    ];
    const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);
    if (missingEnvVars.length > 0) {
        console.error('Error: Missing required environment variables:');
        missingEnvVars.forEach(envVar => console.error(`  - ${envVar}`));
        process.exit(1);
    }

    startMcpServer()
        .then(() => console.log('WooCommerce MCP Server started on stdio'))
        .catch(error => {
            console.error('Failed to start WooCommerce MCP Server:', error);
            process.exit(1);
        });
} else {
    app.listen(PORT, () => {
        console.log(`WooCommerce MCP server running on port ${PORT}`);
        console.log(`  - Streamable HTTP: POST /mcp`);
    });
}
