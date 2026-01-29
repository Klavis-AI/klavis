import type { ToolResult } from '../../types/tool-result.js';
import { escapeMarkdown } from '../../utilities.js';
import { VIEW_PARAMETERS } from '../types.js';

/**
 * Prompt configuration for discover operation (from DYNAMIC_SPACE_DATA)
 * These prompts can be easily tweaked to adjust behavior
 */
export const DISCOVER_PROMPTS = {
	// Header for results
	RESULTS_HEADER: `**Available Spaces:**

These spaces can be invoked using the \`dynamic_space\` tool.
Use \`"operation": "${VIEW_PARAMETERS}"\` to inspect a space's parameters before invoking.

`,

	// No results message
	NO_RESULTS: `No spaces available in the configured list.`,

	// Error fetching
	FETCH_ERROR: (url: string, error: string): string => `Error fetching space list from ${url}: ${error}`,
};

/**
 * Parse CSV content into space entries
 * Expected format: space_id,category,description
 */
function parseCsvContent(content: string): Array<{ id: string; category: string; description: string }> {
	const lines = content.trim().split('\n');
	const results: Array<{ id: string; category: string; description: string }> = [];

	for (const line of lines) {
		if (!line.trim()) continue;

		// Parse CSV with quoted fields
		const match = line.match(/^([^,]+),([^,]+),"([^"]*)"$/) || line.match(/^([^,]+),([^,]+),(.*)$/);

		if (match && match[1] && match[2] && match[3]) {
			results.push({
				id: match[1].trim(),
				category: match[2].trim(),
				description: match[3].trim(),
			});
		}
	}

	return results;
}

/**
 * Format results as a markdown table
 */
function formatDiscoverResults(results: Array<{ id: string; category: string; description: string }>): string {
	if (results.length === 0) {
		return DISCOVER_PROMPTS.NO_RESULTS;
	}

	let markdown = DISCOVER_PROMPTS.RESULTS_HEADER;

	// Table header
	markdown += '| Space ID | Category | Description |\n';
	markdown += '|----------|----------|-------------|\n';

	// Table rows
	for (const result of results) {
		markdown +=
			`| \`${escapeMarkdown(result.id)}\` ` +
			`| ${escapeMarkdown(result.category)} ` +
			`| ${escapeMarkdown(result.description)} |\n`;
	}

	return markdown;
}

/**
 * Discover spaces from a configured URL (DYNAMIC_SPACE_DATA)
 * Fetches CSV content and returns as markdown table
 */
export async function discoverSpaces(): Promise<ToolResult> {
	const url = process.env.DYNAMIC_SPACE_DATA;

	if (!url) {
		return {
			formatted: 'Error: DYNAMIC_SPACE_DATA environment variable is not set.',
			totalResults: 0,
			resultsShared: 0,
			isError: true,
		};
	}

	try {
		const response = await fetch(url);

		if (!response.ok) {
			return {
				formatted: DISCOVER_PROMPTS.FETCH_ERROR(url, `HTTP ${response.status}`),
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		const content = await response.text();
		const results = parseCsvContent(content);

		return {
			formatted: formatDiscoverResults(results),
			totalResults: results.length,
			resultsShared: results.length,
		};
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		return {
			formatted: DISCOVER_PROMPTS.FETCH_ERROR(url, errorMessage),
			totalResults: 0,
			resultsShared: 0,
			isError: true,
		};
	}
}
