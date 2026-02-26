import path from 'node:path'
import { fileURLToPath } from 'url'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js'
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js'
import { randomUUID, randomBytes } from 'node:crypto'
import express from 'express'

import { initProxy, ValidationError } from '../src/init-server.js'

export async function startServer(args: string[] = process.argv) {
  const filename = fileURLToPath(import.meta.url)
  const directory = path.dirname(filename)
  const specPath = path.resolve(directory, '../scripts/notion-openapi.json')
  
  const baseUrl = process.env.BASE_URL ?? undefined

  // Parse command line arguments manually (similar to slack-mcp approach)
  function parseArgs() {
    const args = process.argv.slice(2);
    let transport = 'stdio'; // default
    let port = 3000;
    let authToken: string | undefined;
    let pageIds: string[] = [];
    let pageUrls: string[] = [];

    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--transport' && i + 1 < args.length) {
        transport = args[i + 1];
        i++; // skip next argument
      } else if (args[i] === '--port' && i + 1 < args.length) {
        port = parseInt(args[i + 1], 10);
        i++; // skip next argument
      } else if (args[i] === '--auth-token' && i + 1 < args.length) {
        authToken = args[i + 1];
        i++; // skip next argument
      } else if (args[i] === '--page-id' && i + 1 < args.length) {
        // Support comma-separated page IDs
        pageIds = args[i + 1].split(',').map(id => id.trim()).filter(id => id.length > 0);
        i++; // skip next argument
      } else if (args[i] === '--page-url' && i + 1 < args.length) {
        // Support comma-separated page URLs
        pageUrls = args[i + 1].split(',').map(url => url.trim()).filter(url => url.length > 0);
        i++; // skip next argument
      } else if (args[i] === '--help' || args[i] === '-h') {
        console.log(`
Usage: notion-mcp-server [options]

Options:
  --transport <type>     Transport type: 'stdio' or 'http' (default: stdio)
  --port <number>        Port for HTTP server when using Streamable HTTP transport (default: 3000)
  --auth-token <token>   Bearer token for HTTP transport authentication (optional)
  --page-id <ids>        Restrict access to these pages and their children (comma-separated page IDs)
  --page-url <urls>      Restrict access to these pages and their children (comma-separated page URLs)
  --help, -h             Show this help message

Environment Variables:
  NOTION_TOKEN           Notion integration token (recommended)
  OPENAPI_MCP_HEADERS    JSON string with Notion API headers (alternative)
  AUTH_TOKEN             Bearer token for HTTP transport authentication (alternative to --auth-token)
  NOTION_ROOT_PAGE_ID    Root page IDs for access control (comma-separated, alternative to --page-id)
  NOTION_ROOT_PAGE_URL   Root page URLs for access control (comma-separated, alternative to --page-url)

Examples:
  notion-mcp-server                                    # Use stdio transport (default)
  notion-mcp-server --transport stdio                  # Use stdio transport explicitly
  notion-mcp-server --transport http                   # Use Streamable HTTP transport on port 3000
  notion-mcp-server --page-id "abc123"                 # Limit access to page abc123 and its children
  notion-mcp-server --page-id "abc123,def456,ghi789"   # Limit access to multiple pages and their children
  notion-mcp-server --page-url "https://notion.so/xyz" # Limit access to page xyz and its children
  notion-mcp-server --page-url "https://notion.so/page1,https://notion.so/page2" # Multiple page URLs
`);
        process.exit(0);
      }
      // Ignore unrecognized arguments (like command name passed by Docker)
    }

    // Also check environment variables and merge with command line args
    const envPageIds = process.env.NOTION_ROOT_PAGE_ID?.split(',').map(id => id.trim()).filter(id => id.length > 0) || [];
    const envPageUrls = process.env.NOTION_ROOT_PAGE_URL?.split(',').map(url => url.trim()).filter(url => url.length > 0) || [];
    
    // Merge command line args with environment variables (command line takes precedence)
    const finalPageIds = pageIds.length > 0 ? pageIds : envPageIds;
    const finalPageUrls = pageUrls.length > 0 ? pageUrls : envPageUrls;

    return { transport: transport.toLowerCase(), port, authToken, pageIds: finalPageIds, pageUrls: finalPageUrls };
  }

  const options = parseArgs()
  const transport = options.transport

  if (transport === 'stdio') {
    // Use stdio transport (default)
    const proxy = await initProxy(specPath, baseUrl, { 
      pageIds: options.pageIds, 
      pageUrls: options.pageUrls 
    })
    await proxy.connect(new StdioServerTransport())
    return proxy.getServer()
  } else if (transport === 'http') {
    // Use Streamable HTTP transport
    const app = express()
    app.use(express.json())

    // Generate or use provided auth token (from CLI arg or env var)
    const authToken = options.authToken || process.env.AUTH_TOKEN || randomBytes(32).toString('hex')
    if (!options.authToken && !process.env.AUTH_TOKEN) {
      console.log(`Generated auth token: ${authToken}`)
      console.log(`Use this token in the Authorization header: Bearer ${authToken}`)
    }

    // Authorization middleware
    const authenticateToken = (req: express.Request, res: express.Response, next: express.NextFunction): void => {
      const authHeader = req.headers['authorization']
      const token = authHeader && authHeader.split(' ')[1] // Bearer TOKEN

      if (!token) {
        res.status(401).json({
          jsonrpc: '2.0',
          error: {
            code: -32001,
            message: 'Unauthorized: Missing bearer token',
          },
          id: null,
        })
        return
      }

      if (token !== authToken) {
        res.status(403).json({
          jsonrpc: '2.0',
          error: {
            code: -32002,
            message: 'Forbidden: Invalid bearer token',
          },
          id: null,
        })
        return
      }

      next()
    }

    // Health endpoint (no authentication required)
    app.get('/health', (req, res) => {
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        transport: 'http',
        port: options.port
      })
    })

    // Apply authentication to all /mcp routes
    app.use('/mcp', authenticateToken)

    // Map to store transports by session ID
    const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {}

    // Handle POST requests for client-to-server communication
    app.post('/mcp', async (req, res) => {
      try {
        // Check for existing session ID
        const sessionId = req.headers['mcp-session-id'] as string | undefined
        let transport: StreamableHTTPServerTransport

        if (sessionId && transports[sessionId]) {
          // Reuse existing transport
          transport = transports[sessionId]
        } else if (!sessionId && isInitializeRequest(req.body)) {
          // New initialization request
          transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => randomUUID(),
            onsessioninitialized: (sessionId) => {
              // Store the transport by session ID
              transports[sessionId] = transport
            }
          })

          // Clean up transport when closed
          transport.onclose = () => {
            if (transport.sessionId) {
              delete transports[transport.sessionId]
            }
          }

          const proxy = await initProxy(specPath, baseUrl, { 
            pageIds: options.pageIds, 
            pageUrls: options.pageUrls 
          })
          await proxy.connect(transport)
        } else {
          // Invalid request
          res.status(400).json({
            jsonrpc: '2.0',
            error: {
              code: -32000,
              message: 'Bad Request: No valid session ID provided',
            },
            id: null,
          })
          return
        }

        // Handle the request
        await transport.handleRequest(req, res, req.body)
      } catch (error) {
        console.error('Error handling MCP request:', error)
        if (!res.headersSent) {
          res.status(500).json({
            jsonrpc: '2.0',
            error: {
              code: -32603,
              message: 'Internal server error',
            },
            id: null,
          })
        }
      }
    })

    // Handle GET requests for server-to-client notifications via Streamable HTTP
    app.get('/mcp', async (req, res) => {
      const sessionId = req.headers['mcp-session-id'] as string | undefined
      if (!sessionId || !transports[sessionId]) {
        res.status(400).send('Invalid or missing session ID')
        return
      }
      
      const transport = transports[sessionId]
      await transport.handleRequest(req, res)
    })

    // Handle DELETE requests for session termination
    app.delete('/mcp', async (req, res) => {
      const sessionId = req.headers['mcp-session-id'] as string | undefined
      if (!sessionId || !transports[sessionId]) {
        res.status(400).send('Invalid or missing session ID')
        return
      }
      
      const transport = transports[sessionId]
      await transport.handleRequest(req, res)
    })

    const port = options.port
    app.listen(port, '0.0.0.0', () => {
      console.log(`MCP Server listening on port ${port}`)
      console.log(`Endpoint: http://0.0.0.0:${port}/mcp`)
      console.log(`Health check: http://0.0.0.0:${port}/health`)
      console.log(`Authentication: Bearer token required`)
      if (options.authToken) {
        console.log(`Using provided auth token`)
      }
    })

    // Return a dummy server for compatibility
    return { close: () => {} }
  } else {
    throw new Error(`Unsupported transport: ${transport}. Use 'stdio' or 'http'.`)
  }
}

startServer(process.argv).catch(error => {
  if (error instanceof ValidationError) {
    console.error('Invalid OpenAPI 3.1 specification:')
    error.errors.forEach(err => console.error(err))
  } else {
    console.error('Error:', error)
  }
  process.exit(1)
})
