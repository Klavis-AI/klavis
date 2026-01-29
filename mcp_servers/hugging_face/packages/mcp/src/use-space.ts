import { z } from 'zod';
import { HfApiCall } from './hf-api-call.js';
import { spaceInfo, type SpaceEntry } from '@huggingface/hub';
import type { ToolResult } from './types/tool-result.js';
import { createUIResource } from '@mcp-ui/server';
// Define the return type that matches MCP server expectations
interface UseSpaceResult {
	[x: string]: unknown;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	content: Array<{ type: 'text'; text: string } | { type: 'resource'; resource: any }>;
	metadata: ToolResult;
}

export interface UseSpaceParams {
	space_id: string;
}

export const USE_SPACE_TOOL_CONFIG = {
	name: 'use_space',
	description:
		'Give the User access to a Hugging Face Space with mcp_ui. This tool will return a link accessible to the User that may not be visible to the Assistant',
	schema: z.object({
		space_id: z.string().min(1).describe("Space ID in 'username/repo' format"),
	}),
	annotations: {
		title: 'Use Hugging Face Space',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: false,
	},
} as const;

export class UseSpaceTool extends HfApiCall<UseSpaceParams, UseSpaceResult> {
	constructor(hfToken?: string, hubUrl?: string) {
		super('https://huggingface.co/api', hfToken);
		this.hubUrl = hubUrl;
	}

	private readonly hubUrl?: string;

	async getSpaceStatus(spaceId: string): Promise<UseSpaceResult> {
		try {
			// Fetch space info with runtime and subdomain fields
			const additionalFields = ['runtime', 'subdomain'] as const;
			const info = (await spaceInfo<(typeof additionalFields)[number]>({
				name: spaceId,
				additionalFields: Array.from(additionalFields),
				...(this.hubUrl && { hubUrl: this.hubUrl }),
			})) as SpaceEntry & {
				runtime?: {
					stage?: string;
				};
				subdomain?: string;
			};

			// Extract runtime status and subdomain with proper typing
			const status = info.runtime?.stage || 'UNKNOWN';
			const subdomain = info.subdomain || 'Not available';
			const spaceName = spaceId; // Full space ID like 'username/spacename'

			if (status === 'RUNNING' && subdomain !== 'Not available') {
				// Create UI resource for running space
				const iframeUrl = `https://${subdomain}.hf.space`;
				const uiResource = createUIResource({
					uri: `ui://hf-space/${spaceId.replace('/', '-')}`,
					content: { type: 'externalUrl', iframeUrl },
					encoding: 'text',
					uiMetadata: {
						'preferred-frame-size': ['1024px', '960px'],
					},
				});

				const formatted = `UI resource for running space: ${iframeUrl}`;
				return {
					content: [uiResource],
					metadata: {
						formatted,
						totalResults: 1,
						resultsShared: 1,
					},
				};
			} else {
				// Return text response for non-running spaces
				const formatted = `Space ${spaceName} is ${status}`;
				return {
					content: [{ type: 'text', text: formatted }],
					metadata: {
						formatted,
						totalResults: 1,
						resultsShared: 1,
					},
				};
			}
		} catch (error) {
			if (error instanceof Error) {
				throw new Error(`Failed to get space information for '${spaceId}': ${error.message}`);
			}
			throw error;
		}
	}
}

export const formatUseSpaceResult = async (tool: UseSpaceTool, params: UseSpaceParams): Promise<UseSpaceResult> => {
	return tool.getSpaceStatus(params.space_id);
};
