import { z } from 'zod';
import { HfApiCall, HfApiError } from './hf-api-call.js';
import { formatDate, formatNumber } from './utilities.js';
import { ModelSearchTool } from './model-search.js';
import { DatasetSearchTool } from './dataset-search.js';
import { SpaceSearchTool } from './space-search.js';
import { PaperSearchTool } from './paper-search.js';

// User Summary Prompt Configuration
export const USER_SUMMARY_PROMPT_CONFIG = {
	name: 'User Summary',
	description:
		'Generate a summary of a Hugging Face user including their profile, models, datasets, spaces, and papers. ' +
		'Enter either a username (e.g., "clem") or a Hugging Face profile URL (e.g., "hf.co/julien-c" or "huggingface.co/thomwolf").',
	schema: z.object({
		user_id: z
			.string()
			.min(3, 'User ID must be at least 3 characters long')
			.describe('Hugging Face user ID or URL (e.g., "evalstate" or "hf.co/evalstate")')
			.max(60)
			.describe('Maximum length is 30 characters'),
	}),
} as const;

// Define parameter types
export type UserSummaryParams = z.infer<typeof USER_SUMMARY_PROMPT_CONFIG.schema>;

// Organization interface
interface Organization {
	id: string;
	name: string;
	fullname: string;
	avatarUrl?: string;
}

// User overview API response interface
interface UserOverviewResponse {
	_id: string;
	avatarUrl: string;
	isPro: boolean;
	fullname?: string;
	numModels: number;
	numDatasets: number;
	numSpaces: number;
	numDiscussions: number;
	numPapers: number;
	numUpvotes: number;
	numLikes: number;
	numFollowers: number;
	numFollowing: number;
	orgs: Organization[];
	user: string;
	type: string;
	isFollowing: boolean;
	createdAt: string;
	details?: string; // Present for organizations
	name?: string; // Present for organizations
}

/**
 * Validates and extracts user ID from either a plain username or HF URL
 * @param input - The user input (username or URL)
 * @returns The extracted user ID
 * @throws Error if input is invalid
 */
export function extractUserIdFromInput(input: string): string {
	// Remove whitespace
	const trimmed = input.trim();

	// If it doesn't contain a slash, treat as direct username
	if (!trimmed.includes('/')) {
		if (trimmed.length < 3) {
			throw new Error('User ID must be at least 3 characters long');
		}
		// Reject obvious domain names
		if (trimmed.endsWith('.co') || trimmed.endsWith('.com')) {
			throw new Error('URL must contain only the username (e.g., hf.co/username)');
		}
		return trimmed;
	}

	// Handle URL format
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

	// Validate it's a Hugging Face domain
	const validDomains = ['huggingface.co', 'hf.co'];
	if (!validDomains.includes(url.hostname)) {
		throw new Error('URL must be from huggingface.co or hf.co domain');
	}

	// Check for query parameters or fragments
	if (url.search || url.hash) {
		throw new Error('URL must contain only the username (e.g., hf.co/username)');
	}

	// Extract path segments
	const pathSegments = url.pathname.split('/').filter((segment) => segment.length > 0);

	// Must have exactly one path segment (the username)
	if (pathSegments.length !== 1) {
		throw new Error('URL must contain only the username (e.g., hf.co/username)');
	}

	const userId = pathSegments[0];
	if (!userId || userId.length < 3) {
		throw new Error('User ID must be at least 3 characters long');
	}

	return userId;
}

/**
 * Service for generating comprehensive user summaries
 */
export class UserSummaryPrompt extends HfApiCall<Record<string, string>, UserOverviewResponse> {
	/**
	 * @param hfToken Optional Hugging Face token for API access
	 */
	constructor(hfToken?: string) {
		super('https://huggingface.co/api/users', hfToken);
	}

	/**
	 * Generate a comprehensive user summary
	 */
	async generateSummary(params: UserSummaryParams): Promise<string> {
		try {
			// Extract and validate user ID
			const userId = extractUserIdFromInput(params.user_id);

			// Get user overview
			const userOverview = await this.getUserOverview(userId);

			// Build the summary
			const sections: string[] = [];

			// User profile section
			sections.push(this.formatUserProfile(userOverview));

			// Models section (if user has models)
			if (userOverview.numModels > 0) {
				const modelsSection = await this.getModelsSection(userId);
				if (modelsSection) {
					sections.push(modelsSection);
				}
			}

			// Datasets section (if user has datasets)
			if (userOverview.numDatasets > 0) {
				const datasetsSection = await this.getDatasetsSection(userId);
				if (datasetsSection) {
					sections.push(datasetsSection);
				}
			}

			// Spaces section (if user has spaces)
			if (userOverview.numSpaces > 0) {
				const spacesSection = await this.getSpacesSection(userId);
				if (spacesSection) {
					sections.push(spacesSection);
				}
			}

			// Papers section (if user has a full name with >5 characters)
			if (userOverview.fullname && userOverview.fullname.length > 5) {
				const papersSection = await this.getPapersSection(userOverview.fullname);
				if (papersSection) {
					sections.push(papersSection);
				}
			}

			// Add final instruction
			sections.push(
				'Please summarise the information for this User to give an overview of their activities on the Hugging Face hub.'
			);

			return sections.join('\n\n');
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to generate user summary: ${error.message}`);
			}
			throw error;
		}
	}

	/**
	 * Get user overview from HF API, with organization fallback
	 */
	private async getUserOverview(userId: string): Promise<UserOverviewResponse> {
		try {
			const url = new URL(`${this.apiUrl}/${userId}/overview`);
			return await this.fetchFromApi<UserOverviewResponse>(url);
		} catch (error) {
			// Check if error indicates user doesn't exist (404 with specific error message)
			if (error instanceof HfApiError && error.status === 404 && error.responseBody) {
				try {
					const errorData = JSON.parse(error.responseBody) as { error?: string };
					if (errorData.error === 'This user does not exist') {
						// Try organization API
						try {
							const orgUrl = new URL(`https://huggingface.co/api/organizations/${userId}/overview`);
							const orgResponse = await this.fetchFromApi<UserOverviewResponse>(orgUrl);

							// Map organization response to user response format
							return {
								...orgResponse,
								user: orgResponse.name || 'unknown',
								_id: orgResponse.name || 'unknown',
								isPro: false,
								orgs: [],
								type: 'organization',
								createdAt: new Date().toISOString(),
							};
						} catch {
							throw new Error(`Neither user nor organization found for ID: ${userId}`);
						}
					}
				} catch {
					// If we can't parse the response body, fall through to throw original error
				}
			}
			throw error;
		}
	}

	/**
	 * Helper function to add a statistic line if the value is present
	 */
	private addStatIfPresent(lines: string[], label: string, value: number | undefined): void {
		if (value !== undefined && value !== null) {
			lines.push(`- **${label}:** ${formatNumber(value)}`);
		}
	}

	/**
	 * Format user profile information as markdown
	 */
	private formatUserProfile(user: UserOverviewResponse): string {
		const lines: string[] = [];

		// Check if this is an organization
		const isOrganization = user.type === 'organization';

		if (isOrganization) {
			lines.push(`# Organization Profile: ${user.user}`);
			lines.push('');
			lines.push('**Note:** That user ID refers to an Organization.');
			lines.push('');

			if (user.fullname) {
				lines.push(`**Full Name:** ${user.fullname}`);
			}

			lines.push(`**Username:** ${user.user}`);
			if (user.details) {
				lines.push(`**Description:** ${user.details}`);
			}

			// Organization-specific fields
			const orgData = user as unknown as Record<string, unknown>;
			if (typeof orgData.isEnterprise === 'boolean') {
				lines.push(`**Enterprise:** ${orgData.isEnterprise ? 'Yes' : 'No'}`);
			}
			if (typeof orgData.isVerified === 'boolean') {
				lines.push(`**Verified:** ${orgData.isVerified ? 'Yes' : 'No'}`);
			}
		} else {
			lines.push(`# User Profile: ${user.user}`);
			lines.push('');

			if (user.fullname) {
				lines.push(`**Full Name:** ${user.fullname}`);
			}

			lines.push(`**Username:** ${user.user}`);
			lines.push(`**Account Type:** ${user.isPro ? 'Pro' : 'Free'}`);
			lines.push(`**Created:** ${formatDate(user.createdAt)}`);
		}

		lines.push('');

		// Statistics
		lines.push('## Statistics');
		lines.push('');

		this.addStatIfPresent(lines, 'Models', user.numModels);
		this.addStatIfPresent(lines, 'Datasets', user.numDatasets);
		this.addStatIfPresent(lines, 'Spaces', user.numSpaces);

		if (!isOrganization) {
			this.addStatIfPresent(lines, 'Papers', user.numPapers);
			this.addStatIfPresent(lines, 'Discussions', user.numDiscussions);
			this.addStatIfPresent(lines, 'Likes Given', user.numLikes);
			this.addStatIfPresent(lines, 'Upvotes', user.numUpvotes);
			this.addStatIfPresent(lines, 'Following', user.numFollowing);
		}

		this.addStatIfPresent(lines, 'Followers', user.numFollowers);

		// Organization-specific field
		if (isOrganization) {
			const orgData = user as unknown as Record<string, unknown>;
			if (typeof orgData.numUsers === 'number') {
				this.addStatIfPresent(lines, 'Members', orgData.numUsers);
			}
		}

		if (!isOrganization && user.orgs && user.orgs.length > 0) {
			lines.push('');
			const orgNames = user.orgs.map((org) => `[${org.fullname}](https://hf.co/${org.name})`);
			lines.push(`**Organizations:** ${orgNames.join(', ')}`);
		}

		lines.push('');
		lines.push(`**Profile Link:** [https://hf.co/${user.user}](https://hf.co/${user.user})`);

		return lines.join('\n');
	}

	/**
	 * Get models section using existing ModelSearchTool
	 */
	private async getModelsSection(userId: string): Promise<string | null> {
		try {
			const modelSearch = new ModelSearchTool(this.hfToken);
			const results = await modelSearch.searchWithParams({
				author: userId,
				limit: 10,
				sort: 'downloads',
			});

			return `## Models\n\n${results.formatted}`;
		} catch (error) {
			console.warn(`Failed to fetch models for user ${userId}:`, error);
			return null;
		}
	}

	/**
	 * Get datasets section using existing DatasetSearchTool
	 */
	private async getDatasetsSection(userId: string): Promise<string | null> {
		try {
			const datasetSearch = new DatasetSearchTool(this.hfToken);
			const results = await datasetSearch.searchWithParams({
				author: userId,
				limit: 10,
				sort: 'downloads',
			});

			return `## Datasets\n\n${results.formatted}`;
		} catch (error) {
			console.warn(`Failed to fetch datasets for user ${userId}:`, error);
			return null;
		}
	}

	/**
	 * Get spaces section using existing SpaceSearchTool
	 */
	private async getSpacesSection(userId: string): Promise<string | null> {
		try {
			// Note: SpaceSearchTool doesn't have author filter in semantic search
			// We'll search for the user ID as a query term instead
			const spaceSearch = new SpaceSearchTool(this.hfToken);
			const searchResult = await spaceSearch.search(userId, 10);

			if (searchResult.results.length === 0) {
				return null;
			}

			// Filter results to only show spaces by this author
			const userSpaces = searchResult.results.filter(
				(space) => space.author === userId || space.id.startsWith(`${userId}/`)
			);

			if (userSpaces.length === 0) {
				return null;
			}

			// Use the existing formatting from space-search.ts
			const { formatSearchResults } = await import('./space-search.js');
			const formattedResults = formatSearchResults(userId, userSpaces, userSpaces.length);

			return `## Spaces\n\n${formattedResults.formatted}`;
		} catch (error) {
			console.warn(`Failed to fetch spaces for user ${userId}:`, error);
			return null;
		}
	}

	/**
	 * Get papers section using existing PaperSearchTool
	 */
	private async getPapersSection(fullname: string): Promise<string | null> {
		try {
			const paperSearch = new PaperSearchTool(this.hfToken);
			const results = await paperSearch.search(fullname, 10, false);

			// Check if results indicate no papers found
			if (results.formatted.includes('No papers found')) {
				return null;
			}

			return `## Papers\n\n${results.formatted}`;
		} catch (error) {
			console.warn(`Failed to fetch papers for ${fullname}:`, error);
			return null;
		}
	}
}
