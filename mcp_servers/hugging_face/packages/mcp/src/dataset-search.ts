import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { formatDate, formatNumber } from './utilities.js';
import type { ToolResult } from './types/tool-result.js';
const TAGS_TO_RETURN = 20;
// Dataset Search Tool Configuration
export const DATASET_SEARCH_TOOL_CONFIG = {
	name: 'dataset_search',
	description:
		'Find Datasets hosted on the Hugging Face hub. ' +
		'Returns comprehensive information about matching datasets including downloads, likes, tags, and direct links. ' +
		'Include links to the datasets in your response',
	schema: z.object({
		query: z
			.string()
			.optional()
			.describe(
				'Search term. Leave blank and specify "sort" and "limit" to get e.g. "Top 20 trending datasets", "Top 10 most recent datasets" etc" '
			),
		author: z
			.string()
			.optional()
			.describe("Organization or user who created the dataset (e.g., 'google', 'facebook', 'allenai')"),
		tags: z
			.array(z.string())
			.optional()
			.describe(
				"Tags to filter datasets (e.g., ['language:en', 'size_categories:1M<n<10M', 'task_categories:text-classification'])"
			),
		sort: z
			.enum(['trendingScore', 'downloads', 'likes', 'createdAt', 'lastModified'])
			.optional()
			.describe('Sort order: trendingScore, downloads, likes, createdAt, lastModified'),
		limit: z.number().min(1).max(100).optional().default(20).describe('Maximum number of results to return'),
	}),
	annotations: {
		title: 'Dataset Search',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

// Define search parameter types
export type DatasetSearchParams = z.infer<typeof DATASET_SEARCH_TOOL_CONFIG.schema>;

// API parameter interface for direct HF API calls
interface DatasetApiParams {
	search?: string;
	author?: string;
	filter?: string;
	sort?: string;
	direction?: string;
	limit?: string;
}

// Dataset result interface matching HF API response
interface DatasetApiResult {
	_id: string;
	id: string;
	author: string;
	likes: number;
	downloads: number;
	trendingScore?: number;
	private: boolean;
	gated: boolean;
	tags: string[];
	createdAt: string;
	lastModified: string;
	description?: string;
	sha: string;
}
/**
 * Service for searching Hugging Face Datasets using direct API calls
 */
export class DatasetSearchTool extends HfApiCall<DatasetApiParams, DatasetApiResult[]> {
	/**
	 * @param hfToken Optional Hugging Face token for API access
	 */
	constructor(hfToken?: string) {
		super('https://huggingface.co/api/datasets', hfToken);
	}

	/**
	 * Search for datasets with detailed parameters
	 */
	async searchWithParams(params: Partial<DatasetSearchParams>): Promise<ToolResult> {
		try {
			// Convert our params to the HF API format
			const apiParams: DatasetApiParams = {};

			// Handle search query
			if (params.query) {
				apiParams.search = params.query;
			}

			// Handle author filter
			if (params.author) {
				apiParams.author = params.author;
			}

			// Handle tags filter
			if (params.tags && params.tags.length > 0) {
				apiParams.filter = params.tags.join(',');
			}

			// Handle sorting (always descending)
			if (params.sort) {
				apiParams.sort = params.sort;
				apiParams.direction = '-1';
			}

			// Handle limit
			if (params.limit) {
				apiParams.limit = params.limit.toString();
			}

			// Call the API
			const datasets = await this.callApi<DatasetApiResult[]>(apiParams);

			if (datasets.length === 0) {
				return {
					formatted: `No datasets found for the given criteria.`,
					totalResults: 0,
					resultsShared: 0
				};
			}

			return formatSearchResults(datasets, params);
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search for datasets: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Search for datasets with a specific filter (e.g., arxiv:XXXX.XXXXX)
	 */
	async searchWithFilter(filter: string, limit: number = 10): Promise<ToolResult> {
		try {
			const apiParams: DatasetApiParams = {
				filter: filter,
				limit: limit.toString(),
				sort: 'downloads',
				direction: '-1',
			};

			// Call the API
			const datasets = await this.callApi<DatasetApiResult[]>(apiParams);

			if (datasets.length === 0) {
				return {
					formatted: `No datasets found referencing ${filter}.`,
					totalResults: 0,
					resultsShared: 0
				};
			}

			return formatSearchResults(datasets, { limit });
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search for datasets: ${error.message}`);
			}
			throw error;
		}
	}
}

// Formatting Function
function formatSearchResults(datasets: DatasetApiResult[], params: Partial<DatasetSearchParams>): ToolResult {
	const r: string[] = [];

	// Build search description
	const searchTerms = [];
	if (params.query) searchTerms.push(`query "${params.query}"`);
	if (params.author) searchTerms.push(`author "${params.author}"`);
	if (params.tags && params.tags.length > 0) searchTerms.push(`tags [${params.tags.join(', ')}]`);
	if (params.sort) searchTerms.push(`sorted by ${params.sort} (descending)`);

	const searchDesc = searchTerms.length > 0 ? ` matching ${searchTerms.join(', ')}` : '';

	const resultText =
		datasets.length === params.limit
			? `Showing first ${datasets.length.toString()} datasets${searchDesc}:`
			: `Found ${datasets.length.toString()} datasets${searchDesc}:`;
	r.push(resultText);
	r.push('');

	for (const dataset of datasets) {
		r.push(`## ${dataset.id}`);
		r.push('');

		// Description if available
		if (dataset.description) {
			r.push(`${dataset.description.substring(0, 200)}${dataset.description.length > 200 ? '...' : ''}`);
			r.push('');
		}

		// Basic info line
		const info = [];
		if (dataset.downloads) info.push(`**Downloads:** ${formatNumber(dataset.downloads)}`);
		if (dataset.likes) info.push(`**Likes:** ${dataset.likes.toString()}`);
		if (dataset.trendingScore) info.push(`**Trending Score:** ${dataset.trendingScore.toString()}`);

		if (info.length > 0) {
			r.push(info.join(' | '));
			r.push('');
		}

		// Tags
		if (dataset.tags && dataset.tags.length > 0) {
			r.push(`**Tags:** ${dataset.tags.slice(0, TAGS_TO_RETURN).join(', ')}`);
			if (dataset.tags.length > TAGS_TO_RETURN) {
				r.push(`*and ${(dataset.tags.length - TAGS_TO_RETURN).toString()} more...*`);
			}
			r.push('');
		}

		// Status indicators
		const status = [];
		if (dataset.gated) status.push('🔒 Gated');
		if (dataset.private) status.push('🔐 Private');
		if (status.length > 0) {
			r.push(status.join(' | '));
			r.push('');
		}

		// Dates
		if (dataset.createdAt) {
			r.push(`**Created:** ${formatDate(dataset.createdAt)}`);
		}

		if (dataset.lastModified && dataset.lastModified !== dataset.createdAt) {
			r.push(`**Last Modified:** ${formatDate(dataset.lastModified)}`);
		}

		r.push(`**Link:** [https://hf.co/datasets/${dataset.id}](https://hf.co/datasets/${dataset.id})`);
		r.push('');
		r.push('---');
		r.push('');
	}

	return {
		formatted: r.join('\n'),
		totalResults: datasets.length,
		resultsShared: datasets.length
	};
}
