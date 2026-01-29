import { z } from 'zod';
import { datasetInfo, HubApiError } from '@huggingface/hub';
import { formatDate, formatNumber } from './utilities.js';
import type { ToolResult } from './types/tool-result.js';
import { fetchReadmeContent } from './readme-utils.js';

// Dataset Detail Tool Configuration
export const DATASET_DETAIL_TOOL_CONFIG = {
	name: 'dataset_details',
	description: 'Get detailed information about a specific dataset on Hugging Face Hub.',
	schema: z.object({
		dataset_id: z.string().min(5, 'Dataset ID is required').describe('The Dataset ID (e.g. Anthropic/hh-rlhf, squad)'),
	}),
	annotations: {
		title: 'Dataset Details',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: false,
	},
} as const;

export const DATASET_DETAIL_PROMPT_CONFIG = {
	name: 'Dataset Details',
	title: 'Dataset Details',
	description:
		'Get detailed information about a dataset from the Hugging Face Hub. Includes README from the repository - review before use.',
	schema: z.object({
		dataset_id: z
			.string()
			.min(3, 'Dataset ID is required')
			.max(100)
			.describe("The Dataset ID (e.g. 'Anthropic/hh-rlhf', 'squad')"),
	}),
};

export type DatasetDetailParams = z.infer<typeof DATASET_DETAIL_TOOL_CONFIG.schema>;

// Clean interface design with explicit data availability

// Required core information that should always be available
interface DatasetBasicInfo {
	id: string; // Dataset ID
	name: string; // Dataset name
	downloads: number;
	likes: number;
	private: boolean;
	gated: false | 'auto' | 'manual';
	updatedAt: Date;
}

// Optional but reliable information with simple types
interface DatasetExtendedInfo {
	author?: string;
	downloadsAllTime?: number;
	tags?: string[];
	description?: string;
}

// Dataset card data with careful extraction
interface DatasetMetadata {
	language?: string | string[];
	license?: string | string[];
	task_categories?: string | string[];
	size_categories?: string | string[];
	dataset_info?: Record<string, unknown>;
}

// Complete dataset information structure
interface DatasetInformation extends DatasetBasicInfo {
	extended?: DatasetExtendedInfo;
	metadata?: DatasetMetadata;
}

/**
 * Service for getting detailed dataset information using the official huggingface.js library
 */
export class DatasetDetailTool {
	private readonly hubUrl?: string;
	private readonly accessToken?: string;

	/**
	 * Creates a new dataset detail service
	 * @param hfToken Optional Hugging Face token for API access
	 * @param hubUrl Optional custom hub URL
	 */
	constructor(hfToken?: string, hubUrl?: string) {
		this.accessToken = hfToken;
		this.hubUrl = hubUrl;
	}

	/**
	 * Get detailed information about a specific dataset
	 *
	 * @param datasetId The dataset ID to get details for (e.g., squad, glue, imdb)
	 * @param includeReadme Whether to include README content (default: false)
	 * @returns ToolResult with formatted dataset details
	 */
	async getDetails(datasetId: string, includeReadme: boolean = false): Promise<ToolResult> {
		try {
			// Define additional fields we want to retrieve (only those available in the hub library)
			const additionalFields = ['author', 'downloadsAllTime', 'tags', 'description', 'cardData'] as const;

			const datasetData = await datasetInfo<(typeof additionalFields)[number]>({
				name: datasetId,
				additionalFields: Array.from(additionalFields),
				...(this.accessToken && { credentials: { accessToken: this.accessToken } }),
				...(this.hubUrl && { hubUrl: this.hubUrl }),
			});

			// Build the structured dataset information
			const datasetDetails: DatasetInformation = {
				// Basic info (required fields)
				id: datasetId,
				name: datasetData.name,
				downloads: datasetData.downloads,
				likes: datasetData.likes,
				private: datasetData.private,
				gated: datasetData.gated,
				updatedAt: datasetData.updatedAt,

				// Extended info (optional but reliable fields)
				extended: {
					author: datasetData.author,
					downloadsAllTime: datasetData.downloadsAllTime,
					tags: datasetData.tags,
					description: datasetData.description,
				},
			};

			// Metadata from card data
			if (datasetData.cardData) {
				const metadata: DatasetMetadata = {};
				const cardData = datasetData.cardData as Record<string, unknown>;

				if ('language' in cardData) {
					metadata.language = cardData.language as string | string[];
				}

				if ('license' in cardData) {
					metadata.license = cardData.license as string | string[];
				}

				if ('task_categories' in cardData) {
					metadata.task_categories = cardData.task_categories as string | string[];
				}

				if ('size_categories' in cardData) {
					metadata.size_categories = cardData.size_categories as string | string[];
				}

				if ('dataset_info' in cardData) {
					metadata.dataset_info = cardData.dataset_info as Record<string, unknown>;
				}

				// Only add metadata section if we have data
				if (Object.keys(metadata).length > 0) {
					datasetDetails.metadata = metadata;
				}
			}

			// Note: siblings information is not available through the additional fields API
			// It would require a separate API call to list files

			// Fetch and append README content if requested
			if (includeReadme) {
				const readmeContent = await fetchReadmeContent(datasetDetails.name, 'datasets', false);
				if (readmeContent) {
					const result = formatDatasetDetails(datasetDetails);
					result.formatted +=
						'\n\n## README\n<datasetcard-readme>\n' + readmeContent.trim() + '\n</datasetcard-readme>';
					return result;
				}
			}

			return formatDatasetDetails(datasetDetails);
		} catch (error) {
			if (error instanceof Error) {
				const msg = error.message || '';
				// Map well-known patterns and status codes to friendly messages
				const isNotFound =
					(error instanceof HubApiError && error.statusCode === 404) ||
					msg.includes('404') ||
					msg.includes('Not Found') ||
					msg.includes('Repository not found');

				if (isNotFound) {
					throw new Error(`Dataset '${datasetId}' not found. Please check the dataset ID.`);
				}

				const isUnauthorized =
					(error instanceof HubApiError && (error.statusCode === 401 || error.statusCode === 403)) ||
					msg.includes('401') ||
					msg.includes('403') ||
					msg.includes('username') ||
					msg.includes('password') ||
					msg.includes('Your access token must start with');

				if (isUnauthorized) {
					throw new Error(`Authentication required or insufficient permissions to access dataset '${datasetId}'.`);
				}

				throw new Error(`Failed to get dataset details: ${msg}`);
			}
			throw error;
		}
	}
}

// Formatting Function
function formatDatasetDetails(dataset: DatasetInformation): ToolResult {
	const r: string[] = [];
	const [authorFromName] = dataset.name.includes('/') ? dataset.name.split('/') : ['', dataset.name];

	r.push(`# ${dataset.name}`);
	r.push('');

	// Description if available
	if (dataset.extended?.description) {
		r.push('## Description');
		r.push(dataset.extended.description);
		r.push('');
	}

	// Overview section - using only reliable fields
	r.push('## Overview');

	// Author - from extended info or parsed from name
	if (dataset.extended?.author || authorFromName) {
		r.push(`- **Author:** ${dataset.extended?.author || authorFromName || ''}`);
	}

	// Statistics
	const stats = [];
	if (dataset.extended?.downloadsAllTime) {
		stats.push(`**Downloads:** ${formatNumber(dataset.extended.downloadsAllTime)}`);
	}
	if (dataset.likes) {
		stats.push(`**Likes:** ${dataset.likes.toString()}`);
	}
	if (stats.length > 0) {
		r.push(`- ${stats.join(' | ')}`);
	}

	// Dates
	r.push(`- **Updated:** ${formatDate(dataset.updatedAt)}`);

	// Status indicators
	const status = [];
	if (dataset.gated) status.push('🔒 Gated');
	if (dataset.private) status.push('🔐 Private');
	if (status.length > 0) {
		r.push(`- **Status:** ${status.join(' | ')}`);
	}
	r.push('');

	// Tags - reliable field from extended info
	if (dataset.extended?.tags && dataset.extended.tags.length > 0) {
		r.push('## Tags');
		r.push(dataset.extended.tags.map((tag) => `\`${tag}\``).join(' '));
		r.push('');
	}

	// Metadata - carefully extracted and validated
	if (dataset.metadata) {
		const metadata = [];

		if (dataset.metadata.language) {
			const languages = Array.isArray(dataset.metadata.language)
				? dataset.metadata.language.join(', ')
				: dataset.metadata.language;
			metadata.push(`- **Language:** ${languages}`);
		}

		if (dataset.metadata.license) {
			const license = Array.isArray(dataset.metadata.license)
				? dataset.metadata.license.join(', ')
				: dataset.metadata.license;
			metadata.push(`- **License:** ${license}`);
		}

		if (dataset.metadata.task_categories) {
			const tasks = Array.isArray(dataset.metadata.task_categories)
				? dataset.metadata.task_categories.join(', ')
				: dataset.metadata.task_categories;
			metadata.push(`- **Task Categories:** ${tasks}`);
		}

		if (dataset.metadata.size_categories) {
			const size = Array.isArray(dataset.metadata.size_categories)
				? dataset.metadata.size_categories.join(', ')
				: dataset.metadata.size_categories;
			metadata.push(`- **Size Category:** ${size}`);
		}

		if (metadata.length > 0) {
			r.push('## Metadata');
			r.push(...metadata);
			r.push('');
		}
	}

	// Link is reliable - based on dataset name which is required
	r.push(`**Link:** [https://hf.co/datasets/${dataset.name}](https://hf.co/datasets/${dataset.name})`);

	return {
		formatted: r.join('\n'),
		totalResults: 1, // Dataset was found
		resultsShared: 1, // All details shared
	};
}
