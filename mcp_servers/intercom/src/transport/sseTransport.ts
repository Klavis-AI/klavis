import express, { Request, Response, Router } from 'express';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { IntercomClient, asyncLocalStorage } from '../client/intercomClient.js';
import { validateIntercomToken } from '../utils/validation.js';
import { getIntercomMcpServer } from '../server.js';

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
      const accessToken =
        process.env.INTERCOM_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

      if (!accessToken) {
        res.status(401).json({ error: 'Missing Intercom access token' });
        return;
      }

      const transport = new SSEServerTransport('/messages', res);

      res.on('close', async () => {
        console.log(`SSE connection closed for session: ${transport.sessionId}`);
        try {
          this.transports.delete(transport.sessionId);
          await transport.close();
        } catch (error) {
          console.error('Error during SSE cleanup:', error);
        }
      });

      res.on('error', (error) => {
        console.error(`SSE connection error for session ${transport.sessionId}:`, error);
        this.transports.delete(transport.sessionId);
      });

      this.transports.set(transport.sessionId, transport);

      const server = getIntercomMcpServer();
      await server.connect(transport);

      console.log(`SSE connection established with session: ${transport.sessionId}`);
    } catch (error) {
      console.error('Error establishing SSE connection:', error);
      if (!res.headersSent) {
        res.status(500).json({ error: 'Failed to establish SSE connection' });
      }
    }
  }

  private async handleMessages(req: Request, res: Response): Promise<void> {
    try {
      const sessionId = req.query.sessionId as string;

      if (!sessionId) {
        res.status(400).json({ error: 'Missing sessionId parameter' });
        return;
      }

      const transport = this.transports.get(sessionId);
      if (!transport) {
        res.status(404).json({ error: 'Transport not found or session expired' });
        return;
      }

      const accessToken =
        process.env.INTERCOM_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

      if (!accessToken || !validateIntercomToken(accessToken)) {
        res.status(401).json({ error: 'Invalid or missing access token' });
        return;
      }

      const intercomClient = new IntercomClient(accessToken);

      await asyncLocalStorage.run({ intercomClient }, async () => {
        await transport.handlePostMessage(req, res);
      });
    } catch (error: any) {
      console.error('Error handling message:', error);
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
        res.status(200).json({ message: 'Session terminated' });
      } catch (error) {
        res.status(500).json({ error: 'Failed to terminate session' });
      }
    } else {
      res.status(404).json({ error: 'Session not found' });
    }
  }

  private handleStatus(_req: Request, res: Response): void {
    res.json({
      activeConnections: this.transports.size,
      sessions: Array.from(this.transports.keys()),
      timestamp: new Date().toISOString(),
    });
  }

  getRouter(): Router {
    return this.router;
  }
}
