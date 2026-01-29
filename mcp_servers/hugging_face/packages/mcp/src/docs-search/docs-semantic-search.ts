import { z } from 'zod';
import { HfApiCall } from '../hf-api-call.js';
import { escapeMarkdown, estimateTokens } from '../utilities.js';
import { DOC_FETCH_CONFIG } from './doc-fetch.js';
import type { ToolResult } from '../types/tool-result.js';

/** token estimation. initial results for "how to load a image to image model in transformers" returned
 * 121973 characters (36711 anthropic tokens) */

export const DOCS_SEMANTIC_SEARCH_CONFIG = {
	name: 'hf_doc_search',
	description:
		'Search and Discover Hugging Face Product and Library documentation. Send an empty query to discover structure and navigation instructions. ' +
		'You MUST consult this tool for the most up-to-date information when using Hugging Face libraries. Combine with the Product filter to focus results.',
	schema: z.object({
		query: z
			.string()
			.max(200, 'Query too long')
			.superRefine((value, ctx) => {
				const trimmed = value.trim();
				if (trimmed.length === 0) {
					return;
				}
				if (trimmed.length < 3) {
					ctx.addIssue({
						code: z.ZodIssueCode.too_small,
						type: 'string',
						minimum: 3,
						inclusive: true,
						message: 'Supply at least one search term',
					});
				}
			})
			.describe(
				'Start with an empty query for structure, endpoint discovery and navigation tips. Use semantic queries for targetted searches.'
			),
		product: z.string().optional().describe('Filter by Product. Supply when known for focused results'),
	}),
	annotations: {
		title: 'Hugging Face Documentation Search',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

export type DocSearchParams = z.infer<typeof DOCS_SEMANTIC_SEARCH_CONFIG.schema>;

interface DocSearchResult {
	text: string;
	product: string;
	heading1: string;
	source_page_url: string;
	source_page_title: string;
	heading2?: string;
}

interface DocSearchApiParams {
	q: string;
	product?: string;
}

interface DocsIndexEntry {
	id: string;
	url: string;
	category: string;
}

// Token budget defaults
const DEFAULT_TOKEN_BUDGET = 12500;
const TRUNCATE_EXCERPT_LENGTH = 400; // chars for truncated excerpts
const DOCS_INDEX_URL = 'https://huggingface.co/api/docs';

/**
 * Use the Hugging Face Semantic Document Search API
 */
export class DocSearchTool extends HfApiCall<DocSearchApiParams, DocSearchResult[]> {
	private tokenBudget: number;

	/**
	 * @param hfToken Optional Hugging Face token for API access
	 * @param apiUrl The URL of the Hugging Face document search API
	 * @param tokenBudget Maximum number of tokens to return
	 */
	constructor(hfToken?: string, apiUrl = 'https://hf.co/api/docs/search', tokenBudget = DEFAULT_TOKEN_BUDGET) {
		super(apiUrl, hfToken);
		this.tokenBudget = tokenBudget;
	}

	/**
	 * @param query Search query string (e.g. "rate limits", "analytics")
	 * @param product Optional product filter
	 */
	async search(params: DocSearchParams): Promise<ToolResult> {
		try {
			const query = params.query?.trim() ?? '';
			if (query.length === 0) {
				const docsIndex = await this.fetchFromApi<DocsIndexEntry[]>(DOCS_INDEX_URL);
				return formatDocsIndex(docsIndex);
			}

			const apiParams: DocSearchApiParams = { q: query.toLowerCase() };
			if (params.product) {
				apiParams.product = params.product;
			}

			const results = await this.callApi<DocSearchResult[]>(apiParams);

			if (results.length === 0) {
				return {
					formatted: params.product
						? `No documentation found for query '${query}' in product '${params.product}'`
						: `No documentation found for query '${query}'`,
					totalResults: 0,
					resultsShared: 0,
				};
			}

			return formatSearchResults(query, results, params.product, this.tokenBudget);
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search documentation: ${error.message}`);
			}
			throw error;
		}
	}
}

/**
 * Group results by product and source page URL
 */
function groupResults(results: DocSearchResult[]): Map<string, Map<string, DocSearchResult[]>> {
	const grouped = new Map<string, Map<string, DocSearchResult[]>>();

	for (const result of results) {
		if (!grouped.has(result.product)) {
			grouped.set(result.product, new Map());
		}

		const productGroup = grouped.get(result.product);
		if (!productGroup) continue;

		// Strip the anchor (#section) from the URL for grouping purposes
		const baseUrl = result.source_page_url.split('#')[0] || result.source_page_url;

		if (!productGroup.has(baseUrl)) {
			productGroup.set(baseUrl, []);
		}

		const pageResults = productGroup.get(baseUrl);
		if (pageResults) {
			pageResults.push(result);
		}
	}

	return grouped;
}

/**
 * Format the documentation root index response for empty queries
 */
function formatDocsIndex(docsIndex: DocsIndexEntry[]): ToolResult {
	if (!docsIndex.length) {
		return {
			formatted:
				'No documentation categories are currently available. Try running the search again with specific terms.',
			totalResults: 0,
			resultsShared: 0,
		};
	}

	const header = '### Hugging Face Documentation Products\n';
	const tableHeader = '| Product | Category | Documentation |\n| --- | --- | --- |\n';
	const rows = docsIndex
		.map((entry) => {
			const docsUrl = `https://huggingface.co${entry.url}`;
			return `| \`${entry.id}\` | ${escapeMarkdown(entry.category)} | ${docsUrl} |`;
		})
		.join('\n');

	const llmsNote =
		'\n\nEach documentation root exposes an `llms.txt` endpoint (e.g. add `/llms.txt` to the documentation URL). ' +
		'Use semantic search when you have a specific question for faster, more targeted results.';

	return {
		formatted: `${header}${tableHeader}${rows}${llmsNote}`,
		totalResults: docsIndex.length,
		resultsShared: docsIndex.length,
	};
}

/**
 * Group page results by section (heading2)
 */
function groupBySection(pageResults: DocSearchResult[]): Map<string | undefined, DocSearchResult[]> {
	const sectionGroups = new Map<string | undefined, DocSearchResult[]>();

	for (const result of pageResults) {
		const section = result.heading2;
		if (!sectionGroups.has(section)) {
			sectionGroups.set(section, []);
		}
		const sectionResults = sectionGroups.get(section);
		if (sectionResults) {
			sectionResults.push(result);
		}
	}

	return sectionGroups;
}

/**
 * Format excerpts from a section
 */
function formatSectionExcerpts(
	section: string | undefined,
	results: DocSearchResult[],
	useTruncatedMode: boolean,
	hasAlreadyShownTruncation: boolean
): { text: string; tokensUsed: number; wasContentTruncated: boolean } {
	const lines: string[] = [];
	let tokensUsed = 0;
	let wasContentTruncated = false;

	// Add section heading if we have one
	if (section) {
		const heading =
			results.length > 1
				? `\n#### Excerpts from the "${escapeMarkdown(section)}" section`
				: `\n#### Excerpt from the "${escapeMarkdown(section)}" section`;

		lines.push(heading, '');
		tokensUsed += estimateTokens(heading + '\n\n');
	}

	for (const result of results) {
		let cleanText = result.text
			.replace(/<[^>]*>/g, '')
			.replace(/\n\s*\n/g, '\n')
			.trim();

		// Truncate if in truncated mode and we haven't shown the message yet
		if (useTruncatedMode && cleanText.length > TRUNCATE_EXCERPT_LENGTH && !hasAlreadyShownTruncation) {
			cleanText =
				cleanText.substring(0, TRUNCATE_EXCERPT_LENGTH) +
				`...\n\n*[Content truncated - use ${DOC_FETCH_CONFIG.name} for full text or narrow search terms]*`;
			wasContentTruncated = true;
		}

		lines.push(cleanText, '');
		tokensUsed += estimateTokens(cleanText + '\n\n');
	}

	// Remove trailing empty line
	if (lines.length > 0 && lines[lines.length - 1] === '') {
		lines.pop();
	}

	return { text: lines.join('\n'), tokensUsed, wasContentTruncated };
}

/**
 * Format search results with simple token budget management
 */
function formatSearchResults(
	query: string,
	results: DocSearchResult[],
	productFilter?: string,
	tokenBudget = DEFAULT_TOKEN_BUDGET
): ToolResult {
	const lines: string[] = [];
	let hasShownTruncationMessage = false;

	// Header
	const filterText = productFilter ? ` (filtered by product: ${productFilter})` : '';
	const header = `# Documentation Library Search Results for "${escapeMarkdown(query)}"${filterText}\n\nFound ${results.length} results`;
	lines.push(header);

	// Group and sort results
	const grouped = groupResults(results);
	const sortedProducts = Array.from(grouped.keys()).sort((a, b) => {
		const productGroupA = grouped.get(a);
		const productGroupB = grouped.get(b);
		if (!productGroupA || !productGroupB) return 0;
		const countA = Array.from(productGroupA.values()).reduce((sum, arr) => sum + arr.length, 0);
		const countB = Array.from(productGroupB.values()).reduce((sum, arr) => sum + arr.length, 0);
		return countB - countA;
	});

	const linkOnlyResults: Array<{ product: string; url: string; title: string; count: number }> = [];

	for (const product of sortedProducts) {
		const productGroup = grouped.get(product);
		if (!productGroup) continue;

		// Check current size before adding anything
		const currentText = lines.join('\n');
		if (estimateTokens(currentText) > tokenBudget) {
			// Over budget - add remaining products to links
			for (const url of productGroup.keys()) {
				const pageResults = productGroup.get(url);
				if (!pageResults?.[0]) continue;
				linkOnlyResults.push({
					product,
					url,
					title: pageResults[0].heading1 || pageResults[0].source_page_title,
					count: pageResults.length,
				});
			}
			continue;
		}

		// Add product header
		const totalProductHits = Array.from(productGroup.values()).reduce((sum, arr) => sum + arr.length, 0);
		const productHeader = `## Results for Product: ${escapeMarkdown(product)} (${totalProductHits} results)\n`;
		lines.push(productHeader);

		// Sort pages by hit count
		const sortedUrls = Array.from(productGroup.keys()).sort((a, b) => {
			const pageResultsA = productGroup.get(a);
			const pageResultsB = productGroup.get(b);
			if (!pageResultsA || !pageResultsB) return 0;
			return pageResultsB.length - pageResultsA.length;
		});

		for (const url of sortedUrls) {
			const pageResults = productGroup.get(url);
			if (!pageResults?.[0]) continue;

			const pageTitle = pageResults[0].heading1 || pageResults[0].source_page_title;

			// Check if we're over budget - if so, add remaining pages to links
			const currentText = lines.join('\n');
			if (estimateTokens(currentText) > tokenBudget) {
				linkOnlyResults.push({ product, url, title: pageTitle, count: pageResults.length });
				continue;
			}

			const hitCount = pageResults.length > 1 ? ` (${pageResults.length} results)` : '';
			const pageHeader = `\n### Results from [${escapeMarkdown(pageTitle)}](${url})${hitCount}\n`;
			lines.push(pageHeader);

			// Add all sections for this page
			const sectionGroups = groupBySection(pageResults);
			for (const [section, sectionResults] of sectionGroups) {
				const currentTokens = estimateTokens(lines.join('\n'));
				const useTruncatedMode = currentTokens > tokenBudget * 0.7;

				const result = formatSectionExcerpts(section, sectionResults, useTruncatedMode, hasShownTruncationMessage);

				if (result.text.trim()) {
					lines.push(result.text);
					if (result.wasContentTruncated) {
						hasShownTruncationMessage = true;
					}
				}
			}
		}
	}

	// Add link-only results
	if (linkOnlyResults.length > 0) {
		lines.push(`\n## Further results were found in:\n`);
		for (const linkResult of linkOnlyResults) {
			const hitText = linkResult.count > 1 ? ` (${linkResult.count} results)` : '';
			lines.push(`- [${escapeMarkdown(linkResult.title)}](${linkResult.url})${hitText} *(${linkResult.product})*`);
		}
		lines.push('');
	}

	lines.push('---\n');
	lines.push(`Use the "${DOC_FETCH_CONFIG.name}" tool to fetch a document from the library.`);

	return {
		formatted: lines.join('\n'),
		totalResults: results.length,
		resultsShared: results.length,
	};
}
