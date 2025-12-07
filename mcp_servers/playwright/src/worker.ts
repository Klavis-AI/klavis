#!/usr/bin/env node
/**
 * Playwright MCP Worker Process
 *
 * This runs as an isolated child process with its own HTTP server.
 * Each worker has its own browser process for complete isolation.
 */

import express, { Request, Response } from 'express';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { createConnection } from '@playwright/mcp';

// Use inferred type from createConnection to avoid ESM/CJS type conflicts
type PlaywrightServer = Awaited<ReturnType<typeof createConnection>>;

// Configuration from environment (passed from main process)
const HEADLESS = process.env.HEADLESS !== 'false';
const INSTANCE_ID = process.env.INSTANCE_ID || 'default';
const WORKER_PORT = parseInt(process.env.WORKER_PORT || '0', 10); // 0 = auto-assign

// Express app for this worker
const app = express();
app.use(express.json({ limit: '50mb' }));

/**
 * Create a new Playwright MCP connection
 */
async function createPlaywrightConnection(): Promise<PlaywrightServer> {
    return await createConnection({
        browser: {
            launchOptions: {
                headless: HEADLESS,
            },
        },
    });
}

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PRIMARY)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    console.log(`[Worker ${INSTANCE_ID}] POST /mcp`);

    try {
        const connection = await createPlaywrightConnection();

        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });

        await connection.connect(transport);
        await transport.handleRequest(req, res, req.body);

        res.on('close', () => {
            console.log(`[Worker ${INSTANCE_ID}] StreamableHTTP request closed`);
            transport.close();
            connection.close();
        });
    } catch (error) {
        console.error(`[Worker ${INSTANCE_ID}] Error handling MCP request:`, error);
        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: '2.0',
                error: { code: -32603, message: 'Internal server error' },
                id: null,
            });
        }
    }
});

app.get('/mcp', (req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
    }));
});

app.delete('/mcp', (req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: { code: -32000, message: 'Method not allowed.' },
        id: null,
    }));
});

//=============================================================================
// SSE TRANSPORT (DEPRECATED)
//=============================================================================

interface SSESession {
    transport: SSEServerTransport;
    connection: PlaywrightServer;
}
const sessions = new Map<string, SSESession>();

app.get('/sse', async (req: Request, res: Response) => {
    console.log(`[Worker ${INSTANCE_ID}] GET /sse`);

    try {
        const transport = new SSEServerTransport('/messages', res);
        const connection = await createPlaywrightConnection();

        sessions.set(transport.sessionId, { transport, connection });

        res.on('close', () => {
            console.log(`[Worker ${INSTANCE_ID}] SSE connection closed: ${transport.sessionId}`);
            const session = sessions.get(transport.sessionId);
            if (session) {
                session.connection.close();
                sessions.delete(transport.sessionId);
            }
        });

        await connection.connect(transport);
        console.log(`[Worker ${INSTANCE_ID}] SSE session established: ${transport.sessionId}`);
    } catch (error) {
        console.error(`[Worker ${INSTANCE_ID}] Error establishing SSE:`, error);
        if (!res.headersSent) {
            res.status(500).json({ error: 'Failed to establish SSE connection' });
        }
    }
});

app.post('/messages', async (req: Request, res: Response) => {
    const sessionId = req.query.sessionId as string;
    console.log(`[Worker ${INSTANCE_ID}] POST /messages: ${sessionId}`);

    const session = sessionId ? sessions.get(sessionId) : undefined;

    if (session) {
        try {
            await session.transport.handlePostMessage(req, res);
        } catch (error) {
            console.error(`[Worker ${INSTANCE_ID}] Error handling message:`, error);
            if (!res.headersSent) {
                res.status(500).json({ error: 'Failed to handle message' });
            }
        }
    } else {
        res.status(404).json({ error: 'Session not found' });
    }
});

//=============================================================================
// HEALTH CHECK
//=============================================================================

app.get('/health', (req: Request, res: Response) => {
    res.json({
        status: 'ok',
        instanceId: INSTANCE_ID,
        sessions: sessions.size,
    });
});

//=============================================================================
// START WORKER SERVER
//=============================================================================

const server = app.listen(WORKER_PORT, '127.0.0.1', () => {
    const addr = server.address();
    const port = typeof addr === 'object' && addr ? addr.port : WORKER_PORT;

    console.log(`[Worker ${INSTANCE_ID}] Started on port ${port}`);

    // Notify main process of our port
    if (process.send) {
        process.send({ type: 'ready', port, instanceId: INSTANCE_ID });
    }
});

// Graceful shutdown
async function shutdown() {
    console.log(`[Worker ${INSTANCE_ID}] Shutting down...`);

    // Close all SSE sessions
    for (const [sessionId, session] of sessions) {
        try {
            await session.connection.close();
        } catch (e) {
            // Ignore
        }
    }
    sessions.clear();

    server.close(() => {
        console.log(`[Worker ${INSTANCE_ID}] Shutdown complete`);
        process.exit(0);
    });

    // Force exit after timeout
    setTimeout(() => process.exit(1), 5000);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
process.on('message', (msg: any) => {
    if (msg.type === 'shutdown') {
        shutdown();
    }
});
