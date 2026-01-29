import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { formatDate, formatNumber } from './utilities.js';
import type { ToolResult } from './types/tool-result.js';

export const TAGS_TO_RETURN = 20;
// Model Search Tool Configuration
export const MODEL_SEARCH_TOOL_CONFIG = {
	name: 'model_search',
	description:
		'Find Machine Learning models hosted on Hugging Face. ' +
		'Returns comprehensive information about matching models including downloads, likes, tags, and direct links. ' +
		'Include links to the models in your response',
	schema: z.object({
		query: z
			.string()
			.optional()
			.describe(
				'Search term. Leave blank and specify "sort" and "limit" to get e.g. "Top 20 trending models", "Top 10 most recent models" etc" '
			),
		author: z
			.string()
			.optional()
			.describe("Organization or user who created the model (e.g., 'google', 'meta-llama', 'microsoft')"),
		task: z
			.string()
			.optional()
			.describe("Model task type (e.g., 'text-generation', 'image-classification', 'translation')"),
		library: z.string().optional().describe("Framework the model uses (e.g., 'transformers', 'diffusers', 'timm')"),
		sort: z
			.enum(['trendingScore', 'downloads', 'likes', 'createdAt', 'lastModified'])
			.optional()
			.describe('Sort order: trendingScore, downloads , likes, createdAt, lastModified'),
		limit: z.number().min(1).max(100).optional().default(20).describe('Maximum number of results to return'),
	}),
	annotations: {
		title: 'Model Search',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

// Define search parameter types
export type ModelSearchParams = z.infer<typeof MODEL_SEARCH_TOOL_CONFIG.schema>;

// API parameter interface for direct HF API calls
interface ModelApiParams {
	search?: string;
	author?: string;
	filter?: string;
	sort?: string;
	direction?: string;
	limit?: string;
}

// Model result interface matching HF API response
interface ModelApiResult {
	_id: string;
	id: string;
	modelId: string;
	likes: number;
	downloads: number;
	trendingScore?: number;
	private: boolean;
	tags: string[];
	pipeline_tag?: string;
	library_name?: string;
	createdAt: string;
}

/**
 * Service for searching Hugging Face Models using direct API calls
 */
export class ModelSearchTool extends HfApiCall<ModelApiParams, ModelApiResult[]> {
	/**
	 * @param hfToken Optional Hugging Face token for API access
	 */
	constructor(hfToken?: string) {
		super('https://huggingface.co/api/models', hfToken);
	}

	/**
	 * Search for models with detailed parameters
	 */
	async searchWithParams(params: Partial<ModelSearchParams>): Promise<ToolResult> {
		try {
			// Convert our params to the HF API format
			const apiParams: ModelApiParams = {};

			// Handle search query
			if (params.query) {
				apiParams.search = params.query;
			}

			// Handle author filter
			if (params.author) {
				apiParams.author = params.author;
			}

			// Handle task and library filters
			const filters = [];
			if (params.task) filters.push(params.task);
			if (params.library) filters.push(params.library);
			if (filters.length > 0) {
				apiParams.filter = filters.join(',');
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
			const models = await this.callApi<ModelApiResult[]>(apiParams);

			if (models.length === 0) {
				return {
					formatted: `No models found for the given criteria.`,
					totalResults: 0,
					resultsShared: 0
				};
			}

			return formatSearchResults(models, params);
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search for models: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Search for models with a specific filter (e.g., arxiv:XXXX.XXXXX)
	 */
	async searchWithFilter(filter: string, limit: number = 10): Promise<ToolResult> {
		try {
			const apiParams: ModelApiParams = {
				filter: filter,
				limit: limit.toString(),
				sort: 'downloads',
				direction: '-1',
			};

			// Call the API
			const models = await this.callApi<ModelApiResult[]>(apiParams);

			if (models.length === 0) {
				return {
					formatted: `No models found referencing ${filter}.`,
					totalResults: 0,
					resultsShared: 0
				};
			}

			return formatSearchResults(models, { limit });
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search for models: ${error.message}`);
			}
			throw error;
		}
	}
}

// Formatting Function
function formatSearchResults(models: ModelApiResult[], params: Partial<ModelSearchParams>): ToolResult {
	const r: string[] = [];

	// Build search description
	const searchTerms = [];
	if (params.query) searchTerms.push(`query "${params.query}"`);
	if (params.author) searchTerms.push(`author "${params.author}"`);
	if (params.task) searchTerms.push(`task "${params.task}"`);
	if (params.library) searchTerms.push(`library "${params.library}"`);
	if (params.sort) searchTerms.push(`sorted by ${params.sort} (descending)`);

	const searchDesc = searchTerms.length > 0 ? ` matching ${searchTerms.join(', ')}` : '';

	const resultText =
		models.length === params.limit
			? `Showing first ${models.length.toString()} models${searchDesc}:`
			: `Found ${models.length.toString()} models${searchDesc}:`;
	r.push(resultText);
	r.push('');

	for (const model of models) {
		r.push(`## ${model.id}`);
		r.push('');

		// Basic info line
		const info = [];
		if (model.pipeline_tag) info.push(`**Task:** ${model.pipeline_tag}`);
		if (model.library_name) info.push(`**Library:** ${model.library_name}`);
		if (model.downloads) info.push(`**Downloads:** ${formatNumber(model.downloads)}`);
		if (model.likes) info.push(`**Likes:** ${model.likes.toString()}`);
		if (model.trendingScore) info.push(`**Trending Score:** ${model.trendingScore.toString()}`);

		if (info.length > 0) {
			r.push(info.join(' | '));
			r.push('');
		}

		// Tags
		if (model.tags && model.tags.length > 0) {
			r.push(`**Tags:** ${model.tags.slice(0, TAGS_TO_RETURN).join(', ')}`);
			if (model.tags.length > TAGS_TO_RETURN) {
				r.push(`*and ${(model.tags.length - TAGS_TO_RETURN).toString()} more...*`);
			}
			r.push('');
		}

		// Status indicators
		const status = [];
		if (model.private) status.push('🔐 Private');
		if (status.length > 0) {
			r.push(status.join(' | '));
			r.push('');
		}

		// Dates
		if (model.createdAt) {
			r.push(`**Created:** ${formatDate(model.createdAt)}`);
		}

		r.push(`**Link:** [https://hf.co/${model.id}](https://hf.co/${model.id})`);
		r.push('');
		r.push('---');
		r.push('');
	}

	return {
		formatted: r.join('\n'),
		totalResults: models.length,
		resultsShared: models.length
	};
}
