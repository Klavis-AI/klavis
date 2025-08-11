#!/usr/bin/env node
import express from 'express';
import dotenv from 'dotenv';
import { HttpTransport } from './transport/httpTransport.js';
import { SSETransport } from './transport/sseTransport.js';
import { validateEnvironment } from './utils/validation.js';
import { safeLog } from './client/firefliesClient.js';
import { FirefliesError } from './utils/errors.js';

dotenv.config();

try {
  validateEnvironment();
  safeLog('info', 'Environment variables validated successfully');
} catch (error) {
  safeLog('error', `Environment validation failed: ${error}`);
  process.exit(1);
}

const app = express();
const PORT = process.env.PORT || 5000;

const httpTransport = new HttpTransport();
const sseTransport = new SSETransport();

app.use('/', httpTransport.getRouter());
app.use('/', sseTransport.getRouter());

app.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    service: 'fireflies-mcp-server',
  });
});

app.get('/status', async (_req, res) => {
  try {
    res.json({
      status: 'operational',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      service: 'fireflies-mcp-server',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      environment: {
        node_version: process.version,
        platform: process.platform,
        port: PORT,
      },
      tools: {
        count: 5,
        available: [
          'fireflies_list_meetings',
          'fireflies_get_transcript',
          'fireflies_export_transcript',
          'fireflies_search_meetings',
          'fireflies_get_meeting_summary',
        ],
      },
    });
  } catch (error) {
    safeLog('error', `Status check failed: ${error}`);
    res.status(500).json({
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error instanceof FirefliesError ? error.message : 'Unknown error',
    });
  }
});

app.use((error: any, _req: any, res: any, _next: any) => {
  safeLog('error', `Unhandled error: ${error}`);
  res.status(500).json({
    status: 'error',
    message: 'Internal server error',
    timestamp: new Date().toISOString(),
  });
});

process.on('SIGINT', () => {
  safeLog('info', 'Received SIGINT, shutting down gracefully');
  process.exit(0);
});

process.on('SIGTERM', () => {
  safeLog('info', 'Received SIGTERM, shutting down gracefully');
  process.exit(0);
});

app.listen(PORT, () => {
  safeLog('info', `Fireflies MCP server running on port ${PORT}`);
  safeLog('info', `Health check available at http://localhost:${PORT}/health`);
  safeLog('info', `Status check available at http://localhost:${PORT}/status`);
});
