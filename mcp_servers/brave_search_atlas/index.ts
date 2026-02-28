#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { AsyncLocalStorage } from 'async_hooks';

const asyncLocalStorage = new AsyncLocalStorage<{ apiKey: string }>();

function extractApiKey(req?: Request | null): string {
  let authData = process.env.AUTH_DATA;

  if (!authData) {
    const envKey = process.env.BRAVE_API_KEY;
    if (envKey) return envKey;
  }

  if (!authData && req?.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error decoding x-auth-data header:', error);
    }
  }

  if (!authData) {
    console.error('Error: Brave API key missing. Provide via AUTH_DATA env var, BRAVE_API_KEY env var, or x-auth-data header.');
    return '';
  }

  try {
    const json = JSON.parse(authData);
    const mask = (v: string | undefined) => v ? v.slice(0, 4) + '***' + v.slice(-4) : undefined;
    console.log('Parsed brave_search auth data:', {
      api_key: mask(json.api_key),
    });
    return json.api_key ?? json.BRAVE_API_KEY ?? '';
  } catch {
    return authData;
  }
}

function getApiKey(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.apiKey) return store.apiKey;
  return extractApiKey(null);
}

// Tool definitions
const WEB_SEARCH_TOOL: Tool = {
  name: "brave_web_search",
  description:
    "Performs a web search using the Brave Search API, ideal for general queries, news, articles, and online content. " +
    "Use this for broad information gathering, recent events, or when you need diverse web sources. " +
    "Supports pagination, content filtering, and freshness controls. " +
    "Maximum 20 results per request, with offset for pagination. ",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query (max 400 chars, 50 words)"
      },
      count: {
        type: "number",
        description: "Number of results (1-20, default 10)",
        default: 10
      },
      offset: {
        type: "number",
        description: "Pagination offset (max 9, default 0)",
        default: 0
      },
    },
    required: ["query"],
  },
};

const LOCAL_SEARCH_TOOL: Tool = {
  name: "brave_local_search",
  description:
    "Searches for local businesses and places using Brave's Local Search API. " +
    "Best for queries related to physical locations, businesses, restaurants, services, etc. " +
    "Returns detailed information including:\n" +
    "- Business names and addresses\n" +
    "- Ratings and review counts\n" +
    "- Phone numbers and opening hours\n" +
    "Use this when the query implies 'near me' or mentions specific locations. " +
    "Automatically falls back to web search if no local results are found.",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Local search query (e.g. 'pizza near Central Park')"
      },
      count: {
        type: "number",
        description: "Number of results (1-20, default 5)",
        default: 5
      },
    },
    required: ["query"]
  }
};

// Types
interface BraveWeb {
  web?: {
    results?: Array<{
      title: string;
      description: string;
      url: string;
      language?: string;
      published?: string;
      rank?: number;
    }>;
  };
  locations?: {
    results?: Array<{
      id: string;
      title?: string;
    }>;
  };
}

interface BraveLocation {
  id: string;
  name: string;
  address: {
    streetAddress?: string;
    addressLocality?: string;
    addressRegion?: string;
    postalCode?: string;
  };
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  phone?: string;
  rating?: {
    ratingValue?: number;
    ratingCount?: number;
  };
  openingHours?: string[];
  priceRange?: string;
}

interface BravePoiResponse {
  results: BraveLocation[];
}

interface BraveDescription {
  descriptions: {[id: string]: string};
}

function isBraveWebSearchArgs(args: unknown): args is { query: string; count?: number; offset?: number } {
  return (
    typeof args === "object" &&
    args !== null &&
    "query" in args &&
    typeof (args as { query: string }).query === "string"
  );
}

function isBraveLocalSearchArgs(args: unknown): args is { query: string; count?: number } {
  return (
    typeof args === "object" &&
    args !== null &&
    "query" in args &&
    typeof (args as { query: string }).query === "string"
  );
}

async function performWebSearch(query: string, count: number = 10, offset: number = 0) {
  const apiKey = getApiKey();
  const url = new URL('https://api.search.brave.com/res/v1/web/search');
  url.searchParams.set('q', query);
  url.searchParams.set('count', Math.min(count, 20).toString());
  url.searchParams.set('offset', offset.toString());

  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'Accept-Encoding': 'gzip',
      'X-Subscription-Token': apiKey
    }
  });

  if (!response.ok) {
    throw new Error(`Brave API error: ${response.status} ${response.statusText}\n${await response.text()}`);
  }

  const data = await response.json() as BraveWeb;
  const results = (data.web?.results || []).map(result => ({
    title: result.title || '',
    description: result.description || '',
    url: result.url || ''
  }));

  return results.map(r =>
    `Title: ${r.title}\nDescription: ${r.description}\nURL: ${r.url}`
  ).join('\n\n');
}

async function performLocalSearch(query: string, count: number = 5) {
  const apiKey = getApiKey();
  const webUrl = new URL('https://api.search.brave.com/res/v1/web/search');
  webUrl.searchParams.set('q', query);
  webUrl.searchParams.set('search_lang', 'en');
  webUrl.searchParams.set('result_filter', 'locations');
  webUrl.searchParams.set('count', Math.min(count, 20).toString());

  const webResponse = await fetch(webUrl, {
    headers: {
      'Accept': 'application/json',
      'Accept-Encoding': 'gzip',
      'X-Subscription-Token': apiKey
    }
  });

  if (!webResponse.ok) {
    throw new Error(`Brave API error: ${webResponse.status} ${webResponse.statusText}\n${await webResponse.text()}`);
  }

  const webData = await webResponse.json() as BraveWeb;
  const locationIds = webData.locations?.results?.filter((r): r is {id: string; title?: string} => r.id != null).map(r => r.id) || [];

  if (locationIds.length === 0) {
    return performWebSearch(query, count);
  }

  const [poisData, descriptionsData] = await Promise.all([
    getPoisData(locationIds),
    getDescriptionsData(locationIds)
  ]);

  return formatLocalResults(poisData, descriptionsData);
}

async function getPoisData(ids: string[]): Promise<BravePoiResponse> {
  const apiKey = getApiKey();
  const url = new URL('https://api.search.brave.com/res/v1/local/pois');
  ids.filter(Boolean).forEach(id => url.searchParams.append('ids', id));
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'Accept-Encoding': 'gzip',
      'X-Subscription-Token': apiKey
    }
  });

  if (!response.ok) {
    throw new Error(`Brave API error: ${response.status} ${response.statusText}\n${await response.text()}`);
  }

  return await response.json() as BravePoiResponse;
}

async function getDescriptionsData(ids: string[]): Promise<BraveDescription> {
  const apiKey = getApiKey();
  const url = new URL('https://api.search.brave.com/res/v1/local/descriptions');
  ids.filter(Boolean).forEach(id => url.searchParams.append('ids', id));
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json',
      'Accept-Encoding': 'gzip',
      'X-Subscription-Token': apiKey
    }
  });

  if (!response.ok) {
    throw new Error(`Brave API error: ${response.status} ${response.statusText}\n${await response.text()}`);
  }

  return await response.json() as BraveDescription;
}

function formatLocalResults(poisData: BravePoiResponse, descData: BraveDescription): string {
  return (poisData.results || []).map(poi => {
    const address = [
      poi.address?.streetAddress ?? '',
      poi.address?.addressLocality ?? '',
      poi.address?.addressRegion ?? '',
      poi.address?.postalCode ?? ''
    ].filter(part => part !== '').join(', ') || 'N/A';

    return `Name: ${poi.name}
Address: ${address}
Phone: ${poi.phone || 'N/A'}
Rating: ${poi.rating?.ratingValue ?? 'N/A'} (${poi.rating?.ratingCount ?? 0} reviews)
Price Range: ${poi.priceRange || 'N/A'}
Hours: ${(poi.openingHours || []).join(', ') || 'N/A'}
Description: ${descData.descriptions[poi.id] || 'No description available'}
`;
  }).join('\n---\n') || 'No local results found';
}

//=============================================================================
// MCP SERVER
//=============================================================================

class BraveSearchServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "example-servers/brave-search",
        version: "0.1.0",
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    this.setupToolHandlers();

    this.server.onerror = (error) => console.error("[MCP Error]", error);
    process.on("SIGINT", async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  getServer(): Server {
    return this.server;
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [WEB_SEARCH_TOOL, LOCAL_SEARCH_TOOL],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        if (!args) {
          throw new Error("No arguments provided");
        }

        switch (name) {
          case "brave_web_search": {
            if (!isBraveWebSearchArgs(args)) {
              throw new Error("Invalid arguments for brave_web_search");
            }
            const { query, count = 10 } = args;
            const results = await performWebSearch(query, count);
            return {
              content: [{ type: "text", text: results }],
              isError: false,
            };
          }

          case "brave_local_search": {
            if (!isBraveLocalSearchArgs(args)) {
              throw new Error("Invalid arguments for brave_local_search");
            }
            const { query, count = 5 } = args;
            const results = await performLocalSearch(query, count);
            return {
              content: [{ type: "text", text: results }],
              isError: false,
            };
          }

          default:
            return {
              content: [{ type: "text", text: `Unknown tool: ${name}` }],
              isError: true,
            };
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async runStdio() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Brave Search MCP Server running on stdio");
  }
}

function createBraveSearchServer(): BraveSearchServer {
  return new BraveSearchServer();
}

//=============================================================================
// HTTP SERVER SETUP
//=============================================================================

const app = express();

app.post('/mcp', async (req: Request, res: Response) => {
  const apiKey = extractApiKey(req);
  const braveServer = createBraveSearchServer();
  const server = braveServer.getServer();

  try {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);

    asyncLocalStorage.run({ apiKey }, async () => {
      await transport.handleRequest(req, res, req.body);
    });

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
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Method not allowed." },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: { code: -32000, message: "Method not allowed." },
    id: null
  }));
});

//=============================================================================
// MAIN ENTRY POINT
//=============================================================================

const PORT = parseInt(process.env.PORT || '5000', 10);
const TRANSPORT = process.env.TRANSPORT || 'http';

if (TRANSPORT === 'stdio') {
  const server = createBraveSearchServer();
  server.runStdio().catch((error) => {
    console.error("Server error:", error);
    process.exit(1);
  });
} else {
  app.listen(PORT, () => {
    console.log(`Brave Search MCP server running on port ${PORT}`);
    console.log(`  - Streamable HTTP: POST /mcp`);
  });
}
