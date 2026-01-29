import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { logger } from './logger.js';

/**
 * Options for filtering image content
 */
export interface ImageFilterOptions {
	enabled: boolean;
	toolName: string;
	outwardFacingName: string;
}

/**
 * Strips image content from a tool result if filtering is enabled
 *
 * This function is used by both proxied Gradio tools and the space tool's invoke operation
 * to conditionally remove image content blocks based on user configuration.
 */
export function stripImageContentFromResult(
	callResult: CallToolResult,
	{ enabled, toolName, outwardFacingName }: ImageFilterOptions
): CallToolResult {
	if (!enabled) {
		return callResult;
	}

	const content = callResult.content;
	if (!Array.isArray(content) || content.length === 0) {
		return callResult;
	}

	const filteredContent = content.filter((item) => {
		if (!item || typeof item !== 'object') {
			return true;
		}

		const candidate = item as { type?: unknown };
		const typeValue = typeof candidate.type === 'string' ? candidate.type.toLowerCase() : undefined;
		return typeValue !== 'image';
	});

	if (filteredContent.length === content.length) {
		return callResult;
	}

	const removedCount = content.length - filteredContent.length;
	logger.debug({ tool: toolName, outwardFacingName, removedCount }, 'Stripped image content from Gradio tool response');

	if (filteredContent.length === 0) {
		filteredContent.push({
			type: 'text',
			text: 'Image content omitted due to client configuration (no_image_content=true).',
		});
	}

	return { ...callResult, content: filteredContent };
}

/**
 * Extracts a URL from the result content if present
 *
 * Used for OpenAI MCP client to populate structuredContent field
 */
export function extractUrlFromContent(content: unknown[]): string | undefined {
	if (!Array.isArray(content) || content.length === 0) {
		return undefined;
	}

	// Check each content item for a URL-like string
	for (const item of content) {
		if (!item || typeof item !== 'object') {
			continue;
		}

		const candidate = item as { type?: string; text?: string; url?: string };

		// Check for explicit url field
		if (typeof candidate.url === 'string' && /^https?:\/\//i.test(candidate.url.trim())) {
			return candidate.url.trim();
		}

		// Check for text field that looks like a URL
		if (typeof candidate.text === 'string') {
			let text = candidate.text.trim();

			// Remove "Image URL:" or "Image URL :" prefix if present (case insensitive)
			text = text.replace(/^image\s+url\s*:\s*/i, '');

			if (/^https?:\/\//i.test(text)) {
				return text;
			}
		}
	}

	return undefined;
}
