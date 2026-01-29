import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';

/**
 * Formats tool result for user-friendly display
 * Handles different content types:
 * - Text content (primary)
 * - Image content (with descriptions)
 * - Resource content (with URIs)
 * - Error results
 */
export function formatToolResult(result: CallToolResult): string {
	// Handle error results
	if (result.isError) {
		return formatErrorResult(result);
	}

	// Handle successful results with content
	if (Array.isArray(result.content) && result.content.length > 0) {
		return formatContentArray(result.content);
	}

	// Fallback for empty results
	return 'Tool executed successfully (no content returned).';
}

/**
 * Formats error results
 */
function formatErrorResult(result: CallToolResult): string {
	if (!Array.isArray(result.content) || result.content.length === 0) {
		return 'Error: Tool execution failed (no error details provided).';
	}

	const errorMessages: string[] = [];

	for (const item of result.content) {
		if (typeof item === 'string') {
			errorMessages.push(item);
		} else if (item && typeof item === 'object') {
			const obj = item as Record<string, unknown>;
			if (typeof obj.text === 'string') {
				errorMessages.push(obj.text);
			} else if (typeof obj.message === 'string') {
				errorMessages.push(obj.message);
			} else if (typeof obj.error === 'string') {
				errorMessages.push(obj.error);
			}
		}
	}

	if (errorMessages.length > 0) {
		return `Error: ${errorMessages.join('\n')}`;
	}

	return 'Error: Tool execution failed.';
}

/**
 * Formats an array of content items
 */
function formatContentArray(content: unknown[]): string {
	const formattedItems: string[] = [];

	for (const item of content) {
		const formatted = formatContentItem(item);
		if (formatted) {
			formattedItems.push(formatted);
		}
	}

	if (formattedItems.length === 0) {
		return 'Tool executed successfully (no displayable content).';
	}

	return formattedItems.join('\n\n');
}

/**
 * Formats a single content item
 */
function formatContentItem(item: unknown): string | null {
	if (!item) {
		return null;
	}

	// Handle string content
	if (typeof item === 'string') {
		return item;
	}

	// Handle non-object content
	if (typeof item !== 'object') {
		if (typeof item === 'number' || typeof item === 'boolean') {
			return String(item);
		}
		return JSON.stringify(item);
	}

	const obj = item as Record<string, unknown>;
	const type = typeof obj.type === 'string' ? obj.type.toLowerCase() : undefined;

	switch (type) {
		case 'text':
			return formatTextContent(obj);

		case 'image':
			return formatImageContent(obj);

		case 'resource':
			return formatResourceContent(obj);

		case 'embedded_resource':
			return formatEmbeddedResourceContent(obj);

		default:
			// Try to extract text from unknown types
			if (typeof obj.text === 'string') {
				return obj.text;
			}
			// Fallback to JSON representation
			try {
				return JSON.stringify(item, null, 2);
			} catch {
				return '[complex object]';
			}
	}
}

/**
 * Formats text content
 */
function formatTextContent(obj: Record<string, unknown>): string | null {
	if (typeof obj.text === 'string') {
		return obj.text;
	}
	return null;
}

/**
 * Formats image content
 */
function formatImageContent(obj: Record<string, unknown>): string {
	const parts: string[] = ['[Image Content]'];

	// Add MIME type if available
	if (typeof obj.mimeType === 'string') {
		parts.push(`Type: ${obj.mimeType}`);
	}

	// Add URL if available
	if (typeof obj.url === 'string') {
		parts.push(`URL: ${obj.url}`);
	}

	// Add data indicator if present
	if (typeof obj.data === 'string') {
		const dataLength = obj.data.length;
		parts.push(`Data: ${dataLength} characters (base64)`);
	}

	return parts.join('\n');
}

/**
 * Formats resource content
 */
function formatResourceContent(obj: Record<string, unknown>): string {
	const parts: string[] = ['[Resource]'];

	// Extract resource details
	const resource = obj.resource as Record<string, unknown> | undefined;
	if (resource) {
		if (typeof resource.uri === 'string') {
			parts.push(`URI: ${resource.uri}`);
		}

		if (typeof resource.name === 'string') {
			parts.push(`Name: ${resource.name}`);
		}

		if (typeof resource.mimeType === 'string') {
			parts.push(`Type: ${resource.mimeType}`);
		}

		if (typeof resource.description === 'string') {
			parts.push(`Description: ${resource.description}`);
		}
	}

	return parts.join('\n');
}

/**
 * Formats embedded resource content
 */
function formatEmbeddedResourceContent(obj: Record<string, unknown>): string {
	const parts: string[] = ['[Embedded Resource]'];

	if (typeof obj.uri === 'string') {
		parts.push(`URI: ${obj.uri}`);
	}

	if (typeof obj.mimeType === 'string') {
		parts.push(`Type: ${obj.mimeType}`);
	}

	// Add blob indicator if present
	if (typeof obj.blob === 'string') {
		const blobLength = obj.blob.length;
		parts.push(`Data: ${blobLength} characters`);
	}

	return parts.join('\n');
}

/**
 * Formats a list of warnings
 */
export function formatWarnings(warnings: string[]): string {
	if (warnings.length === 0) {
		return '';
	}

	const header = warnings.length === 1 ? 'Warning:' : 'Warnings:';
	return `${header}\n${warnings.map((w) => `- ${w}`).join('\n')}\n\n`;
}
