#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { whoisAsn, whoisDomain, whoisTld, whoisIp, whoisQuery } from 'whoiser';
import net from 'net';
import dotenv from 'dotenv';

dotenv.config();

/**
 * Lookup the authoritative WHOIS server for a query via IANA.
 *
 * The built-in `findWhoisServerInIana` inside whoiser has a hardcoded
 * 1 000 ms timeout which is too short when traffic goes through a
 * SOCKS5 proxy.  This helper lets us control the timeout.
 */
async function findWhoisServer(query: string, timeout = 15000): Promise<string> {
  const raw = await whoisQuery('whois.iana.org', query, timeout);
  // Parse the "whois:" field out of the IANA response
  const match = String(raw).match(/^whois:\s*(.+)$/m);
  if (!match) {
    throw new Error(`No WHOIS server found in IANA response for "${query}"`);
  }
  return match[1].trim();
}

// Tool definitions
const WHOIS_DOMAIN_TOOL: Tool = {
  name: 'whois_domain',
  description: 'Looks up whois information about the domain',
  inputSchema: {
    type: 'object',
    properties: {
      domain: {
        type: 'string',
        description: 'The domain name to look up',
      },
    },
    required: ['domain'],
  },
};

const WHOIS_TLD_TOOL: Tool = {
  name: 'whois_tld',
  description: 'Looks up whois information about the Top Level Domain (TLD)',
  inputSchema: {
    type: 'object',
    properties: {
      tld: {
        type: 'string',
        description: 'The top level domain to look up',
      },
    },
    required: ['tld'],
  },
};

const WHOIS_IP_TOOL: Tool = {
  name: 'whois_ip',
  description: 'Looks up whois information about the IP address',
  inputSchema: {
    type: 'object',
    properties: {
      ip: {
        type: 'string',
        description: 'The IP address to look up',
      },
    },
    required: ['ip'],
  },
};

const WHOIS_ASN_TOOL: Tool = {
  name: 'whois_as',
  description: 'Looks up whois information about the Autonomous System Number (ASN)',
  inputSchema: {
    type: 'object',
    properties: {
      asn: {
        type: 'string',
        description: 'The ASN to look up (e.g. AS13335)',
      },
    },
    required: ['asn'],
  },
};

const WHOIS_TOOLS = [
  WHOIS_DOMAIN_TOOL,
  WHOIS_TLD_TOOL,
  WHOIS_IP_TOOL,
  WHOIS_ASN_TOOL,
] as const;

// API handlers
async function handleWhoisDomain(domain: string) {
  try {
    const result = await whoisDomain(domain, { timeout: 30000 });
    return {
      content: [{ type: 'text', text: `Domain whois lookup for: \n${JSON.stringify(result)}` }],
      isError: false,
    };
  } catch (err: unknown) {
    const error = err as Error;
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true,
    };
  }
}

async function handleWhoisTld(tld: string) {
  try {
    const result = await whoisTld(tld, 30000);
    return {
      content: [{ type: 'text', text: `TLD whois lookup for: \n${JSON.stringify(result)}` }],
      isError: false,
    };
  } catch (err: unknown) {
    const error = err as Error;
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true,
    };
  }
}

async function handleWhoisIp(ip: string) {
  try {
    if (!net.isIP(ip)) {
      throw new Error(`Invalid IP address "${ip}"`);
    }
    // Discover the authoritative WHOIS server ourselves with a
    // generous timeout (the library's internal lookup is only 1 s).
    const host = await findWhoisServer(ip, 15000);
    const result = await whoisIp(ip, { host, timeout: 30000 });
    return {
      content: [{ type: 'text', text: `IP whois lookup for: \n${JSON.stringify(result)}` }],
      isError: false,
    };
  } catch (err: unknown) {
    const error = err as Error;
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true,
    };
  }
}

async function handleWhoisAsn(asn: string) {
  try {
    const asnNumber = parseInt(asn.replace(/^AS/i, ''));
    if (isNaN(asnNumber)) {
      return {
        content: [{ type: 'text', text: `Error: Invalid ASN format. Expected format: AS12345` }],
        isError: true,
      };
    }
    // Discover the authoritative WHOIS server ourselves with a
    // generous timeout (the library's internal lookup is only 1 s).
    const host = await findWhoisServer(String(asnNumber), 15000);
    const result = await whoisAsn(asnNumber, { host, timeout: 30000 });
    return {
      content: [{ type: 'text', text: `ASN whois lookup for: \n${JSON.stringify(result)}` }],
      isError: false,
    };
  } catch (err: unknown) {
    const error = err as Error;
    return {
      content: [{ type: 'text', text: `Error: ${error.message}` }],
      isError: true,
    };
  }
}

// Utility functions
function safeLog(level: string, data: any): void {
  try {
    const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
    console.log(`[${level.toUpperCase()}] ${logData}`);
  } catch (error) {
    console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
  }
}

// Main server function
const getWhoisMcpServer = () => {
  const server = new Server(
    {
      name: 'mcp-server/whois',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    },
  );

  // Set up request handlers
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: WHOIS_TOOLS,
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'whois_domain': {
          const { domain } = args as { domain: string };
          return await handleWhoisDomain(domain);
        }

        case 'whois_tld': {
          const { tld } = args as { tld: string };
          return await handleWhoisTld(tld);
        }

        case 'whois_ip': {
          const { ip } = args as { ip: string };
          return await handleWhoisIp(ip);
        }

        case 'whois_as': {
          const { asn } = args as { asn: string };
          return await handleWhoisAsn(asn);
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error: any) {
      safeLog('error', `Tool ${name} failed: ${error.message}`);
      return {
        content: [{
          type: 'text',
          text: `Error: ${error.message}`,
        }],
        isError: true,
      };
    }
  });

  return server;
};

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const server = getWhoisMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
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
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: '2.0',
    error: {
      code: -32000,
      message: 'Method not allowed.',
    },
    id: null,
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: '2.0',
    error: {
      code: -32000,
      message: 'Method not allowed.',
    },
    id: null,
  }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get('/sse', async (req, res) => {
  const transport = new SSEServerTransport('/messages', res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
    }
  });

  transports.set(transport.sessionId, transport);

  const server = getWhoisMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post('/messages', async (req, res) => {
  const sessionId = req.query.sessionId as string;
  const transport = transports.get(sessionId);
  if (transport) {
    await transport.handlePostMessage(req, res);
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: 'Transport not found' });
  }
});

app.listen(5000, () => {
  console.log('Whois MCP server running on port 5000');
});
