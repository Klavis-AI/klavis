import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import type { z } from 'zod';
import { createRequire } from 'module';
import { performance } from 'node:perf_hooks';
import { whoAmI, type WhoAmI } from '@huggingface/hub';
import {
	SpaceSearchTool,
	formatSearchResults,
	SEMANTIC_SEARCH_TOOL_CONFIG,
	type SearchParams,
	ModelSearchTool,
	MODEL_SEARCH_TOOL_CONFIG,
	type ModelSearchParams,
	ModelDetailTool,
	MODEL_DETAIL_TOOL_CONFIG,
	MODEL_DETAIL_PROMPT_CONFIG,
	type ModelDetailParams,
	PaperSearchTool,
	PAPER_SEARCH_TOOL_CONFIG,
	DatasetSearchTool,
	DATASET_SEARCH_TOOL_CONFIG,
	type DatasetSearchParams,
	DatasetDetailTool,
	DATASET_DETAIL_TOOL_CONFIG,
	DATASET_DETAIL_PROMPT_CONFIG,
	type DatasetDetailParams,
	HUB_INSPECT_TOOL_CONFIG,
	HubInspectTool,
	type HubInspectParams,
	DuplicateSpaceTool,
	formatDuplicateResult,
	type DuplicateSpaceParams,
	SpaceInfoTool,
	formatSpaceInfoResult,
	SpaceFilesTool,
	type SpaceFilesParams,
	type SpaceInfoParams,
	UseSpaceTool,
	USE_SPACE_TOOL_CONFIG,
	formatUseSpaceResult,
	type UseSpaceParams,
	UserSummaryPrompt,
	USER_SUMMARY_PROMPT_CONFIG,
	type UserSummaryParams,
	PaperSummaryPrompt,
	PAPER_SUMMARY_PROMPT_CONFIG,
	type PaperSummaryParams,
	CONFIG_GUIDANCE,
	TOOL_ID_GROUPS,
	DOCS_SEMANTIC_SEARCH_CONFIG,
	DocSearchTool,
	type DocSearchParams,
	DOC_FETCH_CONFIG,
	DocFetchTool,
	type DocFetchParams,
	HF_JOBS_TOOL_CONFIG,
	HfJobsTool,
	getDynamicSpaceToolConfig,
	SpaceTool,
	type SpaceArgs,
	type InvokeResult,
	type ToolResult,
	VIEW_PARAMETERS,
} from '@llmindset/hf-mcp';

import type { ServerFactory, ServerFactoryResult } from './transport/base-transport.js';
import type { McpApiClient } from './utils/mcp-api-client.js';
import type { WebServer } from './web-server.js';
import { logger } from './utils/logger.js';
import { logSearchQuery, logPromptQuery, logGradioEvent, type QueryLoggerOptions } from './utils/query-logger.js';
import { DEFAULT_SPACE_TOOLS, type AppSettings } from '../shared/settings.js';
import { extractAuthBouquetAndMix } from './utils/auth-utils.js';
import { ToolSelectionStrategy, type ToolSelectionContext } from './utils/tool-selection-strategy.js';
import { hasReadmeFlag } from '../shared/behavior-flags.js';
import { registerCapabilities } from './utils/capability-utils.js';
import { createGradioWidgetResourceConfig } from './resources/gradio-widget-resource.js';
import { applyResultPostProcessing, type GradioToolCallOptions } from './utils/gradio-tool-caller.js';

// Fallback settings when API fails (enables all tools)
export const BOUQUET_FALLBACK: AppSettings = {
	builtInTools: [...TOOL_ID_GROUPS.hf_api],
	spaceTools: DEFAULT_SPACE_TOOLS,
};

// Default tools for unauthenticated users when using external settings API
export const BOUQUET_ANON_DEFAULT: AppSettings = {
	builtInTools: [...TOOL_ID_GROUPS.hf_api],
	spaceTools: DEFAULT_SPACE_TOOLS,
};

// Bouquet configurations moved to tool-selection-strategy.ts

/**
 * Creates a ServerFactory function that produces McpServer instances with all tools registered
 * The shared ApiClient provides global tool state management across all server instances
 */
export const createServerFactory = (_webServerInstance: WebServer, sharedApiClient: McpApiClient): ServerFactory => {
	const require = createRequire(import.meta.url);
	const { version } = require('../../package.json') as { version: string };

	return async (
		headers: Record<string, string> | null,
		userSettings?: AppSettings,
		skipGradio?: boolean,
		sessionInfo?: {
			clientSessionId?: string;
			isAuthenticated?: boolean;
			clientInfo?: { name: string; version: string };
		}
	): Promise<ServerFactoryResult> => {
		logger.debug({ skipGradio, sessionInfo }, '=== CREATING NEW MCP SERVER INSTANCE ===');
		// Extract auth using shared utility
		const { hfToken } = extractAuthBouquetAndMix(headers);

		// Create tool selection strategy
		const toolSelectionStrategy = new ToolSelectionStrategy(sharedApiClient);

		let userInfo: string =
			'The Hugging Face tools are being used anonymously and rate limits apply. ' +
			'Direct the User to set their HF_TOKEN (instructions at https://hf.co/settings/mcp/), or ' +
			'create an account at https://hf.co/join for higher limits.';
		let username: string | undefined;
		let userDetails: WhoAmI | undefined;

		if (hfToken) {
			try {
				userDetails = await whoAmI({ credentials: { accessToken: hfToken } });
				username = userDetails.name;
				userInfo = `Hugging Face tools are being used by authenticated user '${userDetails.name}'`;
			} catch (error) {
				// unexpected - this should have been caught upstream so severity is warn
				logger.warn({ error: (error as Error).message }, `Failed to authenticate with Hugging Face API`);
			}
		}

		// Helper function to build logging options
		const getLoggingOptions = () => {
			const options = {
				clientSessionId: sessionInfo?.clientSessionId,
				isAuthenticated: sessionInfo?.isAuthenticated ?? !!hfToken,
				clientName: sessionInfo?.clientInfo?.name,
				clientVersion: sessionInfo?.clientInfo?.version,
			};
			logger.debug({ sessionInfo, options }, 'Query logging options:');
			return options;
		};

		type QueryLoggerFn = (
			methodName: string,
			query: string,
			parameters: Record<string, unknown>,
			options?: QueryLoggerOptions
		) => void;

		type BaseQueryLoggerOptions = Omit<QueryLoggerOptions, 'durationMs' | 'error'>;

		interface QueryLoggingConfig<T> {
			methodName: string;
			query: string;
			parameters: Record<string, unknown>;
			baseOptions?: BaseQueryLoggerOptions;
			successOptions?: (result: T) => BaseQueryLoggerOptions | void;
		}

		const runWithQueryLogging = async <T>(
			logFn: QueryLoggerFn,
			config: QueryLoggingConfig<T>,
			work: () => Promise<T>
		): Promise<T> => {
			const start = performance.now();
			try {
				const result = await work();
				const durationMs = Math.round(performance.now() - start);
				const successOptions = config.successOptions?.(result) ?? {};
				const { success: successOverride, ...restSuccessOptions } = successOptions;
				const resultHasError =
					typeof result === 'object' &&
					result !== null &&
					'isError' in result &&
					Boolean((result as { isError?: boolean }).isError);
				const successFlag = successOverride ?? !resultHasError;
				logFn(config.methodName, config.query, config.parameters, {
					...config.baseOptions,
					...restSuccessOptions,
					durationMs,
					success: successFlag,
				});
				return result;
			} catch (error) {
				const durationMs = Math.round(performance.now() - start);
				logFn(config.methodName, config.query, config.parameters, {
					...config.baseOptions,
					durationMs,
					success: false,
					error,
				});
				throw error;
			}
		};

		/**
		 *  we will set capabilities below. use of the convenience .tool() registration methods automatically
		 * sets tools: {listChanged: true} .
		 */
		const server = new McpServer(
			{
				name: '@huggingface/mcp-services',
				version: version,
				title: 'Hugging Face',
				websiteUrl: 'https://huggingface.co/mcp',
				icons: [
					{
						src: 'https://huggingface.co/favicon.ico',
					},
				],
			},
			{
				instructions:
					"You have tools for using the Hugging Face Hub. arXiv paper id's are often " +
					'used as references between datasets, models and papers. There are over 100 tags in use, ' +
					"common tags include 'Text Generation', 'Transformers', 'Image Classification' and so on.\n" +
					userInfo,
			}
		);

		interface Tool {
			enable(): void;
			disable(): void;
		}

		// Get tool selection first (needed for runtime configuration like ALLOW_README_INCLUDE)
		const toolSelectionContext: ToolSelectionContext = {
			headers,
			userSettings,
			hfToken,
		};
		const toolSelection = await toolSelectionStrategy.selectTools(toolSelectionContext);
		const rawNoImageHeader = headers?.['x-mcp-no-image-content'];
		const noImageContentHeaderEnabled =
			typeof rawNoImageHeader === 'string' && rawNoImageHeader.trim().toLowerCase() === 'true';

		// Always register all tools and store instances for dynamic control
		const toolInstances: { [name: string]: Tool } = {};

		const whoDescription = userDetails
			? `Hugging Face tools are being used by authenticated user '${username}'`
			: 'Hugging Face tools are being used anonymously and may be rate limited. Call this tool for instructions on joining and authenticating.';

		const response = userDetails ? `You are authenticated as ${username ?? 'unknown'}.` : CONFIG_GUIDANCE;
		server.tool(
			'hf_whoami',
			whoDescription,
			{},
			{ readOnlyHint: true, openWorldHint: false, title: 'Hugging Face User Info' },
			() => {
				return { content: [{ type: 'text', text: response }] };
			}
		);

		/** always leave tool active so flow can complete / allow uid change */
		if (process.env.AUTHENTICATE_TOOL === 'true') {
			server.tool(
				'Authenticate',
				'Authenticate with Hugging Face',
				{},
				{ title: 'Hugging Face Authentication' },
				() => {
					return { content: [{ type: 'text', text: 'You have successfully authenticated' }] };
				}
			);
		}

		server.prompt(
			USER_SUMMARY_PROMPT_CONFIG.name,
			USER_SUMMARY_PROMPT_CONFIG.description,
			USER_SUMMARY_PROMPT_CONFIG.schema.shape,
			async (params: UserSummaryParams) => {
				const summaryText = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: USER_SUMMARY_PROMPT_CONFIG.name,
						query: params.user_id,
						parameters: { user_id: params.user_id },
						baseOptions: getLoggingOptions(),
						successOptions: (text) => ({
							totalResults: 1,
							resultsShared: 1,
							responseCharCount: text.length,
						}),
					},
					async () => {
						const userSummary = new UserSummaryPrompt(hfToken);
						return userSummary.generateSummary(params);
					}
				);

				return {
					description: `User summary for ${params.user_id}`,
					messages: [
						{
							role: 'user' as const,
							content: {
								type: 'text' as const,
								text: summaryText,
							},
						},
					],
				};
			}
		);

		server.prompt(
			PAPER_SUMMARY_PROMPT_CONFIG.name,
			PAPER_SUMMARY_PROMPT_CONFIG.description,
			PAPER_SUMMARY_PROMPT_CONFIG.schema.shape,
			async (params: PaperSummaryParams) => {
				const summaryText = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: PAPER_SUMMARY_PROMPT_CONFIG.name,
						query: params.paper_id,
						parameters: { paper_id: params.paper_id },
						baseOptions: getLoggingOptions(),
						successOptions: (text) => ({
							totalResults: 1,
							resultsShared: 1,
							responseCharCount: text.length,
						}),
					},
					async () => {
						const paperSummary = new PaperSummaryPrompt(hfToken);
						return paperSummary.generateSummary(params);
					}
				);

				return {
					description: `Paper summary for ${params.paper_id}`,
					messages: [
						{
							role: 'user' as const,
							content: {
								type: 'text' as const,
								text: summaryText,
							},
						},
					],
				};
			}
		);

		server.prompt(
			MODEL_DETAIL_PROMPT_CONFIG.name,
			MODEL_DETAIL_PROMPT_CONFIG.description,
			MODEL_DETAIL_PROMPT_CONFIG.schema.shape,
			async (params: ModelDetailParams) => {
				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: MODEL_DETAIL_PROMPT_CONFIG.name,
						query: params.model_id,
						parameters: { model_id: params.model_id },
						baseOptions: getLoggingOptions(),
						successOptions: (details) => ({
							totalResults: details.totalResults,
							resultsShared: details.resultsShared,
							responseCharCount: details.formatted.length,
						}),
					},
					async () => {
						const modelDetail = new ModelDetailTool(hfToken, undefined);
						return modelDetail.getDetails(params.model_id, true);
					}
				);

				return {
					description: `Model details for ${params.model_id}`,
					messages: [
						{
							role: 'user' as const,
							content: {
								type: 'text' as const,
								text: result.formatted,
							},
						},
					],
				};
			}
		);

		server.prompt(
			DATASET_DETAIL_PROMPT_CONFIG.name,
			DATASET_DETAIL_PROMPT_CONFIG.description,
			DATASET_DETAIL_PROMPT_CONFIG.schema.shape,
			async (params: DatasetDetailParams) => {
				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: DATASET_DETAIL_PROMPT_CONFIG.name,
						query: params.dataset_id,
						parameters: { dataset_id: params.dataset_id },
						baseOptions: getLoggingOptions(),
						successOptions: (details) => ({
							totalResults: details.totalResults,
							resultsShared: details.resultsShared,
							responseCharCount: details.formatted.length,
						}),
					},
					async () => {
						const datasetDetail = new DatasetDetailTool(hfToken, undefined);
						return datasetDetail.getDetails(params.dataset_id, true);
					}
				);

				return {
					description: `Dataset details for ${params.dataset_id}`,
					messages: [
						{
							role: 'user' as const,
							content: {
								type: 'text' as const,
								text: result.formatted,
							},
						},
					],
				};
			}
		);

		toolInstances[SEMANTIC_SEARCH_TOOL_CONFIG.name] = server.tool(
			SEMANTIC_SEARCH_TOOL_CONFIG.name,
			SEMANTIC_SEARCH_TOOL_CONFIG.description,
			SEMANTIC_SEARCH_TOOL_CONFIG.schema.shape,
			SEMANTIC_SEARCH_TOOL_CONFIG.annotations,
			async (params: SearchParams) => {
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: SEMANTIC_SEARCH_TOOL_CONFIG.name,
						query: params.query,
						parameters: { limit: params.limit, mcp: params.mcp },
						baseOptions: getLoggingOptions(),
						successOptions: (formatted) => ({
							totalResults: formatted.totalResults,
							resultsShared: formatted.resultsShared,
							responseCharCount: formatted.formatted.length,
						}),
					},
					async () => {
						const semanticSearch = new SpaceSearchTool(hfToken);
						const searchResult = await semanticSearch.search(params.query, params.limit, params.mcp);
						return formatSearchResults(params.query, searchResult.results, searchResult.totalCount);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[MODEL_SEARCH_TOOL_CONFIG.name] = server.tool(
			MODEL_SEARCH_TOOL_CONFIG.name,
			MODEL_SEARCH_TOOL_CONFIG.description,
			MODEL_SEARCH_TOOL_CONFIG.schema.shape,
			MODEL_SEARCH_TOOL_CONFIG.annotations,
			async (params: ModelSearchParams) => {
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: MODEL_SEARCH_TOOL_CONFIG.name,
						query: params.query || `sort:${params.sort || 'trendingScore'}`,
						parameters: params,
						baseOptions: getLoggingOptions(),
						successOptions: (formatted) => ({
							totalResults: formatted.totalResults,
							resultsShared: formatted.resultsShared,
							responseCharCount: formatted.formatted.length,
						}),
					},
					async () => {
						const modelSearch = new ModelSearchTool(hfToken);
						return modelSearch.searchWithParams(params);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[MODEL_DETAIL_TOOL_CONFIG.name] = server.tool(
			MODEL_DETAIL_TOOL_CONFIG.name,
			MODEL_DETAIL_TOOL_CONFIG.description,
			MODEL_DETAIL_TOOL_CONFIG.schema.shape,
			MODEL_DETAIL_TOOL_CONFIG.annotations,
			async (params: ModelDetailParams) => {
				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: MODEL_DETAIL_TOOL_CONFIG.name,
						query: params.model_id,
						parameters: { model_id: params.model_id },
						baseOptions: getLoggingOptions(),
						successOptions: (details) => ({
							totalResults: details.totalResults,
							resultsShared: details.resultsShared,
							responseCharCount: details.formatted.length,
						}),
					},
					async () => {
						const modelDetail = new ModelDetailTool(hfToken, undefined);
						return modelDetail.getDetails(params.model_id, false);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[PAPER_SEARCH_TOOL_CONFIG.name] = server.tool(
			PAPER_SEARCH_TOOL_CONFIG.name,
			PAPER_SEARCH_TOOL_CONFIG.description,
			PAPER_SEARCH_TOOL_CONFIG.schema.shape,
			PAPER_SEARCH_TOOL_CONFIG.annotations,
			async (params: z.infer<typeof PAPER_SEARCH_TOOL_CONFIG.schema>) => {
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: PAPER_SEARCH_TOOL_CONFIG.name,
						query: params.query,
						parameters: { results_limit: params.results_limit, concise_only: params.concise_only },
						baseOptions: getLoggingOptions(),
						successOptions: (formatted) => ({
							totalResults: formatted.totalResults,
							resultsShared: formatted.resultsShared,
							responseCharCount: formatted.formatted.length,
						}),
					},
					async () => {
						const paperSearchTool = new PaperSearchTool(hfToken);
						return paperSearchTool.search(params.query, params.results_limit, params.concise_only);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[DATASET_SEARCH_TOOL_CONFIG.name] = server.tool(
			DATASET_SEARCH_TOOL_CONFIG.name,
			DATASET_SEARCH_TOOL_CONFIG.description,
			DATASET_SEARCH_TOOL_CONFIG.schema.shape,
			DATASET_SEARCH_TOOL_CONFIG.annotations,
			async (params: DatasetSearchParams) => {
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: DATASET_SEARCH_TOOL_CONFIG.name,
						query: params.query || `sort:${params.sort || 'trendingScore'}`,
						parameters: params,
						baseOptions: getLoggingOptions(),
						successOptions: (formatted) => ({
							totalResults: formatted.totalResults,
							resultsShared: formatted.resultsShared,
							responseCharCount: formatted.formatted.length,
						}),
					},
					async () => {
						const datasetSearch = new DatasetSearchTool(hfToken);
						return datasetSearch.searchWithParams(params);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[DATASET_DETAIL_TOOL_CONFIG.name] = server.tool(
			DATASET_DETAIL_TOOL_CONFIG.name,
			DATASET_DETAIL_TOOL_CONFIG.description,
			DATASET_DETAIL_TOOL_CONFIG.schema.shape,
			DATASET_DETAIL_TOOL_CONFIG.annotations,
			async (params: DatasetDetailParams) => {
				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: DATASET_DETAIL_TOOL_CONFIG.name,
						query: params.dataset_id,
						parameters: { dataset_id: params.dataset_id },
						baseOptions: getLoggingOptions(),
						successOptions: (details) => ({
							totalResults: details.totalResults,
							resultsShared: details.resultsShared,
							responseCharCount: details.formatted.length,
						}),
					},
					async () => {
						const datasetDetail = new DatasetDetailTool(hfToken, undefined);
						return datasetDetail.getDetails(params.dataset_id, false);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		// Compute README availability; adjust description and schema accordingly
		const hubInspectReadmeAllowed = hasReadmeFlag(toolSelection.enabledToolIds);
		const hubInspectDescription = hubInspectReadmeAllowed
			? `${HUB_INSPECT_TOOL_CONFIG.description} README file may be requested from the external repository.`
			: HUB_INSPECT_TOOL_CONFIG.description;
		const hubInspectBaseShape = HUB_INSPECT_TOOL_CONFIG.schema.shape as z.ZodRawShape;
		const hubInspectSchemaShape: z.ZodRawShape = hubInspectReadmeAllowed
			? hubInspectBaseShape
			: (() => {
					const { include_readme: _omit, ...rest } = hubInspectBaseShape as unknown as Record<string, unknown>;
					return rest as unknown as z.ZodRawShape;
				})();

		toolInstances[HUB_INSPECT_TOOL_CONFIG.name] = server.tool(
			HUB_INSPECT_TOOL_CONFIG.name,
			hubInspectDescription,
			hubInspectSchemaShape,
			HUB_INSPECT_TOOL_CONFIG.annotations,
			async (params: Record<string, unknown>) => {
				// Re-evaluate flag dynamically to reflect UI changes without restarting server
				const currentSelection = await toolSelectionStrategy.selectTools(toolSelectionContext);
				const allowReadme = hasReadmeFlag(currentSelection.enabledToolIds);
				const wantReadme = (params as { include_readme?: boolean }).include_readme === true; // explicit opt-in required
				const includeReadme = allowReadme && wantReadme;

				// Prepare safe logging parameters without relying on strong typing
				const repoIdsParam = (params as { repo_ids?: unknown }).repo_ids;
				const repoIds = Array.isArray(repoIdsParam) ? repoIdsParam : [];
				const firstRepoId = typeof repoIds[0] === 'string' ? (repoIds[0] as string) : '';
				const repoType = (params as { repo_type?: unknown }).repo_type as unknown;
				const repoTypeSafe =
					repoType === 'model' || repoType === 'dataset' || repoType === 'space' ? repoType : undefined;

				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: HUB_INSPECT_TOOL_CONFIG.name,
						query: firstRepoId,
						parameters: { count: repoIds.length, repo_type: repoTypeSafe, include_readme: includeReadme },
						baseOptions: getLoggingOptions(),
						successOptions: (details) => ({
							totalResults: details.totalResults,
							resultsShared: details.resultsShared,
							responseCharCount: details.formatted.length,
						}),
					},
					async () => {
						const tool = new HubInspectTool(hfToken, undefined);
						return tool.inspect(params as unknown as HubInspectParams, includeReadme);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[DOCS_SEMANTIC_SEARCH_CONFIG.name] = server.tool(
			DOCS_SEMANTIC_SEARCH_CONFIG.name,
			DOCS_SEMANTIC_SEARCH_CONFIG.description,
			DOCS_SEMANTIC_SEARCH_CONFIG.schema.shape,
			DOCS_SEMANTIC_SEARCH_CONFIG.annotations,
			async (params: DocSearchParams) => {
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: DOCS_SEMANTIC_SEARCH_CONFIG.name,
						query: params.query,
						parameters: { product: params.product },
						baseOptions: getLoggingOptions(),
						successOptions: (formatted) => ({
							totalResults: formatted.totalResults,
							resultsShared: formatted.resultsShared,
							responseCharCount: formatted.formatted.length,
						}),
					},
					async () => {
						const docSearch = new DocSearchTool(hfToken);
						return docSearch.search(params);
					}
				);
				return {
					content: [{ type: 'text', text: result.formatted }],
				};
			}
		);

		toolInstances[DOC_FETCH_CONFIG.name] = server.tool(
			DOC_FETCH_CONFIG.name,
			DOC_FETCH_CONFIG.description,
			DOC_FETCH_CONFIG.schema.shape,
			DOC_FETCH_CONFIG.annotations,
			async (params: DocFetchParams) => {
				const docFetch = new DocFetchTool();
				const results = await docFetch.fetch(params);
				return {
					content: [{ type: 'text', text: results }],
				};
			}
		);

		const duplicateToolConfig = DuplicateSpaceTool.createToolConfig(username);
		toolInstances[duplicateToolConfig.name] = server.tool(
			duplicateToolConfig.name,
			duplicateToolConfig.description,
			duplicateToolConfig.schema.shape,
			duplicateToolConfig.annotations,
			async (params: DuplicateSpaceParams) => {
				const duplicateSpace = new DuplicateSpaceTool(hfToken, username);
				const result = await duplicateSpace.duplicate(params);
				return {
					content: [{ type: 'text', text: formatDuplicateResult(result) }],
				};
			}
		);

		const spaceInfoToolConfig = SpaceInfoTool.createToolConfig(username);
		toolInstances[spaceInfoToolConfig.name] = server.tool(
			spaceInfoToolConfig.name,
			spaceInfoToolConfig.description,
			spaceInfoToolConfig.schema.shape,
			spaceInfoToolConfig.annotations,
			async (params: SpaceInfoParams) => {
				const spaceInfoTool = new SpaceInfoTool(hfToken, username);
				const result = await formatSpaceInfoResult(spaceInfoTool, params);
				return {
					content: [{ type: 'text', text: result }],
				};
			}
		);

		const spaceFilesToolConfig = SpaceFilesTool.createToolConfig(username);
		toolInstances[spaceFilesToolConfig.name] = server.tool(
			spaceFilesToolConfig.name,
			spaceFilesToolConfig.description,
			spaceFilesToolConfig.schema.shape,
			spaceFilesToolConfig.annotations,
			async (params: SpaceFilesParams) => {
				const spaceFilesTool = new SpaceFilesTool(hfToken, username);
				const result = await spaceFilesTool.listFiles(params);
				return {
					content: [{ type: 'text', text: result }],
				};
			}
		);

		toolInstances[USE_SPACE_TOOL_CONFIG.name] = server.tool(
			USE_SPACE_TOOL_CONFIG.name,
			USE_SPACE_TOOL_CONFIG.description,
			USE_SPACE_TOOL_CONFIG.schema.shape,
			USE_SPACE_TOOL_CONFIG.annotations,
			async (params: UseSpaceParams) => {
				const result = await runWithQueryLogging(
					logPromptQuery,
					{
						methodName: USE_SPACE_TOOL_CONFIG.name,
						query: params.space_id,
						parameters: { space_id: params.space_id },
						baseOptions: getLoggingOptions(),
						successOptions: (useSpaceResult) => ({
							totalResults: useSpaceResult.metadata.totalResults,
							resultsShared: useSpaceResult.metadata.resultsShared,
							responseCharCount: useSpaceResult.metadata.formatted.length,
						}),
					},
					async () => {
						const useSpaceTool = new UseSpaceTool(hfToken, undefined);
						return formatUseSpaceResult(useSpaceTool, params);
					}
				);
				return {
					content: result.content,
				};
			}
		);

		toolInstances[HF_JOBS_TOOL_CONFIG.name] = server.tool(
			HF_JOBS_TOOL_CONFIG.name,
			HF_JOBS_TOOL_CONFIG.description,
			HF_JOBS_TOOL_CONFIG.schema.shape,
			HF_JOBS_TOOL_CONFIG.annotations,
			async (params: z.infer<typeof HF_JOBS_TOOL_CONFIG.schema>) => {
				// Jobs require authentication - check if user has token
				const isAuthenticated = !!hfToken;
				const loggedOperation = params.operation ?? 'no-operation';
				const result = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: HF_JOBS_TOOL_CONFIG.name,
						query: loggedOperation,
						parameters: params.args || {},
						baseOptions: getLoggingOptions(),
						successOptions: (jobResult) => ({
							totalResults: jobResult.totalResults,
							resultsShared: jobResult.resultsShared,
							responseCharCount: jobResult.formatted.length,
						}),
					},
					async () => {
						const jobsTool = new HfJobsTool(hfToken, isAuthenticated, username);
						return jobsTool.execute(params);
					}
				);

				return {
					content: [{ type: 'text', text: result.formatted }],
					...(result.isError && { isError: true }),
				};
			}
		);

		// Get dynamic config based on environment (uses DYNAMIC_SPACE_DATA env var)
		const dynamicSpaceToolConfig = getDynamicSpaceToolConfig();
		toolInstances[dynamicSpaceToolConfig.name] = server.tool(
			dynamicSpaceToolConfig.name,
			dynamicSpaceToolConfig.description,
			dynamicSpaceToolConfig.schema.shape,
			dynamicSpaceToolConfig.annotations,
			async (params: SpaceArgs, extra) => {
				// Check if invoke operation is disabled by gradio=none
				const { gradio } = extractAuthBouquetAndMix(headers);
				if (params.operation === 'invoke' && gradio === 'none') {
					const errorMessage =
						'The invoke operation is disabled because gradio=none is set. ' +
						'To use invoke, remove gradio=none from your headers or set gradio to a space ID. ' +
						`You can still use operation=${VIEW_PARAMETERS} to inspect the tool schema.`;
					return {
						content: [{ type: 'text', text: errorMessage }],
						isError: true,
					};
				}

				const loggedOperation = params.operation ?? 'no-operation';

				if (params.operation === 'invoke') {
					const startTime = Date.now();
					let success = false;

					try {
						const spaceTool = new SpaceTool(hfToken);
						const result = await spaceTool.execute(params, extra);

						if ('result' in result && result.result) {
							const invokeResult = result as InvokeResult;
							success = !invokeResult.isError;

							const stripImageContent =
								noImageContentHeaderEnabled || toolSelection.enabledToolIds.includes('NO_GRADIO_IMAGE_CONTENT');
							const postProcessOptions: GradioToolCallOptions = {
								stripImageContent,
								toolName: dynamicSpaceToolConfig.name,
								outwardFacingName: dynamicSpaceToolConfig.name,
								sessionInfo,
								spaceName: params.space_name,
							};

								const processedResult = applyResultPostProcessing(invokeResult.result as CallToolResult, postProcessOptions);

							const warningsContent =
								invokeResult.warnings.length > 0
									? [
											{
												type: 'text' as const,
												text:
													(invokeResult.warnings.length === 1 ? 'Warning:\n' : 'Warnings:\n') +
													invokeResult.warnings.map((w) => `- ${w}`).join('\n') +
													'\n',
											},
										]
									: [];

							const durationMs = Date.now() - startTime;
							const responseContent = [...warningsContent, ...(processedResult.content as unknown[])];
							logGradioEvent(params.space_name || 'unknown-space', sessionInfo?.clientSessionId || 'unknown', {
								durationMs,
								isAuthenticated: !!hfToken,
								clientName: sessionInfo?.clientInfo?.name,
								clientVersion: sessionInfo?.clientInfo?.version,
								success,
								error: invokeResult.isError ? JSON.stringify(responseContent) : undefined,
								responseSizeBytes: JSON.stringify(responseContent).length,
								isDynamic: true,
							});

							return {
								content: responseContent,
								...(invokeResult.isError && { isError: true }),
							} as CallToolResult;
						}

						const toolResult = result as ToolResult;
						success = !toolResult.isError;

						const durationMs = Date.now() - startTime;
						logSearchQuery(dynamicSpaceToolConfig.name, loggedOperation, params, {
							...getLoggingOptions(),
							totalResults: toolResult.totalResults,
							resultsShared: toolResult.resultsShared,
							responseCharCount: toolResult.formatted.length,
							durationMs,
							success,
						});

						return {
							content: [{ type: 'text', text: toolResult.formatted }],
							...(toolResult.isError && { isError: true }),
						};
					} catch (err) {
						const durationMs = Date.now() - startTime;
						logGradioEvent(params.space_name || 'unknown-space', sessionInfo?.clientSessionId || 'unknown', {
							durationMs,
							isAuthenticated: !!hfToken,
							clientName: sessionInfo?.clientInfo?.name,
							clientVersion: sessionInfo?.clientInfo?.version,
							success: false,
							error: err,
							isDynamic: true,
						});
						throw err;
					}
				}

				const toolResult = await runWithQueryLogging(
					logSearchQuery,
					{
						methodName: dynamicSpaceToolConfig.name,
						query: loggedOperation,
						parameters: params,
						baseOptions: getLoggingOptions(),
						successOptions: (result) => ({
							totalResults: result.totalResults,
							resultsShared: result.resultsShared,
							responseCharCount: result.formatted.length,
						}),
					},
					async () => {
						const spaceTool = new SpaceTool(hfToken);
						const result = await spaceTool.execute(params, extra);
						return result as ToolResult;
					}
				);

				return {
					content: [{ type: 'text', text: toolResult.formatted }],
					...(toolResult.isError && { isError: true }),
				};
			}
		);

		// Register Gradio widget resource for OpenAI MCP client (skybridge)
		if (sessionInfo?.clientInfo?.name === 'openai-mcp') {
			logger.debug('Registering Gradio widget resource for skybridge client');
			const widgetConfig = createGradioWidgetResourceConfig(version);
			server.registerResource(widgetConfig.name, widgetConfig.uri, {}, async () => ({
				contents: [
					{
						uri: widgetConfig.uri,
						mimeType: widgetConfig.mimeType,
						text: widgetConfig.htmlContent,
						_meta: widgetConfig.metadata,
					},
				],
			}));
		}

		// Declare the function to apply tool states (we only need to call it if we are
		// applying the tool states either because we have a Gradio tool call (grNN_) or
		// we are responding to a ListToolsRequest). This also helps if there is a
		// mismatch between Client cache state and desired states for these specific tools.
		// NB: That may not always be the case, consider carefully whether you want a tool
		// included in the skipGradio check.
		const applyToolStates = async () => {
			logger.info(
				{
					mode: toolSelection.mode,
					reason: toolSelection.reason,
					enabledCount: toolSelection.enabledToolIds.length,
					totalTools: Object.keys(toolInstances).length,
					mixedBouquet: toolSelection.mixedBouquet?.join(','),
				},
				'Tool selection strategy applied'
			);

			// Apply the desired state to each tool (tools start enabled by default)
			for (const [toolName, toolInstance] of Object.entries(toolInstances)) {
				if (toolSelection.enabledToolIds.includes(toolName)) {
					toolInstance.enable();
				} else {
					toolInstance.disable();
				}
			}
		};

		// Always register capabilities consistently for stateless vs stateful modes
		const transportInfo = sharedApiClient.getTransportInfo();

		registerCapabilities(server, sharedApiClient, {
			hasResources: sessionInfo?.clientInfo?.name === 'openai-mcp',
		});

		if (!skipGradio) {
			void applyToolStates();

			if (!transportInfo?.jsonResponseEnabled && !transportInfo?.externalApiMode) {
				// Set up event listener for dynamic tool state changes
				const toolStateChangeHandler = (toolId: string, enabled: boolean) => {
					const toolInstance = toolInstances[toolId];
					if (toolInstance) {
						if (enabled) {
							toolInstance.enable();
						} else {
							toolInstance.disable();
						}
						logger.debug({ toolId, enabled }, 'Applied single tool state change');
					}
				};

				sharedApiClient.on('toolStateChange', toolStateChangeHandler);

				// Clean up event listener when server closes
				server.server.onclose = () => {
					sharedApiClient.removeListener('toolStateChange', toolStateChangeHandler);
					logger.debug('Removed toolStateChange listener for closed server');
				};
			}
		}
		return { server, userDetails, enabledToolIds: toolSelection.enabledToolIds };
	};
};
