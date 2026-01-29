import { EventEmitter } from 'events';
import { logger } from './logger.js';
import type { AppSettings } from '../../shared/settings.js';
import type { TransportInfo } from '../../shared/transport-info.js';
import { BOUQUET_FALLBACK } from '../mcp-server.js';
import { ALL_BUILTIN_TOOL_IDS } from '@llmindset/hf-mcp';
import { normalizeBuiltInTools } from '../../shared/tool-normalizer.js';
import { apiMetrics } from '../utils/api-metrics.js';
export interface ToolStateChangeCallback {
	(toolId: string, enabled: boolean): void;
}

export interface GradioEndpoint {
	name: string;
	subdomain: string;
	id?: string;
	emoji?: string;
	isPrivate?: boolean; // unused for the moment, leaving here temporarily
}

export interface ApiClientConfig {
	type: 'polling' | 'external';
	baseUrl?: string;
	pollInterval?: number;
	externalUrl?: string;
	userConfigUrl?: string;
	hfToken?: string;
	staticGradioEndpoints?: GradioEndpoint[];
}

function withNormalizedFlags(settings: AppSettings): AppSettings {
	const normalizedBuiltInTools = normalizeBuiltInTools(settings.builtInTools);
	const isIdentical =
		normalizedBuiltInTools.length === settings.builtInTools.length &&
		normalizedBuiltInTools.every((value, index) => value === settings.builtInTools[index]);
	return isIdentical ? settings : { ...settings, builtInTools: normalizedBuiltInTools };
}

export class McpApiClient extends EventEmitter {
	private config: ApiClientConfig;
	private pollTimer: NodeJS.Timeout | null = null;
	private cache: Map<string, boolean> = new Map();
	private gradioEndpoints: GradioEndpoint[] = [];
	private gradioEndpointStates: Map<number, boolean> = new Map();
	private isPolling = false;
	private transportInfo: TransportInfo | null = null;

	constructor(config: ApiClientConfig, transportInfo?: TransportInfo) {
		super();
		this.config = config;
		this.transportInfo = transportInfo || null;

		// Initialize gradio endpoints from config if provided
		if (config.staticGradioEndpoints) {
			this.gradioEndpoints = [...config.staticGradioEndpoints];
		}
	}

	getTransportInfo(): TransportInfo | null {
		return this.transportInfo;
	}

	async getSettings(overrideToken?: string): Promise<AppSettings> {
		switch (this.config.type) {
			case 'polling':
				if (!this.config.baseUrl) {
					logger.error('baseUrl required for polling mode');
					return withNormalizedFlags(BOUQUET_FALLBACK);
				}
				try {
					const response = await fetch(`${this.config.baseUrl}/api/settings`);
					if (!response.ok) {
						logger.error(`Failed to fetch settings: ${response.status.toString()} ${response.statusText}`);
						return withNormalizedFlags(BOUQUET_FALLBACK);
					}
					return withNormalizedFlags((await response.json()) as AppSettings);
				} catch (error) {
					logger.error({ error }, 'Error fetching settings from local API');
					return withNormalizedFlags(BOUQUET_FALLBACK);
				}

			case 'external':
				if (!this.config.externalUrl) {
					logger.error('externalUrl required for external mode');
					return withNormalizedFlags(BOUQUET_FALLBACK);
				}
				try {
					const token = overrideToken || this.config.hfToken;
					if (!token || token.trim() === '') {
						// Record anonymous access (successful fallback usage)
						apiMetrics.recordCall(false, 200);
						logger.debug('No HF token available for external config API - using fallback');
						return withNormalizedFlags(BOUQUET_FALLBACK);
					}

					const headers: Record<string, string> = {};
					const hasToken = true; // We know we have a token at this point

					headers['Authorization'] = `Bearer ${token}`;

					// Add timeout using HF_API_TIMEOUT or default to 12.5 seconds
					headers['accept'] = 'application/json';
					headers['cache-control'] = 'no-cache';
					const controller = new AbortController();
					const apiTimeout = process.env.HF_API_TIMEOUT ? parseInt(process.env.HF_API_TIMEOUT, 10) : 12500;
					const timeoutId = setTimeout(() => controller.abort(), apiTimeout);
					logger.debug(`Fetching external settings from ${this.config.externalUrl} with timeout ${apiTimeout}ms`);
					const response = await fetch(this.config.externalUrl, {
						headers,
						signal: controller.signal,
					});
					clearTimeout(timeoutId);

					if (!response.ok) {
						// Record metrics for error responses
						apiMetrics.recordCall(hasToken, response.status);

						// Debug level logging for auth errors
						if (response.status === 401 || response.status === 403) {
							logger.debug(`External config API ${response.status} ${response.statusText}: ${this.config.externalUrl}`);
						}

						logger.debug(
							`Failed to fetch external settings: ${response.status.toString()} ${response.statusText} - using fallback bouquet`
						);
						return withNormalizedFlags(BOUQUET_FALLBACK);
					}

					// Record metrics for successful responses
					apiMetrics.recordCall(hasToken, response.status);
					return withNormalizedFlags((await response.json()) as AppSettings);
				} catch (error) {
					logger.warn({ error }, 'Error fetching settings from external API - defaulting to fallback bouquet');
					return withNormalizedFlags(BOUQUET_FALLBACK);
				}

			default:
				logger.error(`Unknown API client type: ${String(this.config.type)}`);
				return withNormalizedFlags(BOUQUET_FALLBACK);
		}
	}

	async getToolStates(overrideToken?: string): Promise<Record<string, boolean> | null> {
		const settings = await this.getSettings(overrideToken);
		if (!settings) {
			return null;
		}
		logger.trace({ settings: settings }, 'Fetched tool settings from API');

		// Update gradio endpoints from external API
		if (settings.spaceTools && settings.spaceTools.length > 0) {
			this.gradioEndpoints = settings.spaceTools.map((spaceTool) => ({
				name: spaceTool.name,
				subdomain: spaceTool.subdomain,
				id: spaceTool._id,
				emoji: spaceTool.emoji,
			}));
			logger.trace({ gradioEndpoints: this.gradioEndpoints }, 'Updated gradio endpoints from external API');
		}

		// Create tool states: enabled tools = true, rest = false
		const toolStates: Record<string, boolean> = {};
		for (const toolId of ALL_BUILTIN_TOOL_IDS) {
			toolStates[toolId] = settings.builtInTools.includes(toolId);
		}

		// Include virtual/behavior flags that aren't real tools (e.g., ALLOW_README_INCLUDE)
		// Anything present in builtInTools but not in ALL_BUILTIN_TOOL_IDS is treated as an enabled flag.
		for (const id of settings.builtInTools) {
			if (!(id in toolStates)) {
				toolStates[id] = true;
			}
		}
		return toolStates;
	}

	getGradioEndpoints(): GradioEndpoint[] {
		return this.gradioEndpoints;
	}

	updateGradioEndpointState(index: number, enabled: boolean): void {
		if (index >= 0 && index < this.gradioEndpoints.length) {
			this.gradioEndpointStates.set(index, enabled);
			const endpoint = this.gradioEndpoints[index];
			if (endpoint) {
				logger.info(`Gradio endpoint ${(index + 1).toString()} set to ${enabled ? 'enabled' : 'disabled'}`);
			}
		}
	}

	updateGradioEndpoint(index: number, endpoint: GradioEndpoint): void {
		if (index >= 0 && index < this.gradioEndpoints.length) {
			this.gradioEndpoints[index] = endpoint;
			logger.info(`Gradio endpoint ${(index + 1).toString()} updated to ${endpoint.name}`);
		}
	}

	async startPolling(onUpdate: ToolStateChangeCallback): Promise<void> {
		if (this.isPolling) {
			logger.warn('Polling already started');
			return;
		}

		this.isPolling = true;

		// Handle different modes

		// For external mode, don't fetch on startup - wait for user access
		if (this.config.type === 'external') {
			logger.debug('Using external user config API - no startup fetching, will fetch on first user request');
			return;
		}

		const pollInterval = this.config.pollInterval || 5000;
		logger.info(`Starting API polling with interval ${pollInterval.toString()}ms`);

		// Initial fetch to populate cache
		const initialStates = await this.getToolStates();
		if (initialStates) {
			for (const [toolId, enabled] of Object.entries(initialStates)) {
				this.cache.set(toolId, enabled);
				// Call the callback for initial state
				onUpdate(toolId, enabled);
			}
		}

		// Start polling (we've already handled static mode above)
		this.pollTimer = setInterval(() => {
			void (async () => {
				const states = await this.getToolStates();
				if (!states) {
					logger.warn('Failed to fetch tool states during polling');
					return;
				}

				// Check for changes
				for (const [toolId, enabled] of Object.entries(states)) {
					const cachedState = this.cache.get(toolId);
					if (cachedState !== enabled) {
						logger.info(`Tool ${toolId} state changed: ${String(cachedState)} -> ${String(enabled)}`);
						this.cache.set(toolId, enabled);
						onUpdate(toolId, enabled);
						// Only emit events in external mode - in polling mode, web server handles immediate events
						if (this.config.type === 'external') {
							this.emit('toolStateChange', toolId, enabled);
						}
					}
				}

				// Check for removed tools
				for (const [toolId, _] of this.cache) {
					if (!(toolId in states)) {
						logger.info(`Tool ${toolId} removed from settings`);
						this.cache.delete(toolId);
					}
				}
			})();
		}, pollInterval);
	}

	stopPolling(): void {
		if (this.pollTimer) {
			clearInterval(this.pollTimer);
			this.pollTimer = null;
			this.isPolling = false;
			logger.info('Stopped API polling');
		}
	}

	destroy(): void {
		this.stopPolling();
		this.cache.clear();
	}
}
