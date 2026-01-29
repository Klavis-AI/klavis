import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { formatUnknownDate } from './utilities.js';
import type { ToolResult } from './types/tool-result.js';

// https://github.com/huggingface/huggingface_hub/blob/a26b93e8ba0b51ce76ce5c2044896587c47c6b60/src/huggingface_hub/hf_api.py#L1481-L1542
// Raw JSON response for https://hf.co/api/papers/search?q=llama%203%20herd Llama Herd is ~50,000 tokens
// Raw JSON response for https://hf.co/api/papers/search?q=kazakh -> ~ 9 papers,
// Return papers as delimited markdown (or simplified JSON)
// ---
//
// can we link to Collections, Datasets, Models, Spaces?
// Create a schema validator for search parameters

// 80 papers in full mode is ~ 35,000 tokens
// 105 papers in summary mode is ~ 23094 tokens
// 105 papers in full mode is ~ 45797 tokens

export const DEFAULT_AUTHORS_TO_SHOW = 8;
const RESULTS_TO_RETURN = 10;

export const PAPER_SEARCH_TOOL_CONFIG = {
	name: 'paper_search',
	description:
		'Find Machine Learning research papers on the Hugging Face hub. ' +
		"Include 'Link to paper' When presenting the results. " +
		'Consider whether tabulating results matches user intent.',
	schema: z.object({
		query: z
			.string()
			.min(3, 'Supply at least one search term')
			.max(200, 'Query too long')
			.describe('Semantic Search query'),
		results_limit: z.number().optional().default(12).describe('Number of results to return'),
		concise_only: z
			.boolean()
			.optional()
			.default(false)
			.describe(
				'Return a 2 sentence summary of the abstract. Use for broad search terms which may return a lot of results. Check with User if unsure.'
			),
	}),
	annotations: {
		title: 'Paper Search',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

export interface Author {
	name?: string;
	user?: {
		user: string;
	};
}

interface Paper {
	id: string;
	authors?: Author[];
	publishedAt?: string;
	title?: string;
	summary?: string;
	upvotes?: number;
	ai_keywords?: string[];
	ai_summary?: string;
}

export interface PaperSearchResult {
	paper: Paper;
	numComments?: number;
	isAuthorParticipating?: boolean;
}

// Define input types for paper search
interface PaperSearchParams {
	q: string;
}

/**
 * Service for searching Hugging Face Papers
 */
export class PaperSearchTool extends HfApiCall<PaperSearchParams, PaperSearchResult[]> {
	/**
	 * Creates a new papers search service
	 * @param apiUrl The URL of the Hugging Face papers search API
	 * @param hfToken Optional Hugging Face token for API access
	 */
	constructor(hfToken?: string, apiUrl = 'https://huggingface.co/api/papers/search') {
		super(apiUrl, hfToken);
	}

	/**
	 * Searches for papers on the Hugging Face Hub
	 * @param query Search query string (e.g. "llama", "attention")
	 * @param limit Maximum number of results to return
	 * @returns ToolResult with formatted paper information and metrics
	 */
	async search(query: string, limit: number = RESULTS_TO_RETURN, conciseOnly: boolean = false): Promise<ToolResult> {
		try {
			if (!query) return {
				formatted: 'No query',
				totalResults: 0,
				resultsShared: 0
			};

			const papers = await this.callApi<PaperSearchResult[]>({ q: query });

			if (papers.length === 0) return {
				formatted: `No papers found for query '${query}'`,
				totalResults: 0,
				resultsShared: 0
			};
			return formatSearchResults(query, papers.slice(0, limit), papers.length, conciseOnly);
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to search for papers: ${error.message}`);
			}
			throw error;
		}
	}
}

export function published(publishedDate: string | undefined): string {
	const formatted = formatUnknownDate(publishedDate ?? '');
	return formatted ? `Published on ${formatted}` : 'Publication date not available';
}

function formatSearchResults(
	query: string,
	papers: PaperSearchResult[],
	totalCount: number,
	conciseOnly: boolean = false
): ToolResult {
	const r: string[] = [];
	const showingText =
		papers.length < totalCount
			? `${totalCount} papers matched the query '${query}'. Here are the first ${papers.length} results.`
			: `All ${papers.length} papers that matched the query '${query}'`;
	r.push(showingText);

	for (const result of papers) {
		r.push('');
		r.push('---');
		const title = result.paper.title ?? `Paper ID ${result.paper.id}`;
		r.push('');
		r.push(`## ${title}`);
		r.push('');
		const publishedDate = result.paper.publishedAt
			? `Published on ${published(result.paper.publishedAt)}`
			: 'Publication date not available';
		r.push(publishedDate);
		r.push(authors(result.paper.authors));
		r.push('');
		// Handle concise_only option: use ai_summary when enabled, or fallback to ai_summary if summary is blank
		const useAiSummary = conciseOnly || !result.paper.summary;
		const summaryText = useAiSummary ? result.paper.ai_summary : result.paper.summary;
		const summaryHeader = useAiSummary ? '### AI Generated Summary' : '### Abstract';

		r.push(summaryHeader);
		r.push('');
		r.push(summaryText ?? 'No summary available');
		r.push('');
		r.push(result.paper.ai_keywords ? `**AI Keywords**: ${result.paper.ai_keywords.join(', ')}` : '');

		const upvotes: string =
			result.paper.upvotes && result.paper.upvotes > 0 ? `Upvoted ${result.paper.upvotes} times` : '';

		if (result.numComments && result.numComments > 0) {
			if (result.isAuthorParticipating)
				r.push(`${upvotes}. The authors are participating in a discussion with ${result.numComments} comments.`);
			else r.push(`${upvotes}. There is a community discussion with ${result.numComments} comments.`);
		} else {
			if ('' != upvotes) r.push(upvotes);
		}

		r.push(`**Link to paper:** [https://hf.co/papers/${result.paper.id}](https://hf.co/papers/${result.paper.id})`);
	}
	r.push('');
	r.push('---');
	return {
		formatted: r.join('\n'),
		totalResults: totalCount,
		resultsShared: papers.length
	};
}

export function authors(authors: Author[] | undefined, authorsToShow: number = DEFAULT_AUTHORS_TO_SHOW): string {
	if (!authors || 0 === authors.length) return '**Authors:** Not available';
	const f: string[] = [];
	for (const author of authors.slice(0, authorsToShow)) {
		const profileLink: string = author.user?.user ? ` ([${author.user.user}](https://hf.co/${author.user.user}))` : '';
		const authorName: string = author.name ?? 'Unknown';
		f.push(`${authorName}${profileLink}`);
	}

	if (authors.length > authorsToShow) {
		f.push(`and ${authors.length - authorsToShow} more.`);
	}
	return `**Authors:** ${f.join(', ')}`;
}
