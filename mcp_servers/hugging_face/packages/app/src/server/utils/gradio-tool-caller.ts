import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { type ServerNotification, type ServerRequest } from '@modelcontextprotocol/sdk/types.js';
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js';
import { callGradioToolWithHeaders } from '@llmindset/hf-mcp';
import { logger } from './logger.js';
import { stripImageContentFromResult, extractUrlFromContent } from './gradio-result-processor.js';
import { gradioMetrics, getMetricsSafeName } from './gradio-metrics.js';

/**
 * Options for calling a Gradio tool
 */
export interface GradioToolCallOptions {
	/** Whether to strip image content from the result */
	stripImageContent?: boolean;
	/** Original tool name (for logging) */
	toolName: string;
	/** Outward-facing tool name (for logging) */
	outwardFacingName: string;
	/** Session information for client-specific handling */
	sessionInfo?: {
		clientSessionId?: string;
		isAuthenticated?: boolean;
		clientInfo?: { name: string; version: string };
	};
	/** Gradio widget URI for OpenAI client */
	gradioWidgetUri?: string;
	/** Space name for structured content */
	spaceName?: string;
}

/**
 * Unified Gradio tool caller that handles:
 * - Streamable HTTP connection management
 * - MCP tool invocation
 * - Progress notification relay
 *
 * Returns the raw MCP result without post-processing. Callers should apply
 * image filtering and OpenAI-specific transforms as needed using applyResultPostProcessing.
 *
 * This ensures both proxied gr_* tools and the space tool's invoke operation
 * behave identically.
 */
export async function callGradioTool(
	mcpUrl: string,
	toolName: string,
	parameters: Record<string, unknown>,
	hfToken: string | undefined,
	extra: RequestHandlerExtra<ServerRequest, ServerNotification> | undefined
): Promise<CallToolResult> {
	logger.info({ tool: toolName, params: parameters }, 'Calling Gradio tool via unified caller');

	const metricsToolName = getMetricsSafeName(toolName);

	// Call the remote tool via shared helper (handles Streamable HTTP, progress relay, header capture)
	const { result, capturedHeaders } = await callGradioToolWithHeaders(
		mcpUrl,
		toolName,
		parameters,
		hfToken,
		extra,
		{
			logProxiedReplica: true,
			onProgressRelayFailure: () => gradioMetrics.recordProgressRelayFailure(metricsToolName),
		}
	);

	// Attach captured headers (e.g., X-Proxied-Replica) to the result meta so callers can inspect them
	const proxiedReplica = capturedHeaders['x-proxied-replica'];
	if (proxiedReplica) {
		logger.debug({ tool: toolName, proxiedReplica }, 'Captured Gradio response header');
		return {
			...result,
			_meta: {
				...(result as { _meta?: Record<string, unknown> })._meta,
				responseHeaders: {
					...(result as { _meta?: { responseHeaders?: Record<string, unknown> } })._meta?.responseHeaders,
					'x-proxied-replica': proxiedReplica,
				},
			},
		} as CallToolResult;
	}

	return result;
}

/**
 * Applies post-processing to a Gradio tool result:
 * - Image content filtering (conditionally)
 * - OpenAI-specific structured content
 *
 * This should be called after any custom transformations (like _mcpui handling)
 * to ensure consistent behavior across all Gradio tools.
 */
export function applyResultPostProcessing(
	result: CallToolResult,
	options: GradioToolCallOptions
): CallToolResult {
	// Strip image content if requested
	const filteredResult = stripImageContentFromResult(result, {
		enabled: !!options.stripImageContent,
		toolName: options.toolName,
		outwardFacingName: options.outwardFacingName,
	});

	// For OpenAI MCP client, check if result contains a URL and set structuredContent
	if (options.sessionInfo?.clientInfo?.name === 'openai-mcp') {
		const extractedUrl = extractUrlFromContent(filteredResult.content);
		if (extractedUrl) {
			logger.debug({ tool: options.toolName, url: extractedUrl }, 'Setting structuredContent with extracted URL');
			(filteredResult as CallToolResult & {
				structuredContent?: { url: string; spaceName?: string };
			}).structuredContent = {
				url: extractedUrl,
				spaceName: options.spaceName,
			};
		}
	}

	return filteredResult;
}
