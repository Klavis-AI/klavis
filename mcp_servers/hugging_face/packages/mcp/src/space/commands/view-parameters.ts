import type { ToolResult } from '../../types/tool-result.js';
import type { Tool } from '@modelcontextprotocol/sdk/types.js';
import { analyzeSchemaComplexity } from '../utils/schema-validator.js';
import { formatParameters, formatComplexSchemaError } from '../utils/parameter-formatter.js';

/**
 * Fetches space metadata and schema to discover parameters
 */
export async function viewParameters(spaceName: string, hfToken?: string): Promise<ToolResult> {
	try {
		// Step 1: Fetch space metadata to get subdomain
		const metadata = await fetchSpaceMetadata(spaceName, hfToken);

		// Step 2: Fetch schema from Gradio endpoint
		const tools = await fetchGradioSchema(metadata.subdomain, metadata.private, hfToken);

		// For simplicity, we'll work with the first tool
		// (most Gradio spaces expose a single primary tool)
		if (tools.length === 0) {
			return {
				formatted: `Error: No tools found for space '${spaceName}'.`,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		const tool = tools[0] as Tool;

		// Step 3: Analyze schema complexity
		const schemaResult = analyzeSchemaComplexity(tool);

		if (!schemaResult.isSimple) {
			return {
				formatted: formatComplexSchemaError(spaceName, schemaResult.reason || 'Unknown reason'),
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		// Step 4: Format parameters for display
		const formatted = formatParameters(schemaResult, spaceName);

		return {
			formatted,
			totalResults: schemaResult.parameters.length,
			resultsShared: schemaResult.parameters.length,
		};
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);

		// Check if this is a 404 error (space not found)
		const is404 = errorMessage.includes('404') || errorMessage.toLowerCase().includes('not found');

		let formattedError = `Error fetching parameters for space '${spaceName}': ${errorMessage}`;

		if (is404) {
			formattedError += '\n\nNote: The space MUST be an MCP enabled space. Use the `space_search` tool to find MCP enabled spaces.';
		}

		return {
			formatted: formattedError,
			totalResults: 0,
			resultsShared: 0,
			isError: true,
		};
	}
}

/**
 * Fetches space metadata from HuggingFace API
 */
async function fetchSpaceMetadata(
	spaceName: string,
	hfToken?: string
): Promise<{ subdomain: string; private: boolean }> {
	const url = `https://huggingface.co/api/spaces/${spaceName}`;
	const headers: Record<string, string> = {};

	if (hfToken) {
		headers['Authorization'] = `Bearer ${hfToken}`;
	}

	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 10000);

	try {
		const response = await fetch(url, {
			headers,
			signal: controller.signal,
		});

		clearTimeout(timeoutId);

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const info = (await response.json()) as {
			subdomain?: string;
			private?: boolean;
		};

		if (!info.subdomain) {
			throw new Error('Space does not have a subdomain');
		}

		return {
			subdomain: info.subdomain,
			private: info.private || false,
		};
	} finally {
		clearTimeout(timeoutId);
	}
}

/**
 * Fetches schema from Gradio endpoint
 */
async function fetchGradioSchema(subdomain: string, isPrivate: boolean, hfToken?: string): Promise<Tool[]> {
	const schemaUrl = `https://${subdomain}.hf.space/gradio_api/mcp/schema`;

	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
	};

	if (isPrivate && hfToken) {
		headers['X-HF-Authorization'] = `Bearer ${hfToken}`;
	}

	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), 10000);

	try {
		const response = await fetch(schemaUrl, {
			method: 'GET',
			headers,
			signal: controller.signal,
		});

		clearTimeout(timeoutId);

		if (!response.ok) {
			throw new Error(`HTTP ${response.status}: ${response.statusText}`);
		}

		const schemaResponse = (await response.json()) as unknown;

		// Parse schema response (handle both array and object formats)
		return parseSchemaResponse(schemaResponse);
	} finally {
		clearTimeout(timeoutId);
	}
}

/**
 * Parses schema response and extracts tools
 */
function parseSchemaResponse(schemaResponse: unknown): Tool[] {
	const tools: Tool[] = [];

	if (Array.isArray(schemaResponse)) {
		// Array format: [{ name: "toolName", description: "...", inputSchema: {...} }, ...]
		for (const item of schemaResponse) {
			if (
				typeof item === 'object' &&
				item !== null &&
				'name' in item &&
				'inputSchema' in item
			) {
				const itemRecord = item as Record<string, unknown>;
				if (typeof itemRecord.name === 'string') {
					const tool = itemRecord as { name: string; description?: string; inputSchema: unknown };
					tools.push({
						name: tool.name,
						description: tool.description || `${tool.name} tool`,
						inputSchema: {
							type: 'object',
							...(tool.inputSchema as Record<string, unknown>),
						},
					});
				}
			}
		}
	} else if (typeof schemaResponse === 'object' && schemaResponse !== null) {
		// Object format: { "toolName": { properties: {...}, required: [...] }, ... }
		for (const [name, toolSchema] of Object.entries(schemaResponse)) {
			if (typeof toolSchema === 'object' && toolSchema !== null) {
				const schema = toolSchema as { description?: string };
				tools.push({
					name,
					description: schema.description || `${name} tool`,
					inputSchema: {
						type: 'object',
						...(toolSchema as Record<string, unknown>),
					},
				});
			}
		}
	}

	return tools.filter((tool) => !tool.name.toLowerCase().includes('<lambda'));
}
