import { readFile } from 'node:fs/promises';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type { Tool } from '@modelcontextprotocol/sdk/types.js';
import { logger } from './logger.js';

export type ProxyToolResponseType = 'JSON' | 'SSE';

export interface ProxyToolSource {
	proxyId: string;
	url: string;
	responseType: ProxyToolResponseType;
}

export interface ProxyToolDefinition {
	proxyId: string;
	toolName: string;
	upstreamToolName: string;
	url: string;
	responseType: ProxyToolResponseType;
	description?: string;
	inputSchema?: ProxyToolInputSchema;
}

export interface ProxyToolInputSchema {
	type?: string;
	properties?: Record<string, ProxyToolSchemaProperty>;
	required?: string[];
	[key: string]: unknown;
}

export interface ProxyToolSchemaProperty {
	type?: string;
	description?: string;
	default?: unknown;
	enum?: unknown[];
	[key: string]: unknown;
}

const PROXY_TOOLS_ENV_VAR = 'PROXY_TOOLS_CSV';
const VALID_RESPONSE_TYPES = new Set<ProxyToolResponseType>(['JSON', 'SSE']);
const PROXY_SCHEMA_TIMEOUT_MS = 10_000;

let cachedTools: ProxyToolDefinition[] | null = null;
let cachedConfigPromise: Promise<ProxyToolDefinition[]> | null = null;
let cachedToolsByName: Map<string, ProxyToolDefinition> = new Map();

export function getProxyToolsConfig(): ProxyToolDefinition[] {
	return cachedTools ?? [];
}

export function getProxyToolDefinition(toolName: string): ProxyToolDefinition | undefined {
	return cachedToolsByName.get(toolName);
}

export async function loadProxyToolsConfig(): Promise<ProxyToolDefinition[]> {
	if (cachedTools) {
		return cachedTools;
	}
	if (cachedConfigPromise) {
		return cachedConfigPromise;
	}

	cachedConfigPromise = (async () => {
		const source = process.env[PROXY_TOOLS_ENV_VAR]?.trim();
		if (!source) {
			cachedTools = [];
			cachedToolsByName = new Map();
			logger.debug({ envVar: PROXY_TOOLS_ENV_VAR }, 'Proxy tools CSV not configured');
			return cachedTools;
		}

		let content: string | null = null;
		if (source.startsWith('https://')) {
			try {
				const response = await fetch(source);
				if (!response.ok) {
					logger.error(
						{ status: response.status, source },
						'Failed to fetch proxy tools CSV'
					);
					cachedTools = [];
					cachedToolsByName = new Map();
					return cachedTools;
				}
				content = await response.text();
			} catch (error) {
				logger.error({ error, source }, 'Error fetching proxy tools CSV');
				cachedTools = [];
				cachedToolsByName = new Map();
				return cachedTools;
			}
		} else {
			try {
				content = await readFile(source, 'utf8');
			} catch (error) {
				logger.error({ error, source }, 'Proxy tools CSV file not found');
				cachedTools = [];
				cachedToolsByName = new Map();
				return cachedTools;
			}
		}

		const parsedSources = parseProxyToolsCsv(content);
		const toolDefinitions = await loadProxyToolSchemas(parsedSources);
		if (parsedSources.length > 0 && toolDefinitions.length === 0) {
			logger.error('Proxy tools configured but no tool schemas were loaded');
		}
		cachedTools = toolDefinitions;
		cachedToolsByName = new Map(toolDefinitions.map((entry) => [entry.toolName, entry]));
		logger.info({ toolCount: toolDefinitions.length }, 'Loaded proxy tools configuration');
		return toolDefinitions;
	})();

	return cachedConfigPromise;
}

async function loadProxyToolSchemas(sources: ProxyToolSource[]): Promise<ProxyToolDefinition[]> {
	if (sources.length === 0) {
		return [];
	}

	const shouldPrefix = sources.length > 1;
	const hfToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;
	const schemaTasks = sources.map((source) =>
		Promise.race([
			fetchProxyToolSchemas(source, shouldPrefix, hfToken),
			createTimeout(PROXY_SCHEMA_TIMEOUT_MS),
		])
			.then((tools) => ({ source, tools }))
			.catch((error: unknown) => {
				logger.error(
					{ error, proxyId: source.proxyId, url: source.url },
					'Failed to fetch proxy tool schemas'
				);
				return { source, tools: [] as ProxyToolDefinition[] };
			})
	);

	const results = await Promise.all(schemaTasks);
	return results.flatMap((result) => result.tools);
}

async function fetchProxyToolSchemas(
	source: ProxyToolSource,
	shouldPrefix: boolean,
	hfToken: string | undefined
): Promise<ProxyToolDefinition[]> {
	const client = new Client(
		{
			name: 'hf-mcp-proxy-loader',
			version: '1.0.0',
		},
		{ capabilities: {} }
	);

	const headers = buildAuthHeaders(hfToken);
	const transport = new StreamableHTTPClientTransport(new URL(source.url), {
		requestInit: headers ? { headers } : undefined,
	});

	try {
		await client.connect(transport, { timeout: PROXY_SCHEMA_TIMEOUT_MS });
		const result = await client.listTools({}, { timeout: PROXY_SCHEMA_TIMEOUT_MS });
		const tools = result.tools || [];

		if (tools.length === 0) {
			logger.error(
				{ proxyId: source.proxyId, url: source.url },
				'No tools returned from proxy server'
			);
			return [];
		}

		return tools
			.map((tool) => buildProxyToolDefinition(source, tool, shouldPrefix))
			.filter((tool): tool is ProxyToolDefinition => Boolean(tool));
	} catch (error) {
		logger.error({ error, proxyId: source.proxyId, url: source.url }, 'Proxy tool schema fetch failed');
		return [];
	} finally {
		try {
			await client.close();
		} catch (error) {
			logger.debug({ error, proxyId: source.proxyId, url: source.url }, 'Failed to close proxy tool client');
		}
	}
}

function buildProxyToolDefinition(
	source: ProxyToolSource,
	tool: Tool,
	shouldPrefix: boolean
): ProxyToolDefinition | null {
	const outwardName = shouldPrefix ? `${source.proxyId}_${tool.name}` : tool.name;
	const inputSchema = tool.inputSchema as ProxyToolInputSchema | undefined;
	if (!inputSchema || inputSchema.type !== 'object') {
		logger.error(
			{ proxyId: source.proxyId, toolName: tool.name },
			'Proxy tool schema missing or invalid'
		);
		return null;
	}

	return {
		proxyId: source.proxyId,
		toolName: outwardName,
		upstreamToolName: tool.name,
		url: source.url,
		responseType: source.responseType,
		description: tool.description,
		inputSchema,
	};
}

function buildAuthHeaders(hfToken?: string): Record<string, string> | undefined {
	if (!hfToken) {
		return undefined;
	}

	return {
		Authorization: `Bearer ${hfToken}`,
		'X-HF-Authorization': `Bearer ${hfToken}`,
	};
}

function createTimeout(ms: number): Promise<never> {
	return new Promise((_, reject) => {
		setTimeout(() => {
			reject(new Error(`Connection timeout after ${ms.toString()}ms`));
		}, ms);
	});
}

function parseProxyToolsCsv(content: string): ProxyToolSource[] {
	const lines = content.split(/\r?\n/);
	const results: ProxyToolSource[] = [];
	const seen = new Set<string>();

	for (const rawLine of lines) {
		const line = rawLine.trim();
		if (!line || line.startsWith('#')) {
			continue;
		}

		const fields = parseCsvLine(line);
		if (fields.length < 3) {
			logger.warn({ line }, 'Skipping proxy tools CSV row with insufficient fields');
			continue;
		}

		const [proxyIdRaw, urlRaw, responseTypeRaw] = fields;
		if (!proxyIdRaw || !urlRaw || !responseTypeRaw) {
			logger.warn({ line }, 'Skipping proxy tools CSV row with missing values');
			continue;
		}

		const proxyId = proxyIdRaw.trim();
		if (proxyId.toLowerCase() === 'proxy_id') {
			continue;
		}

		if (seen.has(proxyId)) {
			logger.warn({ proxyId }, 'Duplicate proxy id encountered, skipping');
			continue;
		}

		const url = urlRaw.trim();
		let parsedUrl: URL;
		try {
			parsedUrl = new URL(url);
			if (parsedUrl.protocol !== 'https:' && parsedUrl.protocol !== 'http:') {
				logger.warn({ proxyId, url }, 'Skipping proxy tool with unsupported URL protocol');
				continue;
			}
		} catch (error) {
			logger.warn({ proxyId, url, error }, 'Skipping proxy tool with invalid URL');
			continue;
		}

		const responseType = responseTypeRaw.trim().toUpperCase() as ProxyToolResponseType;
		if (!VALID_RESPONSE_TYPES.has(responseType)) {
			logger.warn({ proxyId, responseType }, 'Skipping proxy tool with invalid response_type');
			continue;
		}

		results.push({
			proxyId,
			url: parsedUrl.toString(),
			responseType,
		});
		seen.add(proxyId);
	}

	return results;
}

function parseCsvLine(line: string): string[] {
	const fields: string[] = [];
	let current = '';
	let inQuotes = false;

	for (let i = 0; i < line.length; i += 1) {
		const char = line[i];
		if (char === '"') {
			if (inQuotes && line[i + 1] === '"') {
				current += '"';
				i += 1;
				continue;
			}
			inQuotes = !inQuotes;
			continue;
		}

		if (char === ',' && !inQuotes) {
			fields.push(current.trim());
			current = '';
			continue;
		}

		current += char;
	}

	if (current.length > 0) {
		fields.push(current.trim());
	}

	return fields;
}
