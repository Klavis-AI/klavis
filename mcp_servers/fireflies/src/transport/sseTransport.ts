import express, { Request, Response, Router } from 'express';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { FirefliesClient, asyncLocalStorage } from '../client/firefliesClient.js';
import { ValidationUtils } from '../utils/validation.js';
import { getFirefliesMcpServer } from '../server.js';
import { safeLog } from '../client/firefliesClient.js';

export class SSETransport {
  private router: Router;
  private transports = new Map<string, SSEServerTransport>();

  constructor() {
    this.router = express.Router();
    this.setupRoutes();
  }

  private setupRoutes(): void {
    this.router.get('/sse', this.handleSseConnection.bind(this));
    this.router.post('/messages', this.handleMessages.bind(this));
    this.router.delete('/sse/:sessionId', this.handleDeleteSession.bind(this));
    this.router.get('/sse/status', this.handleStatus.bind(this));
  }

  private async handleSseConnection(req: Request, res: Response): Promise<void> {
    try {
      const accessToken = process.env.FIREFLIES_API_KEY || (req.headers['x-auth-token'] as string);

      if (!accessToken) {
        safeLog('error', 'Missing Fireflies API key in SSE connection request');
        res.status(401).json({ error: 'Missing Fireflies API key' });
        return;
      }

      if (!ValidationUtils.validateApiKey(accessToken)) {
        safeLog('error', 'Invalid Fireflies API key format in SSE connection');
        res.status(401).json({ error: 'Invalid API key format' });
        return;
      }

      const firefliesClient = new FirefliesClient(accessToken);
      const connectionTest = await firefliesClient.testConnection();
      if (!connectionTest) {
        safeLog('error', 'Failed to connect to Fireflies API during SSE setup');
        res.status(401).json({ error: 'Invalid API credentials or connection failed' });
        return;
      }

      const transport = new SSEServerTransport('/messages', res);

      res.on('close', async () => {
        safeLog('info', `SSE connection closed for session: ${transport.sessionId}`);
        try {
          this.transports.delete(transport.sessionId);
          await transport.close();
        } catch (error) {
          safeLog('error', `Error during SSE cleanup: ${error}`);
        }
      });

      res.on('error', (error) => {
        safeLog('error', `SSE connection error for session ${transport.sessionId}: ${error}`);
        this.transports.delete(transport.sessionId);
      });

      this.transports.set(transport.sessionId, transport);

      const server = getFirefliesMcpServer();
      await server.connect(transport);

      safeLog('info', `SSE connection established with session: ${transport.sessionId}`);
    } catch (error) {
      safeLog('error', `Error establishing SSE connection: ${error}`);
      if (!res.headersSent) {
        res.status(500).json({ error: 'Failed to establish SSE connection' });
      }
    }
  }

  private async handleMessages(req: Request, res: Response): Promise<void> {
    try {
      const sessionId = req.query.sessionId as string;

      if (!sessionId) {
        safeLog('error', 'Missing sessionId parameter in messages request');
        res.status(400).json({ error: 'Missing sessionId parameter' });
        return;
      }

      const transport = this.transports.get(sessionId);
      if (!transport) {
        safeLog('error', `Transport not found for session: ${sessionId}`);
        res.status(404).json({ error: 'Transport not found or session expired' });
        return;
      }

      const accessToken = process.env.FIREFLIES_API_KEY || (req.headers['x-auth-token'] as string);

      if (!accessToken || !ValidationUtils.validateApiKey(accessToken)) {
        safeLog('error', `Invalid or missing access token for session: ${sessionId}`);
        res.status(401).json({ error: 'Invalid or missing access token' });
        return;
      }

      const firefliesClient = new FirefliesClient(accessToken);

      safeLog('info', `Processing message for session: ${sessionId}`);

      await asyncLocalStorage.run({ firefliesClient }, async () => {
        await transport.handlePostMessage(req, res);
      });
    } catch (error: any) {
      safeLog('error', `Error handling message: ${error}`);
      if (!res.headersSent) {
        res.status(500).json({ error: `Message handling failed: ${error.message}` });
      }
    }
  }

  private async handleDeleteSession(req: Request, res: Response): Promise<void> {
    const sessionId = req.params.sessionId;
    const transport = this.transports.get(sessionId);

    if (transport) {
      try {
        await transport.close();
        this.transports.delete(sessionId);
        safeLog('info', `Session terminated: ${sessionId}`);
        res.status(200).json({ message: 'Session terminated' });
      } catch (error) {
        safeLog('error', `Failed to terminate session ${sessionId}: ${error}`);
        res.status(500).json({ error: 'Failed to terminate session' });
      }
    } else {
      safeLog('warning', `Attempted to delete non-existent session: ${sessionId}`);
      res.status(404).json({ error: 'Session not found' });
    }
  }

  private handleStatus(_req: Request, res: Response): void {
    const status = {
      service: 'fireflies-mcp-server',
      transport: 'sse',
      activeConnections: this.transports.size,
      sessions: Array.from(this.transports.keys()),
      timestamp: new Date().toISOString(),
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
    };

    safeLog('info', `SSE status requested - ${status.activeConnections} active connections`);
    res.json(status);
  }

  /**
   * Get number of active SSE connections
   */
  getActiveConnectionCount(): number {
    return this.transports.size;
  }

  /**
   * Get list of active session IDs
   */
  getActiveSessions(): string[] {
    return Array.from(this.transports.keys());
  }

  /**
   * Manually close a specific session
   */
  async closeSession(sessionId: string): Promise<boolean> {
    const transport = this.transports.get(sessionId);
    if (transport) {
      try {
        await transport.close();
        this.transports.delete(sessionId);
        safeLog('info', `Manually closed session: ${sessionId}`);
        return true;
      } catch (error) {
        safeLog('error', `Failed to manually close session ${sessionId}: ${error}`);
        return false;
      }
    }
    return false;
  }

  /**
   * Close all active sessions
   */
  async closeAllSessions(): Promise<void> {
    const sessions = Array.from(this.transports.keys());
    safeLog('info', `Closing ${sessions.length} active SSE sessions`);

    await Promise.all(
      sessions.map(async (sessionId) => {
        await this.closeSession(sessionId);
      }),
    );
  }

  getRouter(): Router {
    return this.router;
  }
}
