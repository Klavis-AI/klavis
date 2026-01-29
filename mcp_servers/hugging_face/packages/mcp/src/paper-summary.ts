import { z } from 'zod';
import { HfApiCall, HfApiError } from './hf-api-call.js';
import { formatDate, formatNumber, escapeMarkdown } from './utilities.js';
import { ModelSearchTool } from './model-search.js';
import { DatasetSearchTool } from './dataset-search.js';
import { SpaceSearchTool } from './space-search.js';
import { authors, type Author } from './paper-search.js';

// Paper Summary Prompt Configuration
export const PAPER_SUMMARY_PROMPT_CONFIG = {
	name: 'Paper Summary',
	description:
		'Generate a comprehensive summary of an arXiv paper including its details and related models, datasets, and spaces on Hugging Face. ' +
		'Accepts various formats: "2502.16161", "arxiv:2502.16161", "https://arxiv.org/abs/2502.16161", or Hugging Face paper URLs.',
	schema: z.object({
		paper_id: z
			.string()
			.min(1, 'Paper ID is required')
			.describe('arXiv paper ID in various formats (e.g., "2502.16161", "arxiv:2502.16161", or full URL)')
			.max(60)
			.describe('Maximum length is 100 characters'),
	}),
} as const;

// Define parameter types
export type PaperSummaryParams = z.infer<typeof PAPER_SUMMARY_PROMPT_CONFIG.schema>;

// Paper API response interface
interface PaperDetails {
	id: string;
	title: string;
	authors?: Author[];
	publishedAt: string;
	summary?: string; // This is the abstract field in the API
	upvotes?: number;
	comments?: number;
	pageUrl?: string;
}

/**
 * Validates and extracts arXiv ID from various input formats
 * @param input - The user input (arXiv ID or URL)
 * @returns The extracted arXiv ID in format "YYMM.NNNNN"
 * @throws Error if input is invalid
 */
export function extractArxivIdFromInput(input: string): string {
	// Remove whitespace
	const trimmed = input.trim();

	// Check for empty input
	if (!trimmed) {
		throw new Error('Paper ID is required');
	}

	// Pattern for valid arXiv ID: YYMM.NNNNN (e.g., 2502.16161)
	const arxivPattern = /^\d{4}\.\d{4,5}$/;

	// Check if it's already a plain arXiv ID
	if (arxivPattern.test(trimmed)) {
		return trimmed;
	}

	// Handle URL formats first - check if it looks like a URL
	// Check for: protocol, www prefix, domain pattern with TLD, or path separator
	const urlPattern = /^(https?:\/\/|www\.)|^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\/|$)/;
	if (urlPattern.test(trimmed) || trimmed.includes('://')) {
		let url: URL;
		try {
			// Try to parse as URL, adding protocol if missing
			if (!trimmed.startsWith('http')) {
				url = new URL(`https://${trimmed}`);
			} else {
				url = new URL(trimmed);
			}
		} catch {
			throw new Error('Invalid URL format');
		}

		// Check for query parameters or fragments
		if (url.search || url.hash) {
			throw new Error('URL must contain only the paper ID path');
		}

		// Only accept specific domains
		const allowedHosts = ['arxiv.org', 'www.arxiv.org', 'huggingface.co', 'hf.co'];
		if (!allowedHosts.includes(url.hostname)) {
			throw new Error(`URL must be from arxiv.org, huggingface.co, or hf.co. Got: ${url.hostname}`);
		}

		// Handle arxiv.org URLs
		if (url.hostname === 'arxiv.org' || url.hostname === 'www.arxiv.org') {
			// Pattern: /abs/YYMM.NNNNN
			const match = url.pathname.match(/\/abs\/(\d{4}\.\d{4,5})/);
			if (match && match[1]) {
				return match[1];
			}
			throw new Error('arXiv URL must be in format: arxiv.org/abs/YYMM.NNNNN');
		}

		// Handle Hugging Face paper URLs
		if (url.hostname === 'huggingface.co' || url.hostname === 'hf.co') {
			// Pattern: /papers/YYMM.NNNNN
			const match = url.pathname.match(/\/papers\/(\d{4}\.\d{4,5})/);
			if (match && match[1]) {
				return match[1];
			}
			throw new Error('Hugging Face URL must be in format: hf.co/papers/YYMM.NNNNN');
		}

		// This should never be reached due to the allowedHosts check above
		throw new Error('URL does not contain a valid arXiv ID');
	}

	// Handle "arxiv:" prefix variations
	if (trimmed.toLowerCase().startsWith('arxiv:')) {
		const id = trimmed.substring(6);
		if (arxivPattern.test(id)) {
			return id;
		}
		throw new Error('Invalid arXiv ID format after "arxiv:" prefix');
	}

	// Handle "arxiv." prefix (typo)
	if (trimmed.toLowerCase().startsWith('arxiv.')) {
		const id = trimmed.substring(6);
		if (arxivPattern.test(id)) {
			return id;
		}
		throw new Error('Invalid arXiv ID format after "arxiv." prefix');
	}

	// If we get here, it's not a recognized format
	throw new Error(
		`Invalid arXiv ID format: "${trimmed}". Expected formats: "2502.16161", "arxiv:2502.16161", or paper URL`
	);
}

/**
 * Service for generating comprehensive paper summaries
 */
export class PaperSummaryPrompt extends HfApiCall<Record<string, string>, PaperDetails> {
	/**
	 * @param hfToken Optional Hugging Face token for API access
	 */
	constructor(hfToken?: string) {
		super('https://huggingface.co/api/papers', hfToken);
	}

	/**
	 * Generate a comprehensive paper summary
	 */
	async generateSummary(params: PaperSummaryParams): Promise<string> {
		try {
			// Extract and validate arXiv ID
			const arxivId = extractArxivIdFromInput(params.paper_id);

			// Get paper details
			let paperDetails: PaperDetails;
			try {
				paperDetails = await this.getPaperDetails(arxivId);
			} catch (error) {
				if (error instanceof HfApiError && error.status === 404) {
					return "I'm sorry, paper not found.";
				}
				throw error;
			}

			// Build the summary
			const sections: string[] = [];

			// Paper details section
			sections.push(this.formatPaperDetails(paperDetails));

			// Search for related resources
			const relatedResources = await this.getRelatedResources(arxivId);

			// Add related models section if found
			if (relatedResources.models) {
				sections.push(relatedResources.models);
			}

			// Add related datasets section if found
			if (relatedResources.datasets) {
				sections.push(relatedResources.datasets);
			}

			// Add related spaces section if found
			if (relatedResources.spaces) {
				sections.push(relatedResources.spaces);
			}

			// Add reminder about tags
			sections.push(
				'\n**Note:** Tags and paper references on Hugging Face are not always complete or up-to-date. ' +
					'-- validate information if necessary'
			);

			// Add final instruction
			sections.push('\nPlease provide a summary of this paper and any associated resources.');

			return sections.join('\n\n');
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to generate paper summary: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Get paper details from HF API
	 */
	private async getPaperDetails(arxivId: string): Promise<PaperDetails> {
		const url = new URL(`${this.apiUrl}/${arxivId}`);
		return this.fetchFromApi<PaperDetails>(url);
	}

	/**
	 * Format paper details as markdown
	 */
	private formatPaperDetails(paper: PaperDetails): string {
		const lines: string[] = [];

		// Title as main heading
		lines.push(`# ${escapeMarkdown(paper.title || 'Untitled')}`);
		lines.push('');

		// Authors - use the existing authors formatting function
		lines.push(authors(paper.authors));

		// Published date
		lines.push(`**Published:** ${formatDate(paper.publishedAt)}`);

		// Engagement metrics - only show if they exist and are > 0
		if (paper.upvotes && paper.upvotes > 0) {
			lines.push(`**Upvotes:** ${formatNumber(paper.upvotes)}`);
		}
		if (paper.comments && paper.comments > 0) {
			lines.push(`**Comments:** ${formatNumber(paper.comments)}`);
		}

		// Links
		lines.push('');
		lines.push('**Links:**');
		lines.push(`- [Hugging Face Paper Page](https://hf.co/papers/${paper.id})`);
		lines.push(`- [arXiv Page](https://arxiv.org/abs/${paper.id})`);

		// Abstract
		if (paper.summary) {
			lines.push('');
			lines.push('## Abstract');
			lines.push('');
			lines.push(paper.summary);
		}

		return lines.join('\n');
	}

	/**
	 * Search for related resources (models, datasets, spaces)
	 */
	private async getRelatedResources(arxivId: string): Promise<{ models?: string; datasets?: string; spaces?: string }> {
		const results: { models?: string; datasets?: string; spaces?: string } = {};

		// Search for related models
		try {
			const modelSearch = new ModelSearchTool(this.hfToken);
			// Use the filter parameter to search for models referencing this paper
			const modelResults = await modelSearch.searchWithFilter(`arxiv:${arxivId}`, 25);
			if (modelResults && !modelResults.formatted.includes('No models found')) {
				results.models = `## Related Models\n\n${modelResults.formatted}`;
			}
		} catch (error) {
			console.warn(`Failed to fetch related models for paper ${arxivId}:`, error);
		}

		// Search for related datasets
		try {
			const datasetSearch = new DatasetSearchTool(this.hfToken);
			// Use the filter parameter to search for datasets referencing this paper
			const datasetResults = await datasetSearch.searchWithFilter(`arxiv:${arxivId}`, 25);
			if (datasetResults && !datasetResults.formatted.includes('No datasets found')) {
				results.datasets = `## Related Datasets\n\n${datasetResults.formatted}`;
			}
		} catch (error) {
			console.warn(`Failed to fetch related datasets for paper ${arxivId}:`, error);
		}

		// Search for related spaces
		try {
			const spaceSearch = new SpaceSearchTool(this.hfToken);
			// Use the filter parameter to search for spaces referencing this paper
			const spaceResults = await spaceSearch.searchWithFilter(`arxiv:${arxivId}`, 25, 2);
			if (spaceResults && !spaceResults.formatted.includes('No matching Hugging Face Spaces found')) {
				results.spaces = `## Related Spaces\n\n${spaceResults.formatted}`;
			}
		} catch (error) {
			console.warn(`Failed to fetch related spaces for paper ${arxivId}:`, error);
		}

		return results;
	}
}
