import {
	ALL_BUILTIN_TOOL_IDS,
	TOOL_ID_GROUPS,
	HUB_INSPECT_TOOL_ID,
	USE_SPACE_TOOL_ID,
	HF_JOBS_TOOL_ID,
	DYNAMIC_SPACE_TOOL_ID,
	MODEL_SEARCH_TOOL_ID,
	DATASET_SEARCH_TOOL_ID,
	DOCS_SEMANTIC_SEARCH_TOOL_ID,
} from '@llmindset/hf-mcp';
import type { AppSettings } from './settings.js';
import { README_INCLUDE_FLAG, GRADIO_IMAGE_FILTER_FLAG } from './behavior-flags.js';

export const BOUQUETS: Record<string, AppSettings> = {
	hf_api: {
		builtInTools: [...TOOL_ID_GROUPS.hf_api],
		spaceTools: [],
	},
	spaces: {
		builtInTools: [...TOOL_ID_GROUPS.spaces],
		spaceTools: [],
	},
	search: {
		builtInTools: [...TOOL_ID_GROUPS.search],
		spaceTools: [],
	},
	docs: {
		builtInTools: [...TOOL_ID_GROUPS.docs],
		spaceTools: [],
	},
	skills: {
		builtInTools: [
			HUB_INSPECT_TOOL_ID,
			README_INCLUDE_FLAG,
			MODEL_SEARCH_TOOL_ID,
			DATASET_SEARCH_TOOL_ID,
			DOCS_SEMANTIC_SEARCH_TOOL_ID,
			HF_JOBS_TOOL_ID,
		],
		spaceTools: [],
	},
	all: {
		builtInTools: [...ALL_BUILTIN_TOOL_IDS],
		spaceTools: [],
	},
	// Test bouquets for README inclusion behavior
	hub_repo_details_readme: {
		builtInTools: [HUB_INSPECT_TOOL_ID, README_INCLUDE_FLAG],
		spaceTools: [],
	},
	hub_repo_details: {
		builtInTools: [HUB_INSPECT_TOOL_ID],
		spaceTools: [],
	},
	no_gradio_images: {
		builtInTools: [GRADIO_IMAGE_FILTER_FLAG],
		spaceTools: [],
	},
	mcp_ui: {
		builtInTools: [USE_SPACE_TOOL_ID],
		spaceTools: [],
	},
	jobs: {
		builtInTools: [HF_JOBS_TOOL_ID],
		spaceTools: [],
	},
	dynamic_space: {
		builtInTools: [DYNAMIC_SPACE_TOOL_ID],
		spaceTools: [],
	},
	proxy: {
		builtInTools: [...TOOL_ID_GROUPS.hf_api],
		spaceTools: [],
	},
};

export type BouquetKey = keyof typeof BOUQUETS;

export interface DirectParamOption {
	label: string;
	param: string;
	description?: string;
}

export interface BouquetPreset {
	key: BouquetKey;
	label: string;
	description: string;
	category: 'core' | 'advanced';
	supportsBouquet: boolean;
	supportsMix: boolean;
	builtInTools: readonly string[];
	directParams?: DirectParamOption[];
}

const PRESET_META: Array<Omit<BouquetPreset, 'builtInTools'>> = [
	{
		key: 'skills',
		label: 'Skills Toolkit',
		description: 'Tools that work well with Hugging Face Skills (https://github.com/huggingface/skills).',
		category: 'core',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'spaces',
		label: 'Spaces Toolkit',
		description: 'Launch, inspect, and manage Spaces from your assistant.',
		category: 'core',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'search',
		label: 'Search Tools',
		description: 'Semantic search across models, datasets, papers, and docs.',
		category: 'core',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'docs',
		label: 'Hugging Face Documentation',
		description: 'Documentation Search and Fetch tools.',
		category: 'core',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'hf_api',
		label: 'Hugging Face MCP Defaults',
		description: 'Balanced search plus repository details for models, datasets, and Spaces.',
		category: 'core',
		supportsBouquet: true,
		supportsMix: true,
	},

	// {
	// 	key: 'all',
	// 	label: 'All Built-in Tools',
	// 	description: 'Turn on every MCP tool shipped with the server.',
	// 	category: 'core',
	// 	supportsBouquet: true,
	// 	supportsMix: true,
	// },
	// {
	// 	key: 'hub_repo_details_readme',
	// 	label: 'Hub Repo + README',
	// 	description: 'Return repository metadata and README sections (advanced).',
	// 	category: 'advanced',
	// 	supportsBouquet: true,
	// 	supportsMix: true,
	// },
	// {
	// 	key: 'hub_repo_details',
	// 	label: 'Hub Repo Details Only',
	// 	description: 'Limit responses to repository inspection tools.',
	// 	category: 'advanced',
	// 	supportsBouquet: true,
	// 	supportsMix: true,
	// },
	{
		key: 'no_gradio_images',
		label: 'No Gradio Images',
		description: 'Disable image fetching when interacting with Gradio Spaces.',
		category: 'advanced',
		supportsBouquet: false,
		supportsMix: false,
		directParams: [
			{
				label: 'Disable Gradio images',
				param: 'no_image_content=true',
				description: 'Strip image content returned by Gradio endpoints.',
			},
		],
	},
	{
		key: 'mcp_ui',
		label: 'MCP UI Preview',
		description:
			"Enable the MCP UI 'use_space' tool (Use with an MCP-UI client - see https://mcpui.dev/guide/supported-hosts).",
		category: 'advanced',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'jobs',
		label: 'Run and Manage Jobs',
		description: 'Run, monitor and schedule jobs on Hugging Face infrastructure.',
		category: 'advanced',
		supportsBouquet: true,
		supportsMix: true,
	},
	{
		key: 'proxy',
		label: 'Proxy Tools',
		description: 'Streamable HTTP proxy tools configured via PROXY_TOOLS_CSV.',
		category: 'advanced',
		supportsBouquet: true,
		supportsMix: true,
	},
];

export const BOUQUET_PRESETS: BouquetPreset[] = PRESET_META.map((preset) => {
	const config = BOUQUETS[preset.key];
	return {
		...preset,
		builtInTools: config ? [...config.builtInTools] : [],
		directParams: preset.directParams ? preset.directParams.map((option) => ({ ...option })) : undefined,
	};
});

export type ConfigEntryKind = 'tool' | 'behavior-flag';

export interface ConfigEntryDescription {
	id: string;
	label: string;
	description?: string;
	kind: ConfigEntryKind;
}

const TOOL_DESCRIPTIONS: Record<string, Omit<ConfigEntryDescription, 'id' | 'kind'>> = {
	space_search: {
		label: 'Space Search',
		description: 'Semantic search across public Spaces on the Hugging Face Hub.',
	},
	model_search: {
		label: 'Model Search',
		description: 'Find models on the Hub by keyword or capability.',
	},
	model_details: {
		label: 'Model Details',
		description: 'Retrieve detailed metadata for a specific model repository.',
	},
	paper_search: {
		label: 'Paper Search',
		description: 'Discover research papers relevant to your query.',
	},
	dataset_search: {
		label: 'Dataset Search',
		description: 'Explore datasets published on the Hub.',
	},
	dataset_details: {
		label: 'Dataset Details',
		description: 'Inspect dataset metadata and card information.',
	},
	duplicate_space: {
		label: 'Duplicate Space',
		description: 'Clone a Space into your namespace for customization.',
	},
	space_info: {
		label: 'Space Info',
		description: 'List Spaces for a username or organization.',
	},
	space_files: {
		label: 'Space Files',
		description: 'Browse the file structure of a Space repository.',
	},
	use_space: {
		label: 'Use Space',
		description: 'Launch or interact with a Space through the MCP UI.',
	},
	hf_doc_search: {
		label: 'Docs Search',
		description: 'Search the Hugging Face documentation site.',
	},
	hf_doc_fetch: {
		label: 'Docs Fetch',
		description: 'Retrieve full documentation pages for follow-up analysis.',
	},
	hub_repo_details: {
		label: 'Hub Repo Details',
		description: 'Inspect metadata for models, datasets, or Spaces on the Hub.',
	},
	hf_jobs: {
		label: 'HF Jobs',
		description: 'Run, monitor and schedule jobs on Hugging Face infrastructure.',
	},
};

const BEHAVIOR_FLAG_DESCRIPTIONS: Record<string, Omit<ConfigEntryDescription, 'id' | 'kind'>> = {
	[README_INCLUDE_FLAG]: {
		label: 'Allow README Include',
		description: 'Permit README sections to be returned in responses (advanced).',
	},
	[GRADIO_IMAGE_FILTER_FLAG]: {
		label: 'Skip Gradio Images',
		description: 'Prevent image downloads from Gradio endpoints (advanced).',
	},
};

export function describeConfigEntry(id: string): ConfigEntryDescription {
	const tool = TOOL_DESCRIPTIONS[id];
	if (tool) {
		return {
			id,
			kind: 'tool',
			...tool,
		};
	}
	const flag = BEHAVIOR_FLAG_DESCRIPTIONS[id];
	if (flag) {
		return {
			id,
			kind: 'behavior-flag',
			...flag,
		};
	}
	return {
		id,
		label: id,
		kind: 'tool',
	};
}
