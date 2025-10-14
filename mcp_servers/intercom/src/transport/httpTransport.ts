import express, { Request, Response, Router } from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { IntercomClient, asyncLocalStorage } from '../client/intercomClient.js';
import { validateIntercomToken } from '../utils/validation.js';
import { createErrorResponse } from '../utils/errors.js';
import { getIntercomMcpServer } from '../server.js';

export class HttpTransport {
  private router: Router;

  constructor() {
    this.router = express.Router();
    this.setupRoutes();
  }

  private setupRoutes(): void {
    this.router.post('/mcp', this.handleMcpRequest.bind(this));
    this.router.get('/mcp', this.handleGetMcp.bind(this));
    this.router.delete('/mcp', this.handleDeleteMcp.bind(this));
  }

  private async handleMcpRequest(req: Request, res: Response): Promise<void> {
    const accessToken =
      process.env.INTERCOM_ACCESS_TOKEN || (req.headers['x-auth-token'] as string);

    if (!accessToken) {
      res.status(401).json(createErrorResponse(-32001, 'Missing Intercom access token'));
      return;
    }

    if (!validateIntercomToken(accessToken)) {
      res.status(401).json(createErrorResponse(-32001, 'Invalid token format'));
      return;
    }

    const intercomClient = new IntercomClient(accessToken);

    try {
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });

      const server = getIntercomMcpServer();
      await server.connect(transport);

      asyncLocalStorage.run({ intercomClient }, async () => {
        await transport.handleRequest(req, res, req.body);
      });

      res.on('close', () => {
        console.log('Request closed');
        transport.close();
      });
    } catch (error: any) {
      console.error('Error handling MCP request:', error);
      if (!res.headersSent) {
        res
          .status(500)
          .json(createErrorResponse(-32603, `Internal server error: ${error.message}`));
      }
    }
  }

  private async handleGetMcp(_req: Request, res: Response): Promise<void> {
    res.status(405).json(createErrorResponse(-32000, 'Method not allowed'));
  }

  private async handleDeleteMcp(_req: Request, res: Response): Promise<void> {
    res.status(405).json(createErrorResponse(-32000, 'Method not allowed'));
  }

  getRouter(): Router {
    return this.router;
  }
}
