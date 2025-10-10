import express, { Request, Response } from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    Tool,
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import FirecrawlApp, {
    type ScrapeParams,
    type MapParams,
    type CrawlParams,
    type FirecrawlDocument,
} from '@mendable/firecrawl-js';
import PQueue from 'p-queue';
import { AsyncLocalStorage } from 'async_hooks';

import dotenv from 'dotenv';

dotenv.config();

// Added: Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    firecrawlClient: FirecrawlApp;
}>();

// Added: Getter function for the client
function getFirecrawlClient() {
    const store = asyncLocalStorage.getStore();
    if (!store) {
        throw new Error('Firecrawl client not found in AsyncLocalStorage');
    }
    return store.firecrawlClient;
}

// Tool definitions
const SCRAPE_TOOL: Tool = {
    name: 'firecrawl_scrape',
    description:
        'Scrape a single webpage with advanced options for content extraction. ' +
        'Supports various formats including markdown, HTML, and screenshots. ' +
        'Can execute custom actions like clicking or scrolling before scraping.',
    inputSchema: {
        type: 'object',
        properties: {
            url: {
                type: 'string',
                description: 'The URL to scrape',
            },
            formats: {
                type: 'array',
                items: {
                    type: 'string',
                    enum: [
                        'markdown',
                        'html',
                        'rawHtml',
                        'screenshot',
                        'links',
                        'screenshot@fullPage',
                        'extract',
                    ],
                },
                default: ['markdown'],
                description: "Content formats to extract (default: ['markdown'])",
            },
            onlyMainContent: {
                type: 'boolean',
                description:
                    'Extract only the main content, filtering out navigation, footers, etc.',
            },
            includeTags: {
                type: 'array',
                items: { type: 'string' },
                description: 'HTML tags to specifically include in extraction',
            },
            excludeTags: {
                type: 'array',
                items: { type: 'string' },
                description: 'HTML tags to exclude from extraction',
            },
            waitFor: {
                type: 'number',
                description: 'Time in milliseconds to wait for dynamic content to load',
            },
            timeout: {
                type: 'number',
                description:
                    'Maximum time in milliseconds to wait for the page to load',
            },
            actions: {
                type: 'array',
                items: {
                    type: 'object',
                    properties: {
                        type: {
                            type: 'string',
                            enum: [
                                'wait',
                                'click',
                                'screenshot',
                                'write',
                                'press',
                                'scroll',
                                'scrape',
                                'executeJavascript',
                            ],
                            description: 'Type of action to perform',
                        },
                        selector: {
                            type: 'string',
                            description: 'CSS selector for the target element',
                        },
                        milliseconds: {
                            type: 'number',
                            description: 'Time to wait in milliseconds (for wait action)',
                        },
                        text: {
                            type: 'string',
                            description: 'Text to write (for write action)',
                        },
                        key: {
                            type: 'string',
                            description: 'Key to press (for press action)',
                        },
                        direction: {
                            type: 'string',
                            enum: ['up', 'down'],
                            description: 'Scroll direction',
                        },
                        script: {
                            type: 'string',
                            description: 'JavaScript code to execute',
                        },
                        fullPage: {
                            type: 'boolean',
                            description: 'Take full page screenshot',
                        },
                    },
                    required: ['type'],
                },
                description: 'List of actions to perform before scraping',
            },
            extract: {
                type: 'object',
                properties: {
                    schema: {
                        type: 'object',
                        description: 'Schema for structured data extraction',
                    },
                    systemPrompt: {
                        type: 'string',
                        description: 'System prompt for LLM extraction',
                    },
                    prompt: {
                        type: 'string',
                        description: 'User prompt for LLM extraction',
                    },
                },
                description: 'Configuration for structured data extraction',
            },
            mobile: {
                type: 'boolean',
                description: 'Use mobile viewport',
            },
            skipTlsVerification: {
                type: 'boolean',
                description: 'Skip TLS certificate verification',
            },
            removeBase64Images: {
                type: 'boolean',
                description: 'Remove base64 encoded images from output',
            },
            location: {
                type: 'object',
                properties: {
                    country: {
                        type: 'string',
                        description: 'Country code for geolocation',
                    },
                    languages: {
                        type: 'array',
                        items: { type: 'string' },
                        description: 'Language codes for content',
                    },
                },
                description: 'Location settings for scraping',
            },
        },
        required: ['url'],
    },
    annotations: { category: 'FIRECRAWL_SEARCH', readOnlyHint: true },
};

const MAP_TOOL: Tool = {
    name: 'firecrawl_map',
    description:
        'Discover URLs from a starting point. Can use both sitemap.xml and HTML link discovery.',
    inputSchema: {
        type: 'object',
        properties: {
            url: {
                type: 'string',
                description: 'Starting URL for URL discovery',
            },
            search: {
                type: 'string',
                description: 'Optional search term to filter URLs',
            },
            ignoreSitemap: {
                type: 'boolean',
                description: 'Skip sitemap.xml discovery and only use HTML links',
            },
            sitemapOnly: {
                type: 'boolean',
                description: 'Only use sitemap.xml for discovery, ignore HTML links',
            },
            includeSubdomains: {
                type: 'boolean',
                description: 'Include URLs from subdomains in results',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of URLs to return',
            },
        },
        required: ['url'],
    },
    annotations: { category: 'FIRECRAWL_WEB_SEARCH', readOnlyHint: true },
};

const CRAWL_TOOL: Tool = {
    name: 'firecrawl_crawl',
    description:
        'Start an asynchronous crawl of multiple pages from a starting URL. ' +
        'Supports depth control, path filtering, and webhook notifications.',
    inputSchema: {
        type: 'object',
        properties: {
            url: {
                type: 'string',
                description: 'Starting URL for the crawl',
            },
            excludePaths: {
                type: 'array',
                items: { type: 'string' },
                description: 'URL paths to exclude from crawling',
            },
            includePaths: {
                type: 'array',
                items: { type: 'string' },
                description: 'Only crawl these URL paths',
            },
            maxDepth: {
                type: 'number',
                description: 'Maximum link depth to crawl',
            },
            ignoreSitemap: {
                type: 'boolean',
                description: 'Skip sitemap.xml discovery',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of pages to crawl',
            },
            allowBackwardLinks: {
                type: 'boolean',
                description: 'Allow crawling links that point to parent directories',
            },
            allowExternalLinks: {
                type: 'boolean',
                description: 'Allow crawling links to external domains',
            },
            webhook: {
                oneOf: [
                    {
                        type: 'string',
                        description: 'Webhook URL to notify when crawl is complete',
                    },
                    {
                        type: 'object',
                        properties: {
                            url: {
                                type: 'string',
                                description: 'Webhook URL',
                            },
                            headers: {
                                type: 'object',
                                description: 'Custom headers for webhook requests',
                            },
                        },
                        required: ['url'],
                    },
                ],
            },
            deduplicateSimilarURLs: {
                type: 'boolean',
                description: 'Remove similar URLs during crawl',
            },
            ignoreQueryParameters: {
                type: 'boolean',
                description: 'Ignore query parameters when comparing URLs',
            },
            scrapeOptions: {
                type: 'object',
                properties: {
                    formats: {
                        type: 'array',
                        items: {
                            type: 'string',
                            enum: [
                                'markdown',
                                'html',
                                'rawHtml',
                                'screenshot',
                                'links',
                                'screenshot@fullPage',
                                'extract',
                            ],
                        },
                    },
                    onlyMainContent: {
                        type: 'boolean',
                    },
                    includeTags: {
                        type: 'array',
                        items: { type: 'string' },
                    },
                    excludeTags: {
                        type: 'array',
                        items: { type: 'string' },
                    },
                    waitFor: {
                        type: 'number',
                    },
                },
                description: 'Options for scraping each page',
            },
        },
        required: ['url'],
    },
    annotations: { category: 'FIRECRAWL_WEB_SEARCH', readOnlyHint: true },
};

const BATCH_SCRAPE_TOOL: Tool = {
    name: 'firecrawl_batch_scrape',
    description:
        'Scrape multiple URLs in batch mode. Returns a job ID that can be used to check status.',
    inputSchema: {
        type: 'object',
        properties: {
            urls: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of URLs to scrape',
            },
            options: {
                type: 'object',
                properties: {
                    formats: {
                        type: 'array',
                        items: {
                            type: 'string',
                            enum: [
                                'markdown',
                                'html',
                                'rawHtml',
                                'screenshot',
                                'links',
                                'screenshot@fullPage',
                                'extract',
                            ],
                        },
                    },
                    onlyMainContent: {
                        type: 'boolean',
                    },
                    includeTags: {
                        type: 'array',
                        items: { type: 'string' },
                    },
                    excludeTags: {
                        type: 'array',
                        items: { type: 'string' },
                    },
                    waitFor: {
                        type: 'number',
                    },
                },
            },
        },
        required: ['urls'],
    },
    annotations: { category: 'FIRECRAWL_WEB_SEARCH', readOnlyHint: true },
};

const CHECK_BATCH_STATUS_TOOL: Tool = {
    name: 'firecrawl_check_batch_status',
    description: 'Check the status of a batch scraping job.',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'string',
                description: 'Batch job ID to check',
            },
        },
        required: ['id'],
    },
    annotations: { category: 'FIRECRAWL_METADATA', readOnlyHint: true },
};

const CHECK_CRAWL_STATUS_TOOL: Tool = {
    name: 'firecrawl_check_crawl_status',
    description: 'Check the status of a crawl job.',
    inputSchema: {
        type: 'object',
        properties: {
            id: {
                type: 'string',
                description: 'Crawl job ID to check',
            },
        },
        required: ['id'],
    },
    annotations: { category: 'FIRECRAWL_METADATA', readOnlyHint: true },
};

const SEARCH_TOOL: Tool = {
    name: 'firecrawl_search',
    description:
        'Search and retrieve content from web pages with optional scraping. ' +
        'Returns SERP results by default (url, title, description) or full page content when scrapeOptions are provided.',
    inputSchema: {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'Search query string',
            },
            limit: {
                type: 'number',
                description: 'Maximum number of results to return (default: 5)',
            },
            lang: {
                type: 'string',
                description: 'Language code for search results (default: en)',
            },
            country: {
                type: 'string',
                description: 'Country code for search results (default: us)',
            },
            tbs: {
                type: 'string',
                description: 'Time-based search filter',
            },
            filter: {
                type: 'string',
                description: 'Search filter',
            },
            location: {
                type: 'object',
                properties: {
                    country: {
                        type: 'string',
                        description: 'Country code for geolocation',
                    },
                    languages: {
                        type: 'array',
                        items: { type: 'string' },
                        description: 'Language codes for content',
                    },
                },
                description: 'Location settings for search',
            },
            scrapeOptions: {
                type: 'object',
                properties: {
                    formats: {
                        type: 'array',
                        items: {
                            type: 'string',
                            enum: ['markdown', 'html', 'rawHtml'],
                        },
                        description: 'Content formats to extract from search results',
                    },
                    onlyMainContent: {
                        type: 'boolean',
                        description: 'Extract only the main content from results',
                    },
                    waitFor: {
                        type: 'number',
                        description: 'Time in milliseconds to wait for dynamic content',
                    },
                },
                description: 'Options for scraping search results',
            },
        },
        required: ['query'],
    },
    annotations: { category: 'FIRECRAWL_WEB_SEARCH', readOnlyHint: true },
};

const EXTRACT_TOOL: Tool = {
    name: 'firecrawl_extract',
    description:
        'Extract structured information from web pages using LLM. ' +
        'Supports both cloud AI and self-hosted LLM extraction.',
    inputSchema: {
        type: 'object',
        properties: {
            urls: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of URLs to extract information from',
            },
            prompt: {
                type: 'string',
                description: 'Prompt for the LLM extraction',
            },
            systemPrompt: {
                type: 'string',
                description: 'System prompt for LLM extraction',
            },
            schema: {
                type: 'object',
                description: 'JSON schema for structured data extraction',
            },
            allowExternalLinks: {
                type: 'boolean',
                description: 'Allow extraction from external links',
            },
            enableWebSearch: {
                type: 'boolean',
                description: 'Enable web search for additional context',
            },
            includeSubdomains: {
                type: 'boolean',
                description: 'Include subdomains in extraction',
            },
        },
        required: ['urls'],
    },
    annotations: { category: 'FIRECRAWL_AI_SEARCH', readOnlyHint: true },
};

const GENERATE_LLMSTXT_TOOL: Tool = {
    name: 'firecrawl_generate_llmstxt',
    description:
        'Generate standardized LLMs.txt file for a given URL, which provides context about how LLMs should interact with the website.',
    inputSchema: {
        type: 'object',
        properties: {
            url: {
                type: 'string',
                description: 'The URL to generate LLMs.txt from',
            },
            maxUrls: {
                type: 'number',
                description: 'Maximum number of URLs to process (1-100, default: 10)',
            },
            showFullText: {
                type: 'boolean',
                description: 'Whether to show the full LLMs-full.txt in the response',
            },
        },
        required: ['url'],
    },
    annotations: { category: 'FIRECRAWL_AI_SEARCH', readOnlyHint: true },
};

// Type definitions
interface BatchScrapeOptions {
    urls: string[];
    options?: Omit<ScrapeParams, 'url'>;
}

/**
 * Parameters for LLMs.txt generation operations.
 */
interface GenerateLLMsTextParams {
    /**
     * Maximum number of URLs to process (1-100)
     * @default 10
     */
    maxUrls?: number;
    /**
     * Whether to show the full LLMs-full.txt in the response
     * @default false
     */
    showFullText?: boolean;
    /**
     * Experimental flag for streaming
     */
    __experimental_stream?: boolean;
}

/**
 * Response interface for LLMs.txt generation operations.
 */
// interface GenerateLLMsTextResponse {
//   success: boolean;
//   id: string;
// }

/**
 * Status response interface for LLMs.txt generation operations.
 */
// interface GenerateLLMsTextStatusResponse {
//   success: boolean;
//   data: {
//     llmstxt: string;
//     llmsfulltxt?: string;
//   };
//   status: 'processing' | 'completed' | 'failed';
//   error?: string;
//   expiresAt: string;
// }

interface StatusCheckOptions {
    id: string;
}

interface SearchOptions {
    query: string;
    limit?: number;
    lang?: string;
    country?: string;
    tbs?: string;
    filter?: string;
    location?: {
        country?: string;
        languages?: string[];
    };
    scrapeOptions?: {
        formats?: string[];
        onlyMainContent?: boolean;
        waitFor?: number;
        includeTags?: string[];
        excludeTags?: string[];
        timeout?: number;
    };
}

// Add after other interfaces
interface ExtractParams<T = any> {
    prompt?: string;
    systemPrompt?: string;
    schema?: T | object;
    allowExternalLinks?: boolean;
    enableWebSearch?: boolean;
    includeSubdomains?: boolean;
    origin?: string;
}

interface ExtractArgs {
    urls: string[];
    prompt?: string;
    systemPrompt?: string;
    schema?: object;
    allowExternalLinks?: boolean;
    enableWebSearch?: boolean;
    includeSubdomains?: boolean;
    origin?: string;
}

interface ExtractResponse<T = any> {
    success: boolean;
    data: T;
    error?: string;
    warning?: string;
    creditsUsed?: number;
}

// Type guards
function isScrapeOptions(
    args: unknown
): args is ScrapeParams & { url: string } {
    return (
        typeof args === 'object' &&
        args !== null &&
        'url' in args &&
        typeof (args as { url: unknown }).url === 'string'
    );
}

function isMapOptions(args: unknown): args is MapParams & { url: string } {
    return (
        typeof args === 'object' &&
        args !== null &&
        'url' in args &&
        typeof (args as { url: unknown }).url === 'string'
    );
}

function isCrawlOptions(args: unknown): args is CrawlParams & { url: string } {
    return (
        typeof args === 'object' &&
        args !== null &&
        'url' in args &&
        typeof (args as { url: unknown }).url === 'string'
    );
}

function isBatchScrapeOptions(args: unknown): args is BatchScrapeOptions {
    return (
        typeof args === 'object' &&
        args !== null &&
        'urls' in args &&
        Array.isArray((args as { urls: unknown }).urls) &&
        (args as { urls: unknown[] }).urls.every((url) => typeof url === 'string')
    );
}

function isStatusCheckOptions(args: unknown): args is StatusCheckOptions {
    return (
        typeof args === 'object' &&
        args !== null &&
        'id' in args &&
        typeof (args as { id: unknown }).id === 'string'
    );
}

function isSearchOptions(args: unknown): args is SearchOptions {
    return (
        typeof args === 'object' &&
        args !== null &&
        'query' in args &&
        typeof (args as { query: unknown }).query === 'string'
    );
}

function isExtractOptions(args: unknown): args is ExtractArgs {
    if (typeof args !== 'object' || args === null) return false;
    const { urls } = args as { urls?: unknown };
    return (
        Array.isArray(urls) &&
        urls.every((url): url is string => typeof url === 'string')
    );
}

function isGenerateLLMsTextOptions(
    args: unknown
): args is { url: string } & Partial<GenerateLLMsTextParams> {
    return (
        typeof args === 'object' &&
        args !== null &&
        'url' in args &&
        typeof (args as { url: unknown }).url === 'string'
    );
}

// Get optional API URL
const FIRECRAWL_API_URL = process.env.FIRECRAWL_API_URL;

// Configuration for retries and monitoring
const CONFIG = {
    retry: {
        maxAttempts: Number(process.env.FIRECRAWL_RETRY_MAX_ATTEMPTS) || 3,
        initialDelay: Number(process.env.FIRECRAWL_RETRY_INITIAL_DELAY) || 1000,
        maxDelay: Number(process.env.FIRECRAWL_RETRY_MAX_DELAY) || 10000,
        backoffFactor: Number(process.env.FIRECRAWL_RETRY_BACKOFF_FACTOR) || 2,
    },
    credit: {
        warningThreshold:
            Number(process.env.FIRECRAWL_CREDIT_WARNING_THRESHOLD) || 1000,
        criticalThreshold:
            Number(process.env.FIRECRAWL_CREDIT_CRITICAL_THRESHOLD) || 100,
    },
};

// Add credit tracking
interface CreditUsage {
    total: number;
    lastCheck: number;
}

const creditUsage: CreditUsage = {
    total: 0,
    lastCheck: Date.now(),
};

// Add utility function for delay
function delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

let isStdioTransport = false;

function safeLog(
    level:
        | 'error'
        | 'debug'
        | 'info'
        | 'notice'
        | 'warning'
        | 'critical'
        | 'alert'
        | 'emergency',
    data: any
): void {
    if (isStdioTransport) {
        // For stdio transport, log to stderr to avoid protocol interference
        console.error(
            `[${level}] ${typeof data === 'object' ? JSON.stringify(data) : data}`
        );
    } else {
        // For other transport types, use the normal logging mechanism
        // server.sendLoggingMessage({ level, data });
    }
}

// Add retry logic with exponential backoff
async function withRetry<T>(
    operation: () => Promise<T>,
    context: string,
    attempt = 1
): Promise<T> {
    try {
        return await operation();
    } catch (error) {
        const isRateLimit =
            error instanceof Error &&
            (error.message.includes('rate limit') || error.message.includes('429'));

        if (isRateLimit && attempt < CONFIG.retry.maxAttempts) {
            const delayMs = Math.min(
                CONFIG.retry.initialDelay *
                Math.pow(CONFIG.retry.backoffFactor, attempt - 1),
                CONFIG.retry.maxDelay
            );

            safeLog(
                'warning',
                `Rate limit hit for ${context}. Attempt ${attempt}/${CONFIG.retry.maxAttempts}. Retrying in ${delayMs}ms`
            );

            await delay(delayMs);
            return withRetry(operation, context, attempt + 1);
        }

        throw error;
    }
}

// Add credit monitoring
async function updateCreditUsage(creditsUsed: number): Promise<void> {
    creditUsage.total += creditsUsed;

    // Log credit usage
    safeLog('info', `Credit usage: ${creditUsage.total} credits used total`);

    // Check thresholds
    if (creditUsage.total >= CONFIG.credit.criticalThreshold) {
        safeLog('error', `CRITICAL: Credit usage has reached ${creditUsage.total}`);
    } else if (creditUsage.total >= CONFIG.credit.warningThreshold) {
        safeLog(
            'warning',
            `WARNING: Credit usage has reached ${creditUsage.total}`
        );
    }
}

// Add before server implementation
interface QueuedBatchOperation {
    id: string;
    urls: string[];
    options?: any;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: {
        completed: number;
        total: number;
    };
    result?: any;
    error?: string;
}

// Initialize queue system
const batchQueue = new PQueue({ concurrency: 1 });
const batchOperations = new Map<string, QueuedBatchOperation>();
let operationCounter = 0;

async function processBatchOperation(
    operation: QueuedBatchOperation
): Promise<void> {
    const client = getFirecrawlClient();
    try {
        operation.status = 'processing';
        let totalCreditsUsed = 0;

        // Use library's built-in batch processing
        const response = await withRetry(
            async () =>
                client.asyncBatchScrapeUrls(operation.urls, operation.options),
            `batch ${operation.id} processing`
        );

        if (!response.success) {
            throw new Error(response.error || 'Batch operation failed');
        }

        // Track credits if using cloud API
        if (!FIRECRAWL_API_URL && hasCredits(response)) {
            totalCreditsUsed += response.creditsUsed;
            await updateCreditUsage(response.creditsUsed);
        }

        operation.status = 'completed';
        operation.result = response;

        // Log final credit usage for the batch
        if (!FIRECRAWL_API_URL) {
            safeLog(
                'info',
                `Batch ${operation.id} completed. Total credits used: ${totalCreditsUsed}`
            );
        }
    } catch (error) {
        operation.status = 'failed';
        operation.error = error instanceof Error ? error.message : String(error);

        safeLog('error', `Batch ${operation.id} failed: ${operation.error}`);
    }
}

const getFirecrawlMcpServer = () => {
    // Server implementation
    const server = new Server(
        {
            name: 'firecrawl-mcp',
            version: '1.7.0',
        },
        {
            capabilities: {
                tools: {},
                logging: {},
            },
        }
    );

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            SCRAPE_TOOL,
            MAP_TOOL,
            CRAWL_TOOL,
            BATCH_SCRAPE_TOOL,
            CHECK_BATCH_STATUS_TOOL,
            CHECK_CRAWL_STATUS_TOOL,
            SEARCH_TOOL,
            EXTRACT_TOOL,
            GENERATE_LLMSTXT_TOOL,
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const startTime = Date.now();
        try {
            const { name, arguments: args } = request.params;
            const client = getFirecrawlClient();

            // Log incoming request with timestamp
            safeLog(
                'info',
                `[${new Date().toISOString()}] Received request for tool: ${name}`
            );

            if (!args) {
                throw new Error('No arguments provided');
            }

            switch (name) {
                case 'firecrawl_scrape': {
                    if (!isScrapeOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_scrape');
                    }
                    const { url, ...options } = args;
                    try {
                        const scrapeStartTime = Date.now();
                        safeLog(
                            'info',
                            `Starting scrape for URL: ${url} with options: ${JSON.stringify(options)}`
                        );

                        const response = await client.scrapeUrl(url, {
                            ...options,
                            // @ts-expect-error Extended API options including origin
                            origin: 'mcp-server',
                        });

                        // Log performance metrics
                        safeLog(
                            'info',
                            `Scrape completed in ${Date.now() - scrapeStartTime}ms`
                        );

                        if ('success' in response && !response.success) {
                            throw new Error(response.error || 'Scraping failed');
                        }

                        // Format content based on requested formats
                        const contentParts = [];

                        if (options.formats?.includes('markdown') && response.markdown) {
                            contentParts.push(response.markdown);
                        }
                        if (options.formats?.includes('html') && response.html) {
                            contentParts.push(response.html);
                        }
                        if (options.formats?.includes('rawHtml') && response.rawHtml) {
                            contentParts.push(response.rawHtml);
                        }
                        if (options.formats?.includes('links') && response.links) {
                            contentParts.push(response.links.join('\n'));
                        }
                        if (options.formats?.includes('screenshot') && response.screenshot) {
                            contentParts.push(response.screenshot);
                        }
                        if (options.formats?.includes('extract') && response.extract) {
                            contentParts.push(JSON.stringify(response.extract, null, 2));
                        }

                        // If options.formats is empty, default to markdown
                        if (!options.formats || options.formats.length === 0) {
                            options.formats = ['markdown'];
                        }

                        // Add warning to response if present
                        if (response.warning) {
                            safeLog('warning', response.warning);
                        }

                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: trimResponseText(
                                        contentParts.join('\n\n') || 'No content available'
                                    ),
                                },
                            ],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage =
                            error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }

                case 'firecrawl_map': {
                    if (!isMapOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_map');
                    }
                    const { url, ...options } = args;
                    const response = await client.mapUrl(url, {
                        ...options,
                        // @ts-expect-error Extended API options including origin
                        origin: 'mcp-server',
                    });
                    if ('error' in response) {
                        throw new Error(response.error);
                    }
                    if (!response.links) {
                        throw new Error('No links received from Firecrawl API');
                    }
                    return {
                        content: [
                            { type: 'text', text: trimResponseText(response.links.join('\n')) },
                        ],
                        isError: false,
                    };
                }

                case 'firecrawl_batch_scrape': {
                    if (!isBatchScrapeOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_batch_scrape');
                    }

                    try {
                        const operationId = `batch_${++operationCounter}`;
                        const operation: QueuedBatchOperation = {
                            id: operationId,
                            urls: args.urls,
                            options: args.options,
                            status: 'pending',
                            progress: {
                                completed: 0,
                                total: args.urls.length,
                            },
                        };

                        batchOperations.set(operationId, operation);

                        // Queue the operation
                        batchQueue.add(() => processBatchOperation(operation));

                        safeLog(
                            'info',
                            `Queued batch operation ${operationId} with ${args.urls.length} URLs`
                        );

                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: trimResponseText(
                                        `Batch operation queued with ID: ${operationId}. Use firecrawl_check_batch_status to check progress.`
                                    ),
                                },
                            ],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage =
                            error instanceof Error
                                ? error.message
                                : `Batch operation failed: ${JSON.stringify(error)}`;
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }

                case 'firecrawl_check_batch_status': {
                    if (!isStatusCheckOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_check_batch_status');
                    }

                    const operation = batchOperations.get(args.id);
                    if (!operation) {
                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: trimResponseText(
                                        `No batch operation found with ID: ${args.id}`
                                    ),
                                },
                            ],
                            isError: true,
                        };
                    }

                    const status = `Batch Status:
    Status: ${operation.status}
    Progress: ${operation.progress.completed}/${operation.progress.total}
    ${operation.error ? `Error: ${operation.error}` : ''}
    ${operation.result
                            ? `Results: ${JSON.stringify(operation.result, null, 2)}`
                            : ''
                        }`;

                    return {
                        content: [{ type: 'text', text: trimResponseText(status) }],
                        isError: false,
                    };
                }

                case 'firecrawl_crawl': {
                    if (!isCrawlOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_crawl');
                    }
                    const { url, ...options } = args;
                    const response = await withRetry(
                        async () =>
                            // @ts-expect-error Extended API options including origin
                            client.asyncCrawlUrl(url, { ...options, origin: 'mcp-server' }),
                        'crawl operation'
                    );

                    if (!response.success) {
                        throw new Error(response.error);
                    }

                    // Monitor credits for cloud API
                    if (!FIRECRAWL_API_URL && hasCredits(response)) {
                        await updateCreditUsage(response.creditsUsed);
                    }

                    return {
                        content: [
                            {
                                type: 'text',
                                text: trimResponseText(
                                    `Started crawl for ${url} with job ID: ${response.id}`
                                ),
                            },
                        ],
                        isError: false,
                    };
                }

                case 'firecrawl_check_crawl_status': {
                    if (!isStatusCheckOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_check_crawl_status');
                    }
                    const response = await client.checkCrawlStatus(args.id);
                    if (!response.success) {
                        throw new Error(response.error);
                    }
                    const status = `Crawl Status:
    Status: ${response.status}
    Progress: ${response.completed}/${response.total}
    Credits Used: ${response.creditsUsed}
    Expires At: ${response.expiresAt}
    ${response.data.length > 0 ? '\nResults:\n' + formatResults(response.data) : ''
                        }`;
                    return {
                        content: [{ type: 'text', text: trimResponseText(status) }],
                        isError: false,
                    };
                }

                case 'firecrawl_search': {
                    if (!isSearchOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_search');
                    }
                    try {
                        const response = await withRetry(
                            async () =>
                                client.search(args.query, { ...args, origin: 'mcp-server' }),
                            'search operation'
                        );

                        if (!response.success) {
                            throw new Error(
                                `Search failed: ${response.error || 'Unknown error'}`
                            );
                        }

                        // Monitor credits for cloud API
                        if (!FIRECRAWL_API_URL && hasCredits(response)) {
                            await updateCreditUsage(response.creditsUsed);
                        }

                        // Format the results
                        const results = response.data
                            .map(
                                (result) =>
                                    `URL: ${result.url}
    Title: ${result.title || 'No title'}
    Description: ${result.description || 'No description'}
    ${result.markdown ? `\nContent:\n${result.markdown}` : ''}`
                            )
                            .join('\n\n');

                        return {
                            content: [{ type: 'text', text: trimResponseText(results) }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage =
                            error instanceof Error
                                ? error.message
                                : `Search failed: ${JSON.stringify(error)}`;
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }

                case 'firecrawl_extract': {
                    if (!isExtractOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_extract');
                    }

                    try {
                        const extractStartTime = Date.now();

                        safeLog(
                            'info',
                            `Starting extraction for URLs: ${args.urls.join(', ')}`
                        );

                        // Log if using self-hosted instance
                        if (FIRECRAWL_API_URL) {
                            safeLog('info', 'Using self-hosted instance for extraction');
                        }

                        const extractResponse = await withRetry(
                            async () =>
                                client.extract(args.urls, {
                                    prompt: args.prompt,
                                    systemPrompt: args.systemPrompt,
                                    schema: args.schema,
                                    allowExternalLinks: args.allowExternalLinks,
                                    enableWebSearch: args.enableWebSearch,
                                    includeSubdomains: args.includeSubdomains,
                                    origin: 'mcp-server',
                                } as ExtractParams),
                            'extract operation'
                        );

                        // Type guard for successful response
                        if (!('success' in extractResponse) || !extractResponse.success) {
                            throw new Error(extractResponse.error || 'Extraction failed');
                        }

                        const response = extractResponse as ExtractResponse;

                        // Monitor credits for cloud API
                        if (!FIRECRAWL_API_URL && hasCredits(response)) {
                            await updateCreditUsage(response.creditsUsed || 0);
                        }

                        // Log performance metrics
                        safeLog(
                            'info',
                            `Extraction completed in ${Date.now() - extractStartTime}ms`
                        );

                        // Add warning to response if present
                        const result = {
                            content: [
                                {
                                    type: 'text',
                                    text: trimResponseText(JSON.stringify(response.data, null, 2)),
                                },
                            ],
                            isError: false,
                        };

                        if (response.warning) {
                            safeLog('warning', response.warning);
                        }

                        return result;
                    } catch (error) {
                        const errorMessage =
                            error instanceof Error ? error.message : String(error);

                        // Special handling for self-hosted instance errors
                        if (
                            FIRECRAWL_API_URL &&
                            errorMessage.toLowerCase().includes('not supported')
                        ) {
                            safeLog(
                                'error',
                                'Extraction is not supported by this self-hosted instance'
                            );
                            return {
                                content: [
                                    {
                                        type: 'text',
                                        text: trimResponseText(
                                            'Extraction is not supported by this self-hosted instance. Please ensure LLM support is configured.'
                                        ),
                                    },
                                ],
                                isError: true,
                            };
                        }

                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }

                case 'firecrawl_generate_llmstxt': {
                    if (!isGenerateLLMsTextOptions(args)) {
                        throw new Error('Invalid arguments for firecrawl_generate_llmstxt');
                    }

                    try {
                        const { url, ...params } = args;
                        const generateStartTime = Date.now();

                        safeLog('info', `Starting LLMs.txt generation for URL: ${url}`);

                        // Start the generation process
                        const response = await withRetry(
                            async () =>
                                // @ts-expect-error Extended API options including origin
                                client.generateLLMsText(url, { ...params, origin: 'mcp-server' }),
                            'LLMs.txt generation'
                        );

                        if (!response.success) {
                            throw new Error(response.error || 'LLMs.txt generation failed');
                        }

                        // Log performance metrics
                        safeLog(
                            'info',
                            `LLMs.txt generation completed in ${Date.now() - generateStartTime}ms`
                        );

                        // Format the response
                        let resultText = '';

                        if ('data' in response) {
                            resultText = `LLMs.txt content:\n\n${response.data.llmstxt}`;

                            if (args.showFullText && response.data.llmsfulltxt) {
                                resultText += `\n\nLLMs-full.txt content:\n\n${response.data.llmsfulltxt}`;
                            }
                        }

                        return {
                            content: [{ type: 'text', text: trimResponseText(resultText) }],
                            isError: false,
                        };
                    } catch (error) {
                        const errorMessage =
                            error instanceof Error ? error.message : String(error);
                        return {
                            content: [{ type: 'text', text: trimResponseText(errorMessage) }],
                            isError: true,
                        };
                    }
                }

                default:
                    return {
                        content: [
                            { type: 'text', text: trimResponseText(`Unknown tool: ${name}`) },
                        ],
                        isError: true,
                    };
            }
        } catch (error) {
            // Log detailed error information
            safeLog('error', {
                message: `Request failed: ${error instanceof Error ? error.message : String(error)
                    }`,
                tool: request.params.name,
                arguments: request.params.arguments,
                timestamp: new Date().toISOString(),
                duration: Date.now() - startTime,
            });
            return {
                content: [
                    {
                        type: 'text',
                        text: trimResponseText(
                            `Error: ${error instanceof Error ? error.message : String(error)}`
                        ),
                    },
                ],
                isError: true,
            };
        } finally {
            // Log request completion with performance metrics
            safeLog('info', `Request completed in ${Date.now() - startTime}ms`);
        }
    });

    return server;
}

// Helper function to format results
function formatResults(data: FirecrawlDocument[]): string {
    return data
        .map((doc) => {
            const content = doc.markdown || doc.html || doc.rawHtml || 'No content';
            return `URL: ${doc.url || 'Unknown URL'}
Content: ${content.substring(0, 100)}${content.length > 100 ? '...' : ''}
${doc.metadata?.title ? `Title: ${doc.metadata.title}` : ''}`;
        })
        .join('\n\n');
}

// Add type guard for credit usage
function hasCredits(response: any): response is { creditsUsed: number } {
    return 'creditsUsed' in response && typeof response.creditsUsed === 'number';
}

// Utility function to trim trailing whitespace from text responses
// This prevents Claude API errors with "final assistant content cannot end with trailing whitespace"
function trimResponseText(text: string): string {
    return text.trim();
}

function extractApiKey(req: Request): string {
    let authData = process.env.API_KEY;
    
    if (authData) {
        return authData;
    }
    
    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data JSON:', error);
        }
    }

    if (!authData) {
        console.error('Error: Firecrawl API key is missing. Provide it via API_KEY env var or x-auth-data header with token field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.token ?? authDataJson.api_key ?? '';
}

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {

    // Added: Get API key from env or header
    const apiKey = extractApiKey(req);

    // Added: Instantiate client within request context
    const firecrawlClient = new FirecrawlApp({
        apiKey: apiKey || '', // Use empty string if only API URL is provided (self-hosted)
        ...(FIRECRAWL_API_URL ? { apiUrl: FIRECRAWL_API_URL } : {}),
    });    

    const server = getFirecrawlMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ firecrawlClient }, async () => {
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
    console.log('Received GET MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    console.log('Received DELETE MCP request');
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
    const transport = new SSEServerTransport(`/messages`, res);

    // Set up cleanup when connection closes
    res.on('close', async () => {
        console.log(`SSE connection closed for transport: ${transport.sessionId}`);
        try {
            transports.delete(transport.sessionId);
        } finally {
        }
    });

    transports.set(transport.sessionId, transport);

    const server = getFirecrawlMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    if (transport) {
        // Added: Get API key from env or header
        const apiKey = extractApiKey(req);

        // Added: Instantiate client within request context
        const firecrawlClient = new FirecrawlApp({
            apiKey: apiKey || '', // Use empty string if only API URL is provided (self-hosted)
            ...(FIRECRAWL_API_URL ? { apiUrl: FIRECRAWL_API_URL } : {}),
        });

        // Added: Run handler within AsyncLocalStorage context
        asyncLocalStorage.run({ firecrawlClient }, async () => {
            await transport.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

app.listen(5000, () => {
    console.log('server running on port 5000');
});