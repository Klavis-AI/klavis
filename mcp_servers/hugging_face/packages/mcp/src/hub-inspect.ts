import { z } from 'zod';
import type { ToolResult } from './types/tool-result.js';
import { ModelDetailTool } from './model-detail.js';
import { DatasetDetailTool } from './dataset-detail.js';
import { spaceInfo } from '@huggingface/hub';
import { formatDate } from './utilities.js';

export const HUB_INSPECT_TOOL_CONFIG = {
	name: 'hub_repo_details',
	description:
		'Get details for one or more Hugging Face repos (model, dataset, or space). ' +
		'Auto-detects type unless specified.',
	schema: z.object({
		repo_ids: z
			.array(z.string().min(1))
			.min(1, 'Provide at least one id')
			.max(10, 'Provide at most 10 repo ids')
			.describe('Repo IDs for (models|dataset/space) - usually in author/name format (e.g. openai/gpt-oss-120b)'),
		repo_type: z.enum(['model', 'dataset', 'space']).optional().describe('Specify lookup type; otherwise auto-detects'),
		include_readme: z.boolean().default(false).describe('Include README from the repo'),
	}),
	annotations: {
		title: 'Hub Repo Details',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: false,
	},
} as const;

export type HubInspectParams = z.infer<typeof HUB_INSPECT_TOOL_CONFIG.schema>;

export class HubInspectTool {
	private readonly modelDetail: ModelDetailTool;
	private readonly datasetDetail: DatasetDetailTool;
	private readonly hubUrl?: string;

	constructor(hfToken?: string, hubUrl?: string) {
		this.modelDetail = new ModelDetailTool(hfToken, hubUrl);
		this.datasetDetail = new DatasetDetailTool(hfToken, hubUrl);
		this.hubUrl = hubUrl;
	}

	async inspect(params: HubInspectParams, includeReadme: boolean = false): Promise<ToolResult> {
		const parts: string[] = [];
		let successCount = 0;

		for (const id of params.repo_ids) {
			try {
				const section = await this.inspectSingle(id, params.repo_type, includeReadme);
				parts.push(section);
				successCount += 1;
			} catch (err) {
				const msg = err instanceof Error ? err.message : String(err);
				// Improve error message formatting
				const cleanMsg = msg.replace(/Invalid username or password/g, 'Not found or authentication required');
				parts.push(`# ${id}\n\n- Error: ${cleanMsg}`);
			}
		}

		return {
			formatted: parts.join('\n\n---\n\n'),
			totalResults: params.repo_ids.length,
			resultsShared: successCount,
		};
	}

	private async inspectSingle(
		repoId: string,
		type: 'model' | 'dataset' | 'space' | undefined,
		includeReadme: boolean
	): Promise<string> {
		// If caller constrained the type, do only that
		if (type === 'model') {
			return (await this.modelDetail.getDetails(repoId, includeReadme)).formatted;
		}
		if (type === 'dataset') {
			return (await this.datasetDetail.getDetails(repoId, includeReadme)).formatted;
		}
		if (type === 'space') {
			return await this.getSpaceDetails(repoId);
		}

		// Auto-detect: attempt all three and aggregate. The same id may exist for multiple types.
		const matches: string[] = [];

		try {
			const r = await this.modelDetail.getDetails(repoId, includeReadme);
			matches.push(`**Type: Model**\n\n${r.formatted}`);
		} catch {
			/* not a model */
		}

		try {
			const r = await this.datasetDetail.getDetails(repoId, includeReadme);
			matches.push(`**Type: Dataset**\n\n${r.formatted}`);
		} catch {
			/* not a dataset */
		}

		try {
			const r = await this.getSpaceDetails(repoId);
			matches.push(`**Type: Space**\n\n${r}`);
		} catch {
			/* not a space */
		}

		if (matches.length === 0) {
			throw new Error(`Could not find repo '${repoId}' as model, dataset, or space.`);
		}

		return matches.join('\n\n---\n\n');
	}

	private async getSpaceDetails(spaceId: string): Promise<string> {
		const additionalFields = ['author', 'tags', 'runtime', 'subdomain', 'sha'] as const;
		const info = await spaceInfo<(typeof additionalFields)[number]>({
			name: spaceId,
			additionalFields: Array.from(additionalFields),
			...(this.hubUrl && { hubUrl: this.hubUrl }),
		});

		const lines: string[] = [];
		lines.push(`# ${info.name}`);
		lines.push('');
		lines.push('## Overview');
		interface SpaceExtra {
			author?: string;
			tags?: readonly string[] | string[];
			runtime?: unknown;
			subdomain?: string;
			sha?: string;
		}
		const extra = info as Partial<SpaceExtra>;
		if (extra.author) lines.push(`- **Author:** ${extra.author}`);
		if (info.sdk) lines.push(`- **SDK:** ${info.sdk}`);
		lines.push(`- **Likes:** ${info.likes}`);
		lines.push(`- **Updated:** ${formatDate(info.updatedAt)}`);
		const tags = Array.isArray(extra.tags) ? extra.tags : undefined;
		if (tags && tags.length) lines.push(`- **Tags:** ${tags.join(', ')}`);
		lines.push('');
		lines.push(`**Link:** [https://hf.co/spaces/${info.name}](https://hf.co/spaces/${info.name})`);
		return lines.join('\n');
	}
}
