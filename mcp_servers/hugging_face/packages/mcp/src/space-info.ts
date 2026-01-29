import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { listSpaces } from '@huggingface/hub';
import type { SpaceEntry, SpaceRuntime, SpaceSdk } from '@huggingface/hub';
import { formatDate, formatNumber, escapeMarkdown, NO_TOKEN_INSTRUCTIONS } from './utilities.js';

interface SpaceReport {
	user: string;
	generatedAt: Date;
	totalSpaces: number;
	publicSpaces: number;
	privateSpaces: number;
	runningSpaces: number;
	totalLikes: number;
	sdkCounts: Record<string, number>;
	spaces: SpaceDetails[];
}

interface SpaceDetails {
	name: string;
	url: string;
	sdk: SpaceSdk | 'unknown'; // Allow 'unknown' in our internal type
	status: SpaceRuntime['stage'] | 'UNKNOWN';
	statusEmoji: string;
	hardware: string;
	storage: string;
	visibility: string;
	likes: number;
	lastModified: string;
}

const STATUS_EMOJI: Record<string, string> = {
	RUNNING: '🟢 Running',
	RUNNING_BUILDING: '🔄 Building',
	SLEEPING: '😴 Sleeping',
	PAUSED: '⏸️ Paused',
	STOPPED: '⏹️ Stopped',
	RUNTIME_ERROR: '❌ Error',
	BUILD_ERROR: '🚫 Build Error',
	BUILDING: '🔨 Building',
	NO_APP_FILE: '📄 No App',
	CONFIG_ERROR: '⚙️ Config Error',
	DELETING: '🗑️ Deleting',
};

export interface SpaceInfoParams {
	username?: string;
}

export const SPACE_INFO_TOOL_CONFIG = {
	name: 'space_info',
	description: '', // This will be dynamically set based on auth
	schema: z.object({
		username: z.string().optional().describe('Username to get spaces for (defaults to authenticated user)'),
	}),
	annotations: {
		title: 'Hugging Face Spaces Information',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: false,
	},
} as const;

export class SpaceInfoTool extends HfApiCall<SpaceInfoParams, SpaceReport> {
	private authenticatedUsername?: string;

	constructor(hfToken?: string, authenticatedUsername?: string) {
		super('https://huggingface.co/api', hfToken);
		this.authenticatedUsername = authenticatedUsername;
	}

	static createToolConfig(username?: string): typeof SPACE_INFO_TOOL_CONFIG {
		const description = username
			? `Tabluate Hugging Face Spaces information for ${username}, or another User.`
			: `Tabluate public Hugging Face Spaces for a specific User. Supply a Hugging Face token or go to https://hf.co/join to create an account to view your own private Spaces.`;
		return {
			...SPACE_INFO_TOOL_CONFIG,
			description: description as '',
		};
	}

	async getSpacesReport(targetUsername?: string): Promise<string> {
		// TODO -- think a bit more about this exact condition
		if (!this.authenticatedUsername && !targetUsername) throw new Error(NO_TOKEN_INSTRUCTIONS);

		const username = targetUsername || this.authenticatedUsername || 'error';
		const spaces: SpaceEntry[] = [];
		const spacesWithRuntime: SpaceDetails[] = [];

		try {
			// Fetch all spaces for the user with runtime info in a single request
			for await (const space of listSpaces({
				search: { owner: username },
				additionalFields: ['runtime', 'subdomain'] as const,
				accessToken: this.hfToken,
			})) {
				spaces.push(space);

				// Use runtime data directly from listSpaces response
				const runtime = space.runtime;
				const hardware = runtime?.hardware?.current || 'cpu-basic';

				spacesWithRuntime.push({
					name: space.name.split('/')[1] || space.name,
					url: `https://huggingface.co/spaces/${space.name}`,
					sdk: space.sdk || 'unknown',
					status: runtime?.stage || 'UNKNOWN',
					statusEmoji: STATUS_EMOJI[runtime?.stage || 'STOPPED'] || '❓ Unknown',
					hardware: hardware,
					storage: runtime?.resources?.requests?.ephemeral || 'None',
					visibility: space.private ? '🔒 Private' : '🌍 Public',
					likes: space.likes,
					lastModified: space.updatedAt ? formatDate(space.updatedAt) : 'Unknown',
				});
			}

			// Calculate statistics
			const report: SpaceReport = {
				user: username,
				generatedAt: new Date(),
				totalSpaces: spaces.length,
				publicSpaces: spaces.filter((s) => !s.private).length,
				privateSpaces: spaces.filter((s) => s.private).length,
				runningSpaces: spacesWithRuntime.filter((s) => s.status === 'RUNNING').length,
				totalLikes: spaces.reduce((sum, s) => sum + s.likes, 0),
				sdkCounts: spaces.reduce(
					(acc, s) => {
						const sdk = s.sdk || 'unknown';
						acc[sdk] = (acc[sdk] || 0) + 1;
						return acc;
					},
					{} as Record<string, number>
				),
				spaces: spacesWithRuntime.sort((a, b) => b.lastModified.localeCompare(a.lastModified)),
			};

			// Generate markdown report
			return this.generateMarkdown(report);
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to get spaces information: ${error.message}`);
			}
			throw error;
		}
	}

	private generateMarkdown(report: SpaceReport): string {
		// Handle case where user has no spaces
		if (report.totalSpaces === 0) {
			return `# Hugging Face Spaces Report
**User**: ${report.user}
**Generated**: ${formatDate(report.generatedAt)}

No spaces were found for user '${report.user}'.

You can create your first Space at [https://huggingface.co/new-space](https://huggingface.co/new-space).`;
		}

		const sdkSummary = Object.entries(report.sdkCounts)
			.filter(([_, count]) => count > 0)
			.map(([sdk, count]) => `${sdk} (${count})`)
			.join(', ');

		let markdown = `# Hugging Face Spaces Report
**User**: ${report.user}
**Generated**: ${formatDate(report.generatedAt)}

## Summary
- **Total Spaces**: ${report.totalSpaces}
- **Public**: ${report.publicSpaces}${report.privateSpaces > 0 ? ` | **Private**: ${report.privateSpaces}` : ''}
- **Currently Running**: ${report.runningSpaces}
- **Total Likes**: ${formatNumber(report.totalLikes)}
- **SDKs**: ${sdkSummary || 'None'}

## All Spaces
| Space | SDK | Status | Hardware | Storage | Visibility | Likes ❤️ | Last Modified |
|-------|-----|--------|----------|---------|------------|----------|--------------|\n`;

		// Add each space as a table row
		for (const space of report.spaces) {
			markdown += `| [${escapeMarkdown(space.name)}](${space.url}) | ${escapeMarkdown(space.sdk)} | ${space.statusEmoji} | ${escapeMarkdown(space.hardware)} | ${escapeMarkdown(space.storage)} | ${space.visibility} | ${space.likes} | ${space.lastModified} |\n`;
		}

		return markdown;
	}
}

export const formatSpaceInfoResult = async (tool: SpaceInfoTool, params: SpaceInfoParams): Promise<string> => {
	return tool.getSpacesReport(params.username);
};
