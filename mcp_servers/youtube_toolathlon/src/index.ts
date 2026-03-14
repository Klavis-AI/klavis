import express, { Request, Response } from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createMcpServer } from './server.js';
import { asyncLocalStorage, extractAuthData } from './auth.js';

const app = express();
app.use(express.json());

app.post('/mcp', async (req: Request, res: Response) => {
    const { authToken: accessToken, authData } = extractAuthData(req);

    const server = createMcpServer();
    try {
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);

        asyncLocalStorage.run({ accessToken, authData }, async () => {
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
});

app.get('/mcp', (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
    }));
});

app.delete('/mcp', (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
    }));
});

const PORT = parseInt(process.env.PORT || '5000', 10);
app.listen(PORT, () => {
    console.log(`YouTube MCP Server running on port ${PORT}`);
    console.log(`  - Streamable HTTP: POST /mcp`);
});
