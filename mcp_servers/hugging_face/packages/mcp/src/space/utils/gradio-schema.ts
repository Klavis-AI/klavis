import type { Tool } from '@modelcontextprotocol/sdk/types.js';

export type ParsedSchemaFormat = 'array' | 'object';

export interface ParsedGradioSchema {
	format: ParsedSchemaFormat;
	tools: Array<{ name: string; description?: string; inputSchema: unknown }>;
}

/**
 * Parse a Gradio MCP schema that may be returned as either:
 * - Array format: [{ name, description?, inputSchema }, ...]
 * - Object format: { toolName: { properties, required, description?, ... }, ... }
 *
 * Returns a normalized list of tools and the detected format.
 * Throws if the schema is invalid or empty.
 */
export function parseGradioSchemaResponse(schemaResponse: unknown): ParsedGradioSchema {
	// Array format
	if (Array.isArray(schemaResponse)) {
		const tools = (schemaResponse as Array<unknown>).filter((tool): tool is { name: string; description?: string; inputSchema: unknown } => {
			return (
				typeof tool === 'object' &&
				tool !== null &&
				'name' in tool &&
				typeof (tool as { name?: unknown }).name === 'string' &&
				'inputSchema' in tool
			);
		});

		if (tools.length === 0) {
			throw new Error('Invalid schema: no tools found in array schema');
		}

		return {
			format: 'array',
			tools,
		};
	}

	// Object format
	if (typeof schemaResponse === 'object' && schemaResponse !== null) {
		const entries = Object.entries(schemaResponse as Record<string, unknown>);
		const tools: ParsedGradioSchema['tools'] = entries.map(([name, toolSchema]) => ({
			name,
			description: typeof (toolSchema as { description?: unknown }).description === 'string' ? (toolSchema as { description?: string }).description : undefined,
			inputSchema: toolSchema,
		}));

		if (tools.length === 0) {
			throw new Error('Invalid schema: no tools found in object schema');
		}

		return {
			format: 'object',
			tools,
		};
	}

	throw new Error('Invalid schema format: expected array or object');
}

/**
 * Convert ParsedGradioSchema.tools into SDK Tool[] shape, filtering out <lambda tools.
 */
export function normalizeParsedTools(parsed: ParsedGradioSchema): Tool[] {
	return parsed.tools
		.filter((t) => !t.name.toLowerCase().includes('<lambda'))
		.map((parsedTool) => ({
			name: parsedTool.name,
			description: parsedTool.description || `${parsedTool.name} tool`,
			inputSchema: parsedTool.inputSchema as Tool['inputSchema'],
		}));
}
