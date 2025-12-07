#!/usr/bin/env node
/**
 * Playwright MCP Router (Main Process)
 *
 * Routes requests to isolated worker processes based on x-instance-id header.
 * Each worker has its own browser process for complete security isolation.
 */

import express, { Request, Response } from 'express';
import { fork, ChildProcess } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

// ES module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const PORT = parseInt(process.env.PORT || '5000', 10);
const HEADLESS = process.env.HEADLESS !== 'false';
const WORKER_IDLE_TIMEOUT = parseInt(process.env.WORKER_IDLE_TIMEOUT || '3600000', 10); // 1 hour default

// Worker info
interface WorkerInfo {
    process: ChildProcess;
    port: number;
    instanceId: string;
    lastActivity: number;
    ready: boolean;
}

const workers = new Map<string, WorkerInfo>();
const pendingWorkers = new Map<string, Promise<WorkerInfo>>();

// Express app
const app = express();
app.use(express.json({ limit: '50mb' }));

/**
 * Get or create a worker for the given instance ID
 */
async function getOrCreateWorker(instanceId: string): Promise<WorkerInfo> {
    // Return existing ready worker
    const existing = workers.get(instanceId);
    if (existing?.ready) {
        existing.lastActivity = Date.now();
        return existing;
    }

    // Return pending worker creation
    const pending = pendingWorkers.get(instanceId);
    if (pending) {
        return pending;
    }

    // Create new worker
    const workerPromise = createWorker(instanceId);
    pendingWorkers.set(instanceId, workerPromise);

    try {
        const worker = await workerPromise;
        pendingWorkers.delete(instanceId);
        return worker;
    } catch (error) {
        pendingWorkers.delete(instanceId);
        throw error;
    }
}

/**
 * Spawn a new worker process
 */
function createWorker(instanceId: string): Promise<WorkerInfo> {
    return new Promise((resolve, reject) => {
        console.log(`[Router] Spawning worker for instance: ${instanceId}`);

        const workerPath = path.join(__dirname, 'worker.js');

        const child = fork(workerPath, [], {
            env: {
                ...process.env,
                INSTANCE_ID: instanceId,
                HEADLESS: String(HEADLESS),
                WORKER_PORT: '0', // Auto-assign port
            },
            stdio: ['pipe', 'pipe', 'pipe', 'ipc'],
        });

        // Forward worker stdout/stderr
        child.stdout?.on('data', (data) => {
            process.stdout.write(data);
        });
        child.stderr?.on('data', (data) => {
            process.stderr.write(data);
        });

        const timeout = setTimeout(() => {
            child.kill();
            reject(new Error(`Worker ${instanceId} startup timeout`));
        }, 30000);

        child.on('message', (msg: any) => {
            if (msg.type === 'ready' && msg.port) {
                clearTimeout(timeout);

                const workerInfo: WorkerInfo = {
                    process: child,
                    port: msg.port,
                    instanceId,
                    lastActivity: Date.now(),
                    ready: true,
                };

                workers.set(instanceId, workerInfo);
                console.log(`[Router] Worker ${instanceId} ready on port ${msg.port}`);
                resolve(workerInfo);
            }
        });

        child.on('error', (error) => {
            clearTimeout(timeout);
            workers.delete(instanceId);
            console.error(`[Router] Worker ${instanceId} error:`, error);
            reject(error);
        });

        child.on('exit', (code) => {
            clearTimeout(timeout);
            workers.delete(instanceId);
            console.log(`[Router] Worker ${instanceId} exited with code ${code}`);
        });
    });
}

/**
 * Kill a worker process
 */
async function killWorker(instanceId: string): Promise<void> {
    const worker = workers.get(instanceId);
    if (!worker) return;

    console.log(`[Router] Killing worker: ${instanceId}`);

    try {
        worker.process.send({ type: 'shutdown' });

        // Wait for graceful shutdown, then force kill
        await new Promise<void>((resolve) => {
            const forceKillTimeout = setTimeout(() => {
                worker.process.kill('SIGKILL');
                resolve();
            }, 5000);

            worker.process.on('exit', () => {
                clearTimeout(forceKillTimeout);
                resolve();
            });
        });
    } catch (error) {
        console.error(`[Router] Error killing worker ${instanceId}:`, error);
        worker.process.kill('SIGKILL');
    }

    workers.delete(instanceId);
}

/**
 * Idle timeout cleanup
 */
setInterval(() => {
    const now = Date.now();
    for (const [instanceId, worker] of workers) {
        if (now - worker.lastActivity > WORKER_IDLE_TIMEOUT) {
            console.log(`[Router] Worker ${instanceId} idle timeout, killing...`);
            killWorker(instanceId);
        }
    }
}, 60000); // Check every minute

/**
 * Extract instance ID from request
 */
function getInstanceId(req: Request): string {
    return (req.headers['x-instance-id'] as string) || 'default';
}

/**
 * Proxy request to worker
 */
async function proxyToWorker(
    req: Request,
    res: Response,
    targetPath: string
): Promise<void> {
    const instanceId = getInstanceId(req);

    try {
        const worker = await getOrCreateWorker(instanceId);

        // Manual proxy using fetch (simpler than http-proxy-middleware for our use case)
        const targetUrl = `http://127.0.0.1:${worker.port}${targetPath}`;

        const headers: Record<string, string> = {};
        for (const [key, value] of Object.entries(req.headers)) {
            if (typeof value === 'string') {
                headers[key] = value;
            } else if (Array.isArray(value)) {
                headers[key] = value.join(', ');
            }
        }
        // Remove host header to avoid issues
        delete headers['host'];

        const fetchOptions: RequestInit = {
            method: req.method,
            headers,
        };

        // Add body for non-GET requests
        if (req.method !== 'GET' && req.method !== 'HEAD') {
            fetchOptions.body = JSON.stringify(req.body);
        }

        const response = await fetch(targetUrl, fetchOptions);

        // Copy response status and headers
        res.status(response.status);
        response.headers.forEach((value, key) => {
            // Skip certain headers that shouldn't be forwarded
            if (!['transfer-encoding', 'connection'].includes(key.toLowerCase())) {
                res.setHeader(key, value);
            }
        });

        // Stream response body
        if (response.body) {
            const reader = response.body.getReader();
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    res.write(value);
                }
            } finally {
                reader.releaseLock();
            }
        }

        res.end();
    } catch (error: any) {
        console.error(`[Router] Proxy error for ${instanceId}:`, error);

        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: '2.0',
                error: { code: -32603, message: 'Internal server error' },
                id: null,
            });
        }
    }
}

/**
 * Proxy SSE connection to worker
 */
async function proxySSEToWorker(req: Request, res: Response): Promise<void> {
    const instanceId = getInstanceId(req);

    try {
        const worker = await getOrCreateWorker(instanceId);
        const targetUrl = `http://127.0.0.1:${worker.port}/sse`;

        // For SSE, we need to pipe the response
        const response = await fetch(targetUrl, {
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream',
            },
        });

        if (!response.ok || !response.body) {
            throw new Error(`Worker SSE error: ${response.status}`);
        }

        // Set SSE headers
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.flushHeaders();

        // Pipe the SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        req.on('close', () => {
            reader.cancel();
        });

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                res.write(decoder.decode(value, { stream: true }));
            }
        } catch (e) {
            // Connection closed
        } finally {
            reader.releaseLock();
            res.end();
        }
    } catch (error: any) {
        console.error(`[Router] SSE proxy error for ${instanceId}:`, error);

        if (!res.headersSent) {
            res.status(500).json({ error: 'Failed to establish SSE connection' });
        }
    }
}

//=============================================================================
// ROUTES
//=============================================================================

// Health check
app.get('/', (req: Request, res: Response) => {
    const workerInfo = Array.from(workers.entries()).map(([id, w]) => ({
        instanceId: id,
        port: w.port,
        ready: w.ready,
        idleSeconds: Math.floor((Date.now() - w.lastActivity) / 1000),
    }));

    res.json({
        status: 'ok',
        server: 'playwright-mcp-router',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        workers: workerInfo,
        config: {
            idleTimeoutMs: WORKER_IDLE_TIMEOUT,
            headless: HEADLESS,
        },
    });
});

// StreamableHTTP transport
app.post('/mcp', (req, res) => proxyToWorker(req, res, '/mcp'));
app.get('/mcp', (req, res) => proxyToWorker(req, res, '/mcp'));
app.delete('/mcp', (req, res) => proxyToWorker(req, res, '/mcp'));

// SSE transport
app.get('/sse', (req, res) => proxySSEToWorker(req, res));
app.post('/messages', (req, res) => {
    // For /messages, we need to route to the correct worker
    // The sessionId comes from the worker, so we need to track which worker owns which session
    // For simplicity, we'll pass through the x-instance-id header
    proxyToWorker(req, res, `/messages?${new URLSearchParams(req.query as any).toString()}`);
});

//=============================================================================
// STARTUP & SHUTDOWN
//=============================================================================

const server = app.listen(PORT, () => {
    console.log(`Playwright MCP Router starting on port ${PORT}`);
    console.log(`  - Config: headless=${HEADLESS}, idleTimeout=${WORKER_IDLE_TIMEOUT}ms`);
    console.log(`  - POST /mcp (StreamableHTTP)`);
    console.log(`  - GET /sse, POST /messages (SSE)`);
    console.log(`  - x-instance-id header: optional (default: "default")`);
});

// Graceful shutdown
async function shutdown() {
    console.log('[Router] Shutting down...');

    // Kill all workers
    const killPromises = Array.from(workers.keys()).map((id) => killWorker(id));
    await Promise.all(killPromises);

    server.close(() => {
        console.log('[Router] Shutdown complete');
        process.exit(0);
    });

    // Force exit after timeout
    setTimeout(() => process.exit(1), 10000);
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
