import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    Tool,
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';
import fetch from 'node-fetch';

dotenv.config();

// =============================================================================
// ASYNC LOCAL STORAGE
// =============================================================================

const asyncLocalStorage = new AsyncLocalStorage<{
    apiKey: string;
    orbitKey?: string;
}>();

function getApiKey(): string {
    const store = asyncLocalStorage.getStore();
    if (!store || !store.apiKey) {
        throw new Error('Olostep API key not found in request context.');
    }
    return store.apiKey;
}

function getOrbitKey(): string | undefined {
    return asyncLocalStorage.getStore()?.orbitKey;
}

// =============================================================================
// AUTH EXTRACTION (Klavis pattern)
// =============================================================================

function extractCredentials(req: Request): { apiKey: string; orbitKey?: string } {
    // 1. Check AUTH_DATA env var (Klavis standard)
    let authData = process.env.AUTH_DATA;

    // 2. Fallback: x-auth-data header (base64-encoded JSON)
    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data header:', error);
        }
    }

    if (authData) {
        try {
            const parsed = JSON.parse(authData);
            return {
                apiKey: parsed.access_token ?? parsed.api_key ?? '',
                orbitKey: parsed.orbit_key,
            };
        } catch (error) {
            console.error('Error parsing AUTH_DATA JSON:', error);
        }
    }

    // 3. Fallback: OLOSTEP_API_KEY env var (standalone/local usage)
    if (process.env.OLOSTEP_API_KEY) {
        return {
            apiKey: process.env.OLOSTEP_API_KEY,
            orbitKey: process.env.ORBIT_KEY,
        };
    }

    console.error('Error: Olostep API key is missing. Provide it via AUTH_DATA env var, x-auth-data header, or OLOSTEP_API_KEY env var.');
    return { apiKey: '' };
}

// =============================================================================
// OLOSTEP API HELPERS
// =============================================================================

const OLOSTEP_API_URL = 'https://api.olostep.com/v1';

function apiHeaders(apiKey: string): Record<string, string> {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
    };
}

type ToolResult = {
    content: { type: 'text'; text: string }[];
    isError?: boolean;
};

function errorResult(message: string): ToolResult {
    return { isError: true, content: [{ type: 'text', text: message }] };
}

function textResult(text: string): ToolResult {
    return { content: [{ type: 'text', text }] };
}

function jsonResult(data: unknown): ToolResult {
    return textResult(JSON.stringify(data, null, 2));
}

async function parseApiError(response: { status: number; statusText: string; json: () => Promise<unknown> }): Promise<string> {
    let details: unknown = null;
    try { details = await response.json(); } catch { /* ignore */ }
    return `Olostep API Error: ${response.status} ${response.statusText}. Details: ${JSON.stringify(details)}`;
}

// =============================================================================
// TOOL DEFINITIONS (JSON Schema)
// =============================================================================

const OLOSTEP_SCRAPE_WEBSITE: Tool = {
    name: 'olostep_scrape_website',
    description: 'Extract content from a single URL. Supports multiple formats and JavaScript rendering.',
    inputSchema: {
        type: 'object',
        properties: {
            url_to_scrape: {
                type: 'string',
                description: 'The URL of the website you want to scrape.',
            },
            output_format: {
                type: 'string',
                enum: ['markdown', 'html', 'json', 'text'],
                default: 'markdown',
                description: 'Choose format ("html", "markdown", "json", or "text"). Default: "markdown".',
            },
            country: {
                type: 'string',
                description: 'Optional country code (e.g., US, GB, CA) for location-specific scraping.',
            },
            wait_before_scraping: {
                type: 'integer',
                minimum: 0,
                maximum: 10000,
                default: 0,
                description: 'Wait time in milliseconds before scraping (0-10000). Useful for dynamic content.',
            },
            parser: {
                type: 'string',
                description: 'Optional parser ID for specialized extraction (e.g., "@olostep/amazon-product").',
            },
        },
        required: ['url_to_scrape'],
    },
};

const OLOSTEP_SEARCH_WEB: Tool = {
    name: 'olostep_search_web',
    description: 'Search the web for a given query and return structured results (non-AI, parser-based).',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query.',
            },
            country: {
                type: 'string',
                default: 'US',
                description: 'Optional country code for localized results (e.g., US, GB).',
            },
        },
        required: ['query'],
    },
};

const OLOSTEP_ANSWERS: Tool = {
    name: 'olostep_answers',
    description: 'Search the web and return AI-powered answers in the JSON structure you want, with sources and citations.',
    inputSchema: {
        type: 'object',
        properties: {
            task: {
                type: 'string',
                description: 'Question or task to answer using web data.',
            },
            json: {
                description: 'Optional JSON schema/object or a short description of the desired output shape. Example: { "book_title": "", "author": "", "release_date": "" }.',
            },
        },
        required: ['task'],
    },
};

const OLOSTEP_BATCH_SCRAPE_URLS: Tool = {
    name: 'olostep_batch_scrape_urls',
    description: 'Scrape up to 10k URLs at the same time. Perfect for large-scale data extraction. Returns a batch_id immediately. Use olostep_get_batch_results with the batch_id to fetch the scraped content once the batch completes (~5-8 min). Set wait_for_completion_seconds to poll automatically.',
    inputSchema: {
        type: 'object',
        properties: {
            urls_to_scrape: {
                type: 'array',
                items: {
                    type: 'object',
                    properties: {
                        url: { type: 'string' },
                        custom_id: { type: 'string' },
                    },
                    required: ['url'],
                },
                minItems: 1,
                maxItems: 10000,
                description: 'JSON array of objects with "url" and optional "custom_id".',
            },
            output_format: {
                type: 'string',
                enum: ['markdown', 'html', 'json', 'text'],
                default: 'markdown',
                description: 'Choose format for all URLs. Default: "markdown".',
            },
            country: {
                type: 'string',
                description: 'Optional country code for location-specific scraping.',
            },
            wait_before_scraping: {
                type: 'integer',
                minimum: 0,
                maximum: 10000,
                default: 0,
                description: 'Wait time in milliseconds before scraping each URL.',
            },
            parser: {
                type: 'string',
                description: 'Optional parser ID for specialized extraction (e.g. @olostep/google-search).',
            },
            wait_for_completion_seconds: {
                type: 'integer',
                minimum: 0,
                maximum: 300,
                default: 0,
                description: 'Seconds to wait for batch completion. If >0, polls every 10s until done or timeout. Use 0 to return immediately with batch_id. Recommended: 60 for small batches, 0 for large ones.',
            },
        },
        required: ['urls_to_scrape'],
    },
};

const OLOSTEP_GET_BATCH_RESULTS: Tool = {
    name: 'olostep_get_batch_results',
    description: 'Retrieve the status and scraped content for a batch job. Pass the batch_id returned by olostep_batch_scrape_urls. If the batch is completed, returns the scraped content for each URL. If still in_progress, returns the current status so you can call again later.',
    inputSchema: {
        type: 'object',
        properties: {
            batch_id: {
                type: 'string',
                description: 'The batch_id (or id) returned from olostep_batch_scrape_urls.',
            },
            formats: {
                type: 'array',
                items: { type: 'string', enum: ['markdown', 'html', 'json', 'text'] },
                default: ['markdown'],
                description: 'Content formats to retrieve per URL. Default: ["markdown"].',
            },
            items_limit: {
                type: 'integer',
                minimum: 1,
                maximum: 100,
                default: 20,
                description: 'Max number of items to retrieve content for (1-100). Default: 20.',
            },
        },
        required: ['batch_id'],
    },
};

const OLOSTEP_CREATE_CRAWL: Tool = {
    name: 'olostep_create_crawl',
    description: 'Autonomously discover and scrape entire websites by following links from a start URL.',
    inputSchema: {
        type: 'object',
        properties: {
            start_url: {
                type: 'string',
                description: 'Starting URL for the crawl.',
            },
            max_pages: {
                type: 'integer',
                minimum: 1,
                default: 10,
                description: 'Maximum number of pages to crawl.',
            },
            follow_links: {
                type: 'boolean',
                default: true,
                description: 'Whether to follow links found on pages.',
            },
            output_format: {
                type: 'string',
                enum: ['markdown', 'html', 'json', 'text'],
                default: 'markdown',
                description: 'Format for scraped content. Default: "markdown".',
            },
            country: {
                type: 'string',
                description: 'Optional country code for location-specific crawling.',
            },
            parser: {
                type: 'string',
                description: 'Optional parser ID for specialized content extraction.',
            },
        },
        required: ['start_url'],
    },
};

const OLOSTEP_CREATE_MAP: Tool = {
    name: 'olostep_create_map',
    description: 'Get all URLs on a website. Extract URLs for discovery and site analysis.',
    inputSchema: {
        type: 'object',
        properties: {
            website_url: {
                type: 'string',
                description: 'Website URL to extract links from.',
            },
            search_query: {
                type: 'string',
                description: 'Optional search query to filter URLs (e.g., "blog").',
            },
            top_n: {
                type: 'integer',
                minimum: 1,
                description: 'Optional limit for number of URLs returned.',
            },
            include_url_patterns: {
                type: 'array',
                items: { type: 'string' },
                description: 'Optional glob patterns to include (e.g., "/blog/**").',
            },
            exclude_url_patterns: {
                type: 'array',
                items: { type: 'string' },
                description: 'Optional glob patterns to exclude (e.g., "/admin/**").',
            },
        },
        required: ['website_url'],
    },
};

const OLOSTEP_GET_WEBPAGE_CONTENT: Tool = {
    name: 'olostep_get_webpage_content',
    description: 'Retrieve content of a webpage in markdown.',
    inputSchema: {
        type: 'object',
        properties: {
            url_to_scrape: {
                type: 'string',
                description: 'The URL of the webpage to scrape.',
            },
            wait_before_scraping: {
                type: 'integer',
                minimum: 0,
                default: 0,
                description: 'Time to wait in milliseconds before starting the scrape.',
            },
            country: {
                type: 'string',
                description: 'Residential country to load the request from (e.g., US, CA, GB). Optional.',
            },
        },
        required: ['url_to_scrape'],
    },
};

const OLOSTEP_GET_WEBSITE_URLS: Tool = {
    name: 'olostep_get_website_urls',
    description: 'Search and retrieve relevant URLs from a website.',
    inputSchema: {
        type: 'object',
        properties: {
            url: {
                type: 'string',
                description: 'The URL of the website to map.',
            },
            search_query: {
                type: 'string',
                description: 'The search query to sort URLs by.',
            },
        },
        required: ['url', 'search_query'],
    },
};

const ALL_TOOLS: Tool[] = [
    OLOSTEP_SCRAPE_WEBSITE,
    OLOSTEP_SEARCH_WEB,
    OLOSTEP_ANSWERS,
    OLOSTEP_BATCH_SCRAPE_URLS,
    OLOSTEP_GET_BATCH_RESULTS,
    OLOSTEP_CREATE_CRAWL,
    OLOSTEP_CREATE_MAP,
    OLOSTEP_GET_WEBPAGE_CONTENT,
    OLOSTEP_GET_WEBSITE_URLS,
];

// =============================================================================
// TOOL HANDLERS
// =============================================================================

async function handleScrapeWebsite(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const orbitKey = getOrbitKey();
    const headers = apiHeaders(apiKey);

    const formats: string[] = [args.output_format || 'markdown'];
    const body: Record<string, unknown> = {
        url_to_scrape: args.url_to_scrape,
        formats,
        wait_before_scraping: args.wait_before_scraping ?? 0,
    };
    if (args.country) body.country = args.country;
    if (orbitKey) body.force_connection_id = orbitKey;
    if (args.parser) body.parser_extract = { parser_id: args.parser };

    const response = await fetch(`${OLOSTEP_API_URL}/scrapes`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = (await response.json()) as { result?: unknown };
    return jsonResult(data.result ?? {});
}

async function handleSearchWeb(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const orbitKey = getOrbitKey();
    const headers = apiHeaders(apiKey);

    const searchUrl = new URL('https://www.google.com/search');
    searchUrl.searchParams.append('q', args.query);
    if (args.country) searchUrl.searchParams.append('gl', args.country);

    const body = {
        formats: ['json', 'parser_extract'],
        parser_extract: { parser_id: '@olostep/google-search' },
        url_to_scrape: searchUrl.toString(),
        wait_before_scraping: 0,
        ...(orbitKey && { force_connection_id: orbitKey }),
    };

    const response = await fetch(`${OLOSTEP_API_URL}/scrapes`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = (await response.json()) as { result?: { json_content?: string } };
    if (data.result?.json_content) {
        const parsed = JSON.parse(data.result.json_content);
        return jsonResult(parsed);
    }
    return errorResult('Error: No search results found in Olostep API response.');
}

async function handleAnswers(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const headers = apiHeaders(apiKey);

    const payload: Record<string, unknown> = { task: args.task };
    if (args.json !== undefined) payload.json = args.json;

    const response = await fetch(`${OLOSTEP_API_URL}/answers`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = await response.json();
    return jsonResult(data);
}

async function handleBatchScrapeUrls(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const orbitKey = getOrbitKey();
    const headers = apiHeaders(apiKey);

    const formats: string[] = [args.output_format || 'markdown'];
    const items = (args.urls_to_scrape as { url: string; custom_id?: string }[]).map((item) => ({
        url: item.url,
        ...(item.custom_id && { custom_id: item.custom_id }),
    }));

    const payload: Record<string, unknown> = {
        items,
        formats,
        wait_before_scraping: args.wait_before_scraping ?? 0,
    };
    if (args.country) payload.country = args.country;
    if (orbitKey) payload.force_connection_id = orbitKey;
    if (args.parser) payload.parser = { id: args.parser };

    const response = await fetch(`${OLOSTEP_API_URL}/batches`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = (await response.json()) as Record<string, unknown>;
    const batchId = (data.id || data.batch_id) as string | undefined;

    const waitSeconds = args.wait_for_completion_seconds ?? 0;
    if (waitSeconds > 0 && batchId) {
        const pollIntervalMs = 10_000;
        const deadline = Date.now() + waitSeconds * 1000;

        while (Date.now() < deadline) {
            await new Promise((r) => setTimeout(r, pollIntervalMs));

            const statusRes = await fetch(
                `${OLOSTEP_API_URL}/batches/${encodeURIComponent(batchId)}`,
                { method: 'GET', headers },
            );
            if (!statusRes.ok) break;

            const statusData = (await statusRes.json()) as Record<string, unknown>;
            const status = String(statusData.status || '').toLowerCase();

            if (status === 'completed' || status === 'failed') {
                return jsonResult({
                    ...statusData,
                    message: status === 'completed'
                        ? 'Batch completed. Call olostep_get_batch_results with this batch_id to retrieve scraped content.'
                        : 'Batch failed.',
                });
            }
        }

        return jsonResult({
            ...data,
            message: `Batch still processing after ${waitSeconds}s. Call olostep_get_batch_results with batch_id "${batchId}" to check again later.`,
        });
    }

    return jsonResult({
        ...data,
        message: `Batch created. Call olostep_get_batch_results with batch_id "${batchId}" to retrieve results once completed (~5-8 min).`,
    });
}

async function handleGetBatchResults(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const headers = apiHeaders(apiKey);
    const batchId = args.batch_id as string;

    const statusRes = await fetch(
        `${OLOSTEP_API_URL}/batches/${encodeURIComponent(batchId)}`,
        { method: 'GET', headers },
    );

    if (!statusRes.ok) return errorResult(await parseApiError(statusRes));

    const status = (await statusRes.json()) as Record<string, unknown>;
    const batchStatus = String(status.status || '').toLowerCase();

    if (batchStatus !== 'completed') {
        return jsonResult({
            batch_id: status.id || status.batch_id,
            status: status.status,
            total_urls: status.total_urls,
            completed_urls: status.completed_urls,
            message: `Batch is still ${status.status}. Call olostep_get_batch_results again in ~10 seconds.`,
        });
    }

    const limit = args.items_limit ?? 20;
    const itemsRes = await fetch(
        `${OLOSTEP_API_URL}/batches/${encodeURIComponent(batchId)}/items?cursor=0&limit=${limit}`,
        { method: 'GET', headers },
    );

    if (!itemsRes.ok) {
        return jsonResult({
            batch_id: status.id || status.batch_id,
            status: 'completed',
            message: 'Batch completed but failed to fetch items.',
        });
    }

    const itemsData = (await itemsRes.json()) as { items?: { custom_id?: string; url?: string; retrieve_id?: string }[]; cursor?: number };
    const items = itemsData.items ?? [];

    const retrieveFormats = (args.formats && args.formats.length > 0) ? args.formats as string[] : ['markdown'];
    const formatsParam = retrieveFormats.map((f: string) => `formats[]=${encodeURIComponent(f)}`).join('&');

    const results = await Promise.all(
        items.map(async (item) => {
            if (!item.retrieve_id) {
                return { custom_id: item.custom_id, url: item.url, error: 'No retrieve_id' };
            }
            try {
                const retrieveRes = await fetch(
                    `${OLOSTEP_API_URL}/retrieve?retrieve_id=${encodeURIComponent(item.retrieve_id)}&${formatsParam}`,
                    { method: 'GET', headers },
                );
                if (!retrieveRes.ok) {
                    return { custom_id: item.custom_id, url: item.url, error: `Retrieve failed: ${retrieveRes.status}` };
                }
                const content = (await retrieveRes.json()) as Record<string, unknown>;
                const result: Record<string, unknown> = {
                    custom_id: item.custom_id,
                    url: item.url,
                };
                if (content.markdown_content) result.markdown_content = content.markdown_content;
                if (content.html_content) result.html_content = content.html_content;
                if (content.json_content) result.json_content = content.json_content;
                if (content.text_content) result.text_content = content.text_content;
                return result;
            } catch {
                return { custom_id: item.custom_id, url: item.url, error: 'Retrieve request failed' };
            }
        }),
    );

    return jsonResult({
        batch_id: status.id || status.batch_id,
        status: 'completed',
        total_urls: status.total_urls,
        items_returned: results.length,
        has_more: itemsData.cursor !== undefined,
        items: results,
    });
}

async function handleCreateCrawl(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const orbitKey = getOrbitKey();
    const headers = apiHeaders(apiKey);

    const formats: string[] = [args.output_format || 'markdown'];
    const payload: Record<string, unknown> = {
        start_url: args.start_url,
        max_pages: args.max_pages ?? 10,
        follow_links: args.follow_links ?? true,
        formats,
    };
    if (args.country) payload.country = args.country;
    if (orbitKey) payload.force_connection_id = orbitKey;
    if (args.parser) payload.parser_extract = { parser_id: args.parser };

    const response = await fetch(`${OLOSTEP_API_URL}/crawls`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = await response.json();
    return jsonResult(data);
}

async function handleCreateMap(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const headers = apiHeaders(apiKey);

    const payload: Record<string, unknown> = {
        url: args.website_url,
    };
    if (args.search_query) payload.search_query = args.search_query;
    if (typeof args.top_n === 'number') payload.top_n = args.top_n;
    if (args.include_url_patterns?.length) payload.include_url_patterns = args.include_url_patterns;
    if (args.exclude_url_patterns?.length) payload.exclude_url_patterns = args.exclude_url_patterns;

    const response = await fetch(`${OLOSTEP_API_URL}/maps`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = await response.json();
    return jsonResult(data);
}

async function handleGetWebpageContent(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const orbitKey = getOrbitKey();
    const headers = apiHeaders(apiKey);

    const payload = {
        url_to_scrape: args.url_to_scrape,
        wait_before_scraping: args.wait_before_scraping ?? 0,
        formats: ['markdown'],
        ...(args.country && { country: args.country }),
        ...(orbitKey && { force_connection_id: orbitKey }),
    };

    const response = await fetch(`${OLOSTEP_API_URL}/scrapes`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = (await response.json()) as { result?: { markdown_content?: string } };
    if (data.result?.markdown_content) {
        return textResult(data.result.markdown_content);
    }
    return errorResult('Error: No markdown content found in Olostep API response.');
}

async function handleGetWebsiteUrls(args: any): Promise<ToolResult> {
    const apiKey = getApiKey();
    const headers = apiHeaders(apiKey);

    const payload = {
        url: args.url,
        search_query: args.search_query,
        top_n: 100,
    };

    const response = await fetch(`${OLOSTEP_API_URL}/maps`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
    });

    if (!response.ok) return errorResult(await parseApiError(response));

    const data = (await response.json()) as { urls_count?: number; urls?: string[] };
    if (data.urls && data.urls.length > 0) {
        return textResult(`Found ${data.urls_count} URLs matching your query:\n\n${data.urls.join('\n')}`);
    }
    return textResult('No URLs found matching your search query.');
}

// =============================================================================
// MCP SERVER FACTORY
// =============================================================================

const getOlostepMcpServer = () => {
    const server = new Server(
        {
            name: 'olostep-mcp-server',
            version: '1.0.0',
        },
        {
            capabilities: {
                tools: {},
            },
        }
    );

    server.setRequestHandler(ListToolsRequestSchema, async () => {
        return { tools: ALL_TOOLS };
    });

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;

        try {
            switch (name) {
                case 'olostep_scrape_website':
                    return await handleScrapeWebsite(args);
                case 'olostep_search_web':
                    return await handleSearchWeb(args);
                case 'olostep_answers':
                    return await handleAnswers(args);
                case 'olostep_batch_scrape_urls':
                    return await handleBatchScrapeUrls(args);
                case 'olostep_get_batch_results':
                    return await handleGetBatchResults(args);
                case 'olostep_create_crawl':
                    return await handleCreateCrawl(args);
                case 'olostep_create_map':
                    return await handleCreateMap(args);
                case 'olostep_get_webpage_content':
                    return await handleGetWebpageContent(args);
                case 'olostep_get_website_urls':
                    return await handleGetWebsiteUrls(args);
                default:
                    return errorResult(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            console.error(`Tool ${name} failed:`, error.message);
            return errorResult(`Error: ${error.message}`);
        }
    });

    return server;
};

// =============================================================================
// EXPRESS APP & TRANSPORTS
// =============================================================================

const app = express();

// Health check
app.get('/health', (_req: Request, res: Response) => {
    res.json({ status: 'ok' });
});

// =============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
// =============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const credentials = extractCredentials(req);

    const server = getOlostepMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run(credentials, async () => {
            await transport.handleRequest(req, res, req.body);
        });
        res.on('close', () => {
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

app.get('/mcp', async (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: {
            code: -32000,
            message: 'Method not allowed.',
        },
        id: null,
    }));
});

app.delete('/mcp', async (_req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: '2.0',
        error: {
            code: -32000,
            message: 'Method not allowed.',
        },
        id: null,
    }));
});

// =============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
// =============================================================================

const transports = new Map<string, SSEServerTransport>();

app.get('/sse', async (_req, res) => {
    const transport = new SSEServerTransport('/messages', res);

    res.on('close', async () => {
        transports.delete(transport.sessionId);
    });

    transports.set(transport.sessionId, transport);

    const server = getOlostepMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established: ${transport.sessionId}`);
});

app.post('/messages', async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);

    if (transport) {
        const credentials = extractCredentials(req);

        asyncLocalStorage.run(credentials, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        res.status(404).send({ error: 'Transport not found' });
    }
});

// =============================================================================
// START SERVER
// =============================================================================

const args = process.argv.slice(2);

if (args.includes('--stdio')) {
    // Stdio transport for Claude Desktop and similar clients
    const server = getOlostepMcpServer();
    const transport = new StdioServerTransport();

    // Extract credentials from env for stdio mode
    const apiKey = process.env.OLOSTEP_API_KEY || '';
    if (!apiKey) {
        console.error('OLOSTEP_API_KEY environment variable is required for stdio mode.');
        process.exit(1);
    }

    // Set AsyncLocalStorage context for all stdio requests
    asyncLocalStorage.enterWith({ apiKey, orbitKey: undefined });

    server.connect(transport).then(() => {
        console.error('Olostep MCP server running on stdio');
    });
} else {
    // HTTP transport (StreamableHTTP + SSE)
    const port = parseInt(process.env.PORT || '5000', 10);

    app.listen(port, () => {
        console.log(`Olostep MCP server running on port ${port}`);
    });
}
