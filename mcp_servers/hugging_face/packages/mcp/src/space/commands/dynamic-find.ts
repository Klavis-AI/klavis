import type { ToolResult } from '../../types/tool-result.js';
import { SpaceSearchTool, type SpaceSearchResult } from '../../space-search.js';
import { escapeMarkdown } from '../../utilities.js';
import { VIEW_PARAMETERS } from '../dynamic-space-tool.js';

// Default number of results to return
const DEFAULT_RESULTS_LIMIT = 10;

/**
 * Prompt configuration for discover operation
 * These prompts can be easily tweaked to adjust the search behavior
 */
const FIND_PROMPTS = {
	// Task hints shown when called with blank query
	TASK_HINTS: `Here are some examples of tasks that dynamic spaces can perform:

- Image Generation
- Video Generation
- Text Generation
- Visual QA
- Language Translation
- Speech Synthesis
- 3D Modeling
- Object Detection
- Text Analysis
- Image Editing
- Code Generation
- Question Answering
- Data Visualization
- Voice Cloning
- Background Removal
- OCR
- Image Captioning
- Sentiment Analysis
- Music Generation
- Style Transfer

To find MCP-enabled Spaces for a specific task, call this operation with a search query:

**Example:**
\`\`\`json
{
  "operation": "find",
  "search_query": "image generation",
  "limit": 10
}
\`\`\``,

	// Header for search results
	RESULTS_HEADER: (query: string, showing: number, total: number) => {
		const showingText = showing < total ? `Showing ${showing} of ${total} results` : `All ${showing} results`;
		return `# MCP Space Find Results for "${query}" (${showingText})

These MCP-enabled Spaces can be invoked using the \`dynamic_space\` tool.
Use \`"operation": "${VIEW_PARAMETERS}"\` to inspect a space's parameters before invoking.

`;
	},

	// No results message
	NO_RESULTS: (query: string) =>
		`No MCP-enabled Spaces found for "${query}".

Try:
- Broader search terms (e.g., "image generation" instead of specific model names)
- Task-focused queries (e.g., "text generation", "object detection")
- Different task categories (e.g., "video generation", "image classification")`,
};

/**
 * Discovers MCP-enabled Spaces based on search criteria
 *
 * @param searchQuery - The search query or task category
 * @param limit - Maximum number of results to return
 * @param hfToken - Optional HuggingFace API token
 * @returns Formatted search results
 */
export async function findSpaces(
	searchQuery?: string,
	limit: number = DEFAULT_RESULTS_LIMIT,
	hfToken?: string
): Promise<ToolResult> {
	// Return task hints when called with blank query
	if (!searchQuery || searchQuery.trim() === '') {
		return {
			formatted: FIND_PROMPTS.TASK_HINTS,
			totalResults: 0,
			resultsShared: 0,
		};
	}

	try {
		// Use SpaceSearchTool to search for MCP-enabled spaces only
		const searchTool = new SpaceSearchTool(hfToken);
		const { results, totalCount } = await searchTool.search(
			searchQuery,
			limit,
			true // mcp = true (only MCP-enabled spaces)
		);

		// Format and return results
		return formatFindResults(searchQuery, results, totalCount);
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		return {
			formatted: `Error discovering spaces: ${errorMessage}`,
			totalResults: 0,
			resultsShared: 0,
			isError: true,
		};
	}
}

/**
 * Formats discover results as a markdown table
 * Note: Author column is omitted as it's superfluous for invocation purposes
 * Duplication is OK for the mean time; space_search will be rolled in to a general tool
 */
function formatFindResults(query: string, results: SpaceSearchResult[], totalCount: number): ToolResult {
	if (results.length === 0) {
		return {
			formatted: FIND_PROMPTS.NO_RESULTS(query),
			totalResults: 0,
			resultsShared: 0,
		};
	}

	let markdown = FIND_PROMPTS.RESULTS_HEADER(query, results.length, totalCount);

	// Table header (without Author column)
	markdown += '| Space | Description | Space ID | Category | Likes | Trending | Relevance |\n';
	markdown += '|-------|-------------|----------|----------|-------|----------|----------|\n';

	// Table rows
	for (const result of results) {
		const title = result.title || 'Untitled';
		const description = result.shortDescription || result.ai_short_description || 'No description';
		const id = result.id || '';
		const emoji = result.emoji ? escapeMarkdown(result.emoji) + ' ' : '';
		const relevance = result.semanticRelevancyScore ? (result.semanticRelevancyScore * 100).toFixed(1) + '%' : 'N/A';

		markdown +=
			`| ${emoji}[${escapeMarkdown(title)}](https://hf.co/spaces/${id}) ` +
			`| ${escapeMarkdown(description)} ` +
			`| \`${escapeMarkdown(id)}\` ` +
			`| \`${escapeMarkdown(result.ai_category ?? '-')}\` ` +
			`| ${escapeMarkdown(result.likes?.toString() ?? '-')} ` +
			`| ${escapeMarkdown(result.trendingScore?.toString() ?? '-')} ` +
			`| ${relevance} |\n`;
	}

	return {
		formatted: markdown,
		totalResults: totalCount,
		resultsShared: results.length,
	};
}
