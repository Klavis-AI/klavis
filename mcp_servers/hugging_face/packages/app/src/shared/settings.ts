/**
 * Settings service for the MCP server
 * Manages application settings like enabled search tools
 */

import { ALL_BUILTIN_TOOL_IDS } from '@llmindset/hf-mcp';
import { normalizeBuiltInTools } from './tool-normalizer.js';

// Define the settings types
export interface SpaceTool {
	_id: string;
	name: string;
	subdomain: string;
	emoji: string;
}

export interface AppSettings {
	builtInTools: string[];
	spaceTools: SpaceTool[];
}

// Default space tools (exported for reuse)
export const DEFAULT_SPACE_TOOLS: SpaceTool[] = [
	{
		_id: '6931936f57adaf3524388f9c',
		name: 'mcp-tools/Z-Image-Turbo',
		subdomain: 'mcp-tools-z-image-turbo',
		emoji: '🖼️',
	},

	// {
	// 	_id: '69147d8b8dc517cb9b2d313f',
	// 	name: 'mcp-tools/Qwen-Image-Fast',
	// 	subdomain: 'mcp-tools-qwen-image-fast',
	// 	emoji: '🖼️',
	// },
	// {
	// 	_id: '6755d0d9e0ea01e11fa2a38a',
	// 	name: 'evalstate/flux1_schnell',
	// 	subdomain: 'evalstate-flux1-schnell',
	// 	emoji: '🏎️💨',
	// },
	/*
	{
		_id: '680be03dc38b7fa7d6855910',
		name: 'abidlabs/EasyGhibli',
		subdomain: 'abidlabs-easyghibli',
		emoji: '🦀',
	},
	*/
];

// Default settings
const defaultSettings: AppSettings = {
	builtInTools: normalizeBuiltInTools([...ALL_BUILTIN_TOOL_IDS]),
	spaceTools: [...DEFAULT_SPACE_TOOLS],
};

// In-memory settings store (could be replaced with persistence later)
let settings: AppSettings = { ...defaultSettings };

/** only used in local mode */
export const settingsService = {
	/**
	 * Get all application settings
	 */
	getSettings(): AppSettings {
		return { ...settings };
	},

	/**
	 * Update built-in tools array
	 */
	updateBuiltInTools(builtInTools: string[]): AppSettings {
		const normalized = normalizeBuiltInTools(builtInTools);
		settings = {
			...settings,
			builtInTools: [...normalized],
		};
		return { ...settings };
	},

	/**
	 * Update space tools array
	 */
	updateSpaceTools(spaceTools: SpaceTool[]): AppSettings {
		settings = {
			...settings,
			spaceTools: [...spaceTools],
		};
		return { ...settings };
	},

	/**
	 * Reset all settings to default values
	 */
	resetSettings(): AppSettings {
		settings = { ...defaultSettings };
		return { ...settings };
	},

	/**
	 * Check if a tool is enabled
	 */
	isToolEnabled(toolId: string): boolean {
		return settings.builtInTools.includes(toolId);
	},
};
