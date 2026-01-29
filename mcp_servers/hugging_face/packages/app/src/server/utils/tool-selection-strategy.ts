import { logger } from './logger.js';
import type { AppSettings, SpaceTool } from '../../shared/settings.js';
import { ALL_BUILTIN_TOOL_IDS } from '@llmindset/hf-mcp';
import type { McpApiClient } from './mcp-api-client.js';
import { extractAuthBouquetAndMix } from '../utils/auth-utils.js';
import { normalizeBuiltInTools } from '../../shared/tool-normalizer.js';
import { BOUQUETS } from '../../shared/bouquet-presets.js';
import { parseGradioSpaceIds } from './gradio-utils.js';
import { getProxyToolsConfig } from './proxy-tools-config.js';

export enum ToolSelectionMode {
	BOUQUET_OVERRIDE = 'bouquet_override',
	MIX = 'mix',
	EXTERNAL_API = 'external_api',
	INTERNAL_API = 'internal_api',
	FALLBACK = 'fallback',
}

export interface ToolSelectionContext {
	headers: Record<string, string> | null;
	userSettings?: AppSettings;
	hfToken?: string;
}

export interface ToolSelectionResult {
	mode: ToolSelectionMode;
	enabledToolIds: string[];
	reason: string;
	baseSettings?: AppSettings;
	mixedBouquet?: string[];
	gradioSpaceTools?: SpaceTool[];
}

/**
 * Tool Selection Strategy - implements clear precedence rules for tool selection
 *
 * ## Two Independent Systems
 *
 * 1. **Built-in Tool Selection** (handled by this class):
 *    - Controlled by: bouquet, mix, and user settings
 *    - Affects: Built-in HuggingFace MCP tools only
 *    - Returns: enabledToolIds array
 *
 * 2. **Gradio Endpoint Registration** (handled by mcp-proxy.ts):
 *    - Controlled by: gradio parameter + user settings spaceTools
 *    - Affects: Dynamic Gradio Space endpoints
 *    - Works with any bouquet when explicitly specified via gradio=
 *    - Special: gradio="none" disables all Gradio endpoints
 *
 * ## Precedence for Built-in Tools
 *
 * 1. BOUQUET_OVERRIDE (highest) - Completely replaces tool selection
 * 2. MIX - Adds mix bouquet tools to user settings
 * 3. USER_SETTINGS - Uses external or internal API settings
 * 4. FALLBACK (lowest) - All tools enabled when no config available
 *
 * ## Gradio Parameter Behavior
 *
 * - When `gradio=foo/bar` is **explicitly specified**, those endpoints are always included
 * - When `bouquet=search` (no gradio param), Gradio endpoints from settings are skipped
 * - When `bouquet=all`, Gradio endpoints from user settings are included
 * - Examples:
 *   - `bouquet=search&gradio=microsoft/Florence-2-large` → search tools + Florence endpoint ✓
 *   - `bouquet=hf_api&gradio=foo/bar` → hf_api tools + foo/bar endpoint ✓
 *   - `bouquet=search` (no gradio param) → search tools only ✓
 *   - `bouquet=all` → all tools + gradio endpoints from settings ✓
 *
 * The gradio parameter is parsed here for metadata/logging purposes only.
 * Actual endpoint registration happens in mcp-proxy.ts.
 */
export class ToolSelectionStrategy {
	private apiClient: McpApiClient;

	constructor(apiClient: McpApiClient) {
		this.apiClient = apiClient;
	}

	/**
	 * Parses gradio parameter to extract space IDs for metadata/logging.
	 * Note: This does NOT fetch real subdomains from the API - it's for reporting only.
	 * Real subdomain fetching happens in mcp-proxy.ts via parseAndFetchGradioEndpoints.
	 *
	 * @param gradioParam Comma-delimited list of space IDs (e.g., "microsoft/Florence-2-large")
	 * @returns Array of SpaceTool objects with placeholder subdomains for metadata
	 */
	private parseGradioEndpoints(gradioParam: string): SpaceTool[] {
		// Use shared parsing logic to extract space IDs
		const parsedSpaces = parseGradioSpaceIds(gradioParam);

		// Convert to SpaceTool format for metadata (subdomain is placeholder only)
		return parsedSpaces.map((space) => {
			// Use a placeholder subdomain for metadata purposes only
			// Real subdomains are fetched from the API in mcp-proxy.ts
			const placeholderSubdomain = space.name.replace(/[/]/g, '-');

			return {
				_id: `gradio_metadata_${placeholderSubdomain}`,
				name: space.name,
				subdomain: placeholderSubdomain,
				emoji: '🔧',
			};
		});
	}

	/**
	 * Applies SEARCH_ENABLES_FETCH logic if enabled
	 * If hf_doc_search is enabled and SEARCH_ENABLES_FETCH=true, also enable hf_doc_fetch
	 */
	private applySearchEnablesFetch(enabledToolIds: string[]): string[] {
		if (process.env.SEARCH_ENABLES_FETCH === 'true') {
			if (enabledToolIds.includes('hf_doc_search') && !enabledToolIds.includes('hf_doc_fetch')) {
				logger.debug('SEARCH_ENABLES_FETCH: Auto-enabling hf_doc_fetch because hf_doc_search is enabled');
				return [...enabledToolIds, 'hf_doc_fetch'];
			}
		}
		return enabledToolIds;
	}

	private getProxyToolNames(): string[] {
		return getProxyToolsConfig().map((tool) => tool.toolName);
	}

	private appendProxyTools(enabledToolIds: string[]): string[] {
		const proxyToolNames = this.getProxyToolNames();
		if (proxyToolNames.length === 0) {
			return enabledToolIds;
		}
		return normalizeBuiltInTools([...enabledToolIds, ...proxyToolNames]);
	}

	/**
	 * Selects tools based on clear precedence rules:
	 * 1. Bouquet override (highest precedence)
	 * 2. Mix + user settings (additive)
	 * 3. User settings (external/internal API)
	 * 4. Fallback (all tools)
	 *
	 * Note: The `gradio` parameter is parsed and included in the result regardless of
	 * the bouquet/mix/settings selection. The actual endpoint registration in mcp-proxy.ts
	 * will respect the explicit gradio parameter even when a non-"all" bouquet is specified.
	 */
	async selectTools(context: ToolSelectionContext): Promise<ToolSelectionResult> {
		const { bouquet, mix, gradio } = extractAuthBouquetAndMix(context.headers);
		const mixList = mix ?? [];

		// Parse gradio endpoints if provided (independent of bouquet selection)
		// These endpoints will be registered in mcp-proxy.ts unless gradio="none"
		const gradioSpaceTools = gradio ? this.parseGradioEndpoints(gradio) : [];

		const proxyToolNames = this.getProxyToolNames();
		const hasProxyBouquet = bouquet === 'proxy';
		const includesProxyMix = mixList.includes('proxy');

		// 1. Bouquet override (highest precedence)
		if (bouquet && BOUQUETS[bouquet]) {
			let enabledToolIds = normalizeBuiltInTools(
				this.applySearchEnablesFetch(BOUQUETS[bouquet].builtInTools)
			);
			const wantsProxyTools = hasProxyBouquet || includesProxyMix;
			if (wantsProxyTools && proxyToolNames.length > 0) {
				enabledToolIds = this.appendProxyTools(enabledToolIds);
			} else if (wantsProxyTools && proxyToolNames.length === 0) {
				logger.warn('Proxy tools requested but no proxy tools are configured');
			}
			logger.debug(
				{ bouquet, mix: includesProxyMix ? ['proxy'] : [], enabledToolIds, gradioCount: gradioSpaceTools.length },
				'Using bouquet override'
			);
			return {
				mode: ToolSelectionMode.BOUQUET_OVERRIDE,
				enabledToolIds,
				reason: `Bouquet override: ${bouquet}${includesProxyMix ? ' + proxy mix' : ''}${gradioSpaceTools.length > 0 ? ` + ${gradioSpaceTools.length} gradio endpoints` : ''}`,
				gradioSpaceTools: gradioSpaceTools.length > 0 ? gradioSpaceTools : undefined,
			};
		}

		// 2. Get base user settings
		const baseSettings = await this.getUserSettings(context);

		// 3. Apply mix if specified and we have base settings
		if (mixList.length > 0 && baseSettings) {
			const validMixes = mixList.filter((mixName) => {
				const isValid = Boolean(BOUQUETS[mixName]);
				if (!isValid) {
					logger.warn({ mixName }, 'Ignoring invalid mix bouquet name');
				}
				return isValid;
			});

				if (validMixes.length > 0) {
					const includesProxyMix = validMixes.includes('proxy');
					const mixedTools = validMixes.flatMap((mixName) => BOUQUETS[mixName]?.builtInTools ?? []);
					const combinedTools = [...new Set([...baseSettings.builtInTools, ...mixedTools])];
					let enabledToolIds = normalizeBuiltInTools(
						this.applySearchEnablesFetch(combinedTools)
					);
					if (includesProxyMix && proxyToolNames.length > 0) {
						enabledToolIds = this.appendProxyTools(enabledToolIds);
					} else if (includesProxyMix && proxyToolNames.length === 0) {
						logger.warn('Proxy mix requested but no proxy tools are configured');
					}

					logger.debug(
						{
							mix: validMixes,
							baseToolCount: baseSettings.builtInTools.length,
							mixToolCount: mixedTools.length,
							finalToolCount: enabledToolIds.length,
						},
						'Applying mix to user settings'
					);

					return {
						mode: ToolSelectionMode.MIX,
						enabledToolIds,
						reason: `User settings + mix(${validMixes.join(',')})${gradioSpaceTools.length > 0 ? ` + ${gradioSpaceTools.length} gradio endpoints` : ''}`,
					baseSettings,
					mixedBouquet: validMixes,
					gradioSpaceTools: gradioSpaceTools.length > 0 ? gradioSpaceTools : undefined,
				};
			}
		}

		// 4. Use base settings if available
		if (baseSettings) {
			const mode = this.apiClient.getTransportInfo()?.externalApiMode
				? ToolSelectionMode.EXTERNAL_API
				: ToolSelectionMode.INTERNAL_API;

			const enabledToolIds = normalizeBuiltInTools(
				this.applySearchEnablesFetch(baseSettings.builtInTools)
			);

			logger.debug(
				{
					mode,
					enabledToolIds,
				},
				'Using user settings'
			);

			return {
				mode,
				enabledToolIds,
				reason:
					mode === ToolSelectionMode.EXTERNAL_API
						? `External API user settings${gradioSpaceTools.length > 0 ? ` + ${gradioSpaceTools.length} gradio endpoints` : ''}`
						: `Internal API user settings${gradioSpaceTools.length > 0 ? ` + ${gradioSpaceTools.length} gradio endpoints` : ''}`,
				baseSettings,
				gradioSpaceTools: gradioSpaceTools.length > 0 ? gradioSpaceTools : undefined,
			};
		}

		// 5. Fallback - all tools enabled
		logger.warn('No settings available, using fallback (all tools enabled)');
		const enabledToolIds = normalizeBuiltInTools(
			this.applySearchEnablesFetch([...ALL_BUILTIN_TOOL_IDS])
		);
		return {
			mode: ToolSelectionMode.FALLBACK,
			enabledToolIds,
			reason: `Fallback - no settings available${gradioSpaceTools.length > 0 ? ` + ${gradioSpaceTools.length} gradio endpoints` : ''}`,
			gradioSpaceTools: gradioSpaceTools.length > 0 ? gradioSpaceTools : undefined,
		};
	}

	/**
	 * Gets user settings from provided context or API client
	 */
	private async getUserSettings(context: ToolSelectionContext): Promise<AppSettings | null> {
		// Use provided user settings (from proxy mode)
		if (context.userSettings) {
			logger.debug('Using provided user settings');
			return context.userSettings;
		}

		// Fetch from API client (skip in test environment)
		if (process.env.NODE_ENV === 'test' || process.env.VITEST) {
			logger.debug('Skipping API client fetch in test environment');
			return null;
		}

		try {
			const toolStates = await this.apiClient.getToolStates(context.hfToken);
			if (toolStates) {
				const builtInTools = Object.keys(toolStates).filter((id) => toolStates[id]);
				// Note: spaceTools come from gradio endpoints in the API client
				const spaceTools = this.apiClient.getGradioEndpoints().map((endpoint) => ({
					name: endpoint.name,
					subdomain: endpoint.subdomain,
					_id: endpoint.id || endpoint.name,
					emoji: endpoint.emoji || '🛠️',
				}));

				return { builtInTools, spaceTools };
			}
		} catch (error) {
			logger.warn({ error }, 'Failed to fetch user settings from API client');
		}

		return null;
	}
}
