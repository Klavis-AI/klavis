import express, { Request, Response, Router } from 'express';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { FirefliesClient, asyncLocalStorage } from '../client/firefliesClient.js';
import { ValidationUtils } from '../utils/validation.js';
import { createErrorResponse } from '../utils/errors.js';
import { getFirefliesMcpServer } from '../server.js';
import { safeLog } from '../client/firefliesClient.js';

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
    const accessToken = process.env.FIREFLIES_API_KEY || (req.headers['x-auth-token'] as string);

    if (!accessToken) {
      safeLog('error', 'Missing Fireflies API key in request');
      res.status(401).json(createErrorResponse('Missing Fireflies API key'));
      return;
    }

    if (!ValidationUtils.validateApiKey(accessToken)) {
      safeLog('error', 'Invalid Fireflies API key format');
      res.status(401).json(createErrorResponse('Invalid API key format'));
      return;
    }

    const firefliesClient = new FirefliesClient(accessToken);

    try {
      const connectionTest = await firefliesClient.testConnection();
      if (!connectionTest) {
        safeLog('error', 'Failed to connect to Fireflies API');
        res.status(401).json(createErrorResponse('Invalid API credentials or connection failed'));
        return;
      }

      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });

      const server = getFirefliesMcpServer();
      await server.connect(transport);

      safeLog('info', 'Processing MCP request with Fireflies client');

      asyncLocalStorage.run({ firefliesClient }, async () => {
        await transport.handleRequest(req, res, req.body);
      });

      res.on('close', () => {
        safeLog('info', 'MCP request connection closed');
        transport.close();
      });

      res.on('error', (error) => {
        safeLog('error', `Response error: ${error}`);
        transport.close();
      });
    } catch (error: any) {
      safeLog('error', `Error handling MCP request: ${error}`);
      if (!res.headersSent) {
        res.status(500).json(createErrorResponse(error, 'mcp_request_handler'));
      }
    }
  }

  private async handleGetMcp(_req: Request, res: Response): Promise<void> {
    safeLog('info', 'GET request to /mcp endpoint - method not allowed');
    res.status(405).json(createErrorResponse('Method not allowed - use POST for MCP requests'));
  }

  private async handleDeleteMcp(_req: Request, res: Response): Promise<void> {
    safeLog('info', 'DELETE request to /mcp endpoint - method not allowed');
    res.status(405).json(createErrorResponse('Method not allowed - use POST for MCP requests'));
  }

  getRouter(): Router {
    return this.router;
  }
}
