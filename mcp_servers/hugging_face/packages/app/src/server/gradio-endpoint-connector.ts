import type { Client } from '@modelcontextprotocol/sdk/client/index.js';
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { type ServerNotification, type ServerRequest, type Tool } from '@modelcontextprotocol/sdk/types.js';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js';
import { logger } from './utils/logger.js';
import { logGradioEvent } from './utils/query-logger.js';
import { z } from 'zod';
import type { GradioEndpoint } from './utils/mcp-api-client.js';
import { spaceInfo } from '@huggingface/hub';
import { gradioMetrics, getMetricsSafeName } from './utils/gradio-metrics.js';
import { createGradioToolName } from './utils/gradio-utils.js';
import { createAudioPlayerUIResource } from './utils/ui/audio-player.js';
import { spaceMetadataCache, CACHE_CONFIG } from './utils/gradio-cache.js';
import { callGradioTool, applyResultPostProcessing, type GradioToolCallOptions } from './utils/gradio-tool-caller.js';
import { parseGradioSchemaResponse } from '@llmindset/hf-mcp';

// Define types for JSON Schema
interface JsonSchemaProperty {
	type?: string;
	description?: string;
	default?: unknown;
	enum?: unknown[];
	[key: string]: unknown;
}

interface JsonSchema {
	type?: string;
	properties?: Record<string, JsonSchemaProperty>;
	required?: string[];
	[key: string]: unknown;
}

// Define type for array format schema
interface EndpointConnection {
	endpointId: string;
	originalIndex: number;
	client: Client | null; // Will be null when using schema-only approach
	tools: Tool[];
	name?: string;
	emoji?: string;
	mcpUrl?: string; // Store the MCP URL for lazy connection during tool calls
	isPrivate?: boolean;
}

interface RegisterRemoteToolsOptions {
	stripImageContent?: boolean;
	gradioWidgetUri?: string;
}

type EndpointConnectionResult =
	| {
			success: true;
			endpointId: string;
			connection: EndpointConnection;
	  }
	| {
			success: false;
			endpointId: string;
			error: Error;
	  };

const CONNECTION_TIMEOUT_MS = 12000;

/**
 * Creates a timeout promise that rejects after the specified milliseconds
 */
function createTimeout(ms: number): Promise<never> {
	return new Promise((_, reject) => {
		setTimeout(() => {
			reject(new Error(`Connection timeout after ${ms.toString()}ms`));
		}, ms);
	});
}

// Kept export for callers; now delegates to shared helper and tracks metrics.
export function parseSchemaResponse(
	schemaResponse: unknown,
	endpointId: string,
	subdomain: string
	): Array<{ name: string; description?: string; inputSchema: JsonSchema }> {
	try {
		const parsed = parseGradioSchemaResponse(schemaResponse);
		gradioMetrics.recordSchemaFormat(parsed.format);

		logger.debug(
			{
				endpointId,
				toolCount: parsed.tools.length,
				tools: parsed.tools.map((t) => t.name),
				format: parsed.format,
			},
			'Retrieved schema'
		);

		return parsed.tools as Array<{ name: string; description?: string; inputSchema: JsonSchema }>;
	} catch (error) {
		if (error instanceof Error && error.message.includes('no tools found')) {
			// Preserve legacy error wording expected by tests/callers
			throw new Error('No tools found in schema');
		}
		logger.error(
			{ endpointId, subdomain, schemaType: typeof schemaResponse, error: error instanceof Error ? error.message : String(error) },
			'Invalid schema format'
		);
		throw error;
	}
}

/**
 * Check if a space is private using cache first, then API if needed
 */
async function isSpacePrivate(spaceName: string, hfToken?: string): Promise<boolean> {
	try {
		if (!hfToken) return false; // anonymous requests don't have a token to forward

		// Check cache first
		const cached = spaceMetadataCache.get(spaceName);
		if (cached) {
			logger.trace({ spaceName, private: cached.private }, 'Using cached private status');
			return cached.private;
		}

		// Fall back to API call if not cached
		logger.debug({ spaceName }, 'Cache miss for private status, fetching from API');

		// Create abort controller for timeout
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), CACHE_CONFIG.SPACE_INFO_TIMEOUT);

		try {
			const info = await spaceInfo({
				name: spaceName,
				credentials: { accessToken: hfToken },
				// Note: We can't pass signal to spaceInfo, but this is a best-effort timeout
			});

			clearTimeout(timeoutId);

			// Only cache public spaces - private spaces should always be fetched fresh
			// This ensures auth-sensitive information is never stale
			if (!info.private) {
				const metadata = {
					_id: (info as { _id?: string })._id || `gradio_${spaceName.replace('/', '-')}`,
					name: spaceName,
					subdomain: (info as { subdomain?: string }).subdomain || '',
					emoji: '🔧',
					private: info.private,
					sdk: (info as { sdk?: string }).sdk || 'gradio',
					fetchedAt: Date.now(),
				};
				spaceMetadataCache.set(spaceName, metadata);
				logger.trace({ spaceName }, 'Public space metadata cached');
			} else {
				logger.trace({ spaceName }, 'Private space metadata not cached');
			}

			return info.private;
		} finally {
			clearTimeout(timeoutId);
		}
	} catch (error) {
		// If we can't fetch space info, assume it might be private to be safe
		logger.warn({ spaceName, error }, 'Failed to fetch space info, assuming private');
		return true;
	}
}

/**
 * Fetches schema from a single Gradio endpoint without establishing a Streamable HTTP connection
 */
async function fetchEndpointSchema(
	endpoint: GradioEndpoint,
	originalIndex: number,
	hfToken: string | undefined
): Promise<EndpointConnection> {
	const endpointId = `endpoint${(originalIndex + 1).toString()}`;
	const schemaUrl = `https://${endpoint.subdomain}.hf.space/gradio_api/mcp/schema`;

	// TODO -- leaving this commented out for now -- i may want this again very shortly
	const isPrivateSpace = await isSpacePrivate(endpoint.name, hfToken);
	logger.debug({ url: schemaUrl, endpointId }, 'Fetching schema from endpoint');

	// Prepare headers
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
	};

	if (isPrivateSpace && hfToken) {
		headers['X-HF-Authorization'] = `Bearer ${hfToken}`;
	}

	// Add timeout using AbortController (same pattern as HfApiCall)
	const apiTimeout = process.env.HF_API_TIMEOUT ? parseInt(process.env.HF_API_TIMEOUT, 10) : 12500;
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), apiTimeout);

	// Fetch schema directly
	const response = await fetch(schemaUrl, {
		method: 'GET',
		headers,
		signal: controller.signal,
	});

	clearTimeout(timeoutId);

	if (!response.ok) {
		throw new Error(`Failed to fetch schema: ${response.status} ${response.statusText}`);
	}

	const schemaResponse = (await response.json()) as unknown;

	// Parse the schema response
	const parsed = parseSchemaResponse(schemaResponse, endpointId, endpoint.subdomain);
	const tools: Tool[] = parsed
		.filter((parsedTool) => !parsedTool.name.toLowerCase().includes('<lambda'))
		.map((parsedTool) => ({
			name: parsedTool.name,
			description: parsedTool.description || `${parsedTool.name} tool`,
			inputSchema: {
				type: 'object',
				properties: parsedTool.inputSchema.properties || {},
				required: parsedTool.inputSchema.required || [],
				description: parsedTool.inputSchema.description,
			},
		}));

	return {
		endpointId,
		originalIndex,
		client: null, // No client connection yet
		tools: tools,
		name: endpoint.name,
		emoji: endpoint.emoji,
		mcpUrl: `https://${endpoint.subdomain}.hf.space/gradio_api/mcp/`, // Store MCP URL for later
		isPrivate: isPrivateSpace,
	};
}

/**
 * Fetches schemas from multiple Gradio endpoints in parallel with timeout
 * Uses efficient /mcp/schema endpoint instead of opening streaming connections
 */
export async function connectToGradioEndpoints(
	gradioEndpoints: GradioEndpoint[],
	hfToken: string | undefined
): Promise<EndpointConnectionResult[]> {
	// Filter and map valid endpoints with their indices
	const validWithIndex = gradioEndpoints
		.map((ep, index) => ({ endpoint: ep, originalIndex: index }))
		.filter((item) => item.endpoint.subdomain && item.endpoint.subdomain.trim() !== '');

	if (validWithIndex.length === 0) {
		logger.debug('No valid Gradio endpoints to fetch schemas from');
		return [];
	}

	// Create schema fetch tasks with timeout
	const schemaFetchTasks = validWithIndex.map(({ endpoint, originalIndex }) => {
		const endpointId = `endpoint${(originalIndex + 1).toString()}`;

		return Promise.race([fetchEndpointSchema(endpoint, originalIndex, hfToken), createTimeout(CONNECTION_TIMEOUT_MS)])
			.then(
				(connection): EndpointConnectionResult => ({
					success: true,
					endpointId,
					connection,
				})
			)
			.catch((error: unknown): EndpointConnectionResult => {
				const isFirstError = gradioMetrics.schemaFetchError(endpoint.name);
				const logLevel = isFirstError ? 'warn' : 'trace';

				logger[logLevel](
					{
						endpointId,
						subdomain: endpoint.subdomain,
						error: error instanceof Error ? error.message : String(error),
					},
					'Failed to fetch schema from endpoint'
				);

				return {
					success: false,
					endpointId,
					error: error instanceof Error ? error : new Error(String(error)),
				};
			});
	});

	// Execute all schema fetches in parallel
	const results = await Promise.all(schemaFetchTasks);

	// Log results
	const successful = results.filter((r) => r.success);
	const failed = results.filter((r) => !r.success);

	logger.debug(
		{
			total: results.length,
			successful: successful.length,
			failed: failed.length,
		},
		'Gradio endpoint schema fetch results'
	);

	return results;
}

/**
 * Creates the display information for a tool
 */
function createToolDisplayInfo(connection: EndpointConnection, tool: Tool): { title: string; description: string } {
	const displayName = connection.name || 'Unknown Space';
	const title = `${displayName} - ${tool.name}${connection.emoji ? ` ${connection.emoji}` : ''}`;
	const description = tool.description
		? `${tool.description} (from ${displayName})`
		: `${tool.name} tool from ${displayName}`;
	return { title, description };
}

/**
 * Creates the tool handler function
 */
function createToolHandler(
	connection: EndpointConnection,
	tool: Tool,
	outwardFacingName: string,
	hfToken?: string,
	sessionInfo?: {
		clientSessionId?: string;
		isAuthenticated?: boolean;
		clientInfo?: { name: string; version: string };
	},
	options: RegisterRemoteToolsOptions = {}
): (
	params: Record<string, unknown>,
	extra: RequestHandlerExtra<ServerRequest, ServerNotification>
) => Promise<CallToolResult> {
	return async (params: Record<string, unknown>, extra) => {
		logger.info({ tool: tool.name, params }, 'Calling remote tool');

		// Track metrics for logging
		const startTime = Date.now();
		let success = false;
		let error: string | undefined;
		let responseSizeBytes: number | undefined;
		const notificationCount = 0;

		try {
			// Validate MCP URL
			if (!connection.mcpUrl) {
				throw new Error('No MCP URL available for tool execution');
			}

			// Use unified Gradio tool caller for Streamable HTTP connection, MCP call, and progress relay
			const result = await callGradioTool(connection.mcpUrl, tool.name, params, hfToken, extra);

			// Calculate response size (rough estimate based on JSON serialization)
			try {
				responseSizeBytes = JSON.stringify(result).length;
			} catch {
				// If serialization fails, don't worry about size
			}

			success = !result.isError;
			if (result.isError) {
				// Extract a meaningful error message from MCP content items
				const first =
					Array.isArray(result.content) && result.content.length > 0 ? (result.content[0] as unknown) : undefined;
				let message: string | undefined;
				if (typeof first === 'string') {
					message = first;
				} else if (first && typeof first === 'object') {
					const obj = first as Record<string, unknown>;
					if (typeof obj.text === 'string') {
						message = obj.text;
					} else if (typeof obj.message === 'string') {
						message = obj.message;
					} else if (typeof obj.error === 'string') {
						message = obj.error;
					} else {
						try {
							message = JSON.stringify(obj);
						} catch {
							message = String(obj);
						}
					}
				} else if (first !== undefined) {
					// Fallback for other primitive types
					message = String(first);
				}

				error = message || 'Unknown error';

				// Bubble up the error so upstream callers and metrics can track failures
				throw new Error(error);
			}

			// Record success in gradio metrics when no error and no exception thrown
			if (success) {
				const metricsName = getMetricsSafeName(outwardFacingName);
				gradioMetrics.recordSuccess(metricsName);
			}

			// Prepare post-processing options
			const postProcessOptions: GradioToolCallOptions = {
				stripImageContent: options.stripImageContent,
				toolName: tool.name,
				outwardFacingName,
				sessionInfo,
				gradioWidgetUri: options.gradioWidgetUri,
				spaceName: connection.name,
			};

			// Special handling: if the tool name contains "_mcpui" and it returns a single text URL,
			// wrap it as an embedded audio player UI resource.
			try {
				const hasUiSuffix = tool.name.includes('_mcpui');
				if (!result.isError && hasUiSuffix && Array.isArray(result.content) && result.content.length === 1) {
					const item = result.content[0] as unknown as { type?: string; text?: string };
					const text = typeof item?.text === 'string' ? item.text.trim() : '';
					const looksLikeUrl = /^https?:\/\//i.test(text);

					if ((item.type === 'text' || !item.type) && looksLikeUrl) {
						let base64Audio: string | undefined;
						const url = text;

						try {
							const resp = await fetch(url);
							if (resp.ok) {
								const buf = Buffer.from(await resp.arrayBuffer());
								base64Audio = buf.toString('base64');
							}
						} catch (e) {
							logger.debug(
								{ tool: tool.name, url, error: e instanceof Error ? e.message : String(e) },
								'Failed to inline audio; falling back to URL source'
							);
						}

						const title = `${connection.name || 'MCP UI tool'}`;
						const uriSafeName = (connection.name || 'audio').replace(/[^a-z0-9-_]+/gi, '-');
						const uiUri: `ui://${string}` = `ui://huggingface-mcp/${uriSafeName}/${Date.now().toString()}`;

						const uiResource = createAudioPlayerUIResource(uiUri, {
							title,
							base64Audio,
							srcUrl: base64Audio ? undefined : url,
							mimeType: `audio/wav`,
						});

						const decoratedResult = {
							isError: false,
							content: [result.content[0], uiResource],
						} as CallToolResult;

						// Apply post-processing to the decorated result
						return applyResultPostProcessing(decoratedResult, postProcessOptions);
					}
				}
			} catch (e) {
				logger.debug(
					{ tool: tool.name, error: e instanceof Error ? e.message : String(e) },
					'MCP UI transform skipped'
				);
			}

			// Apply standard post-processing (image stripping + OpenAI structured content)
			return applyResultPostProcessing(result, postProcessOptions);
		} catch (err) {
			// Ensure meaningful error output instead of [object Object]
			const errObj =
				err instanceof Error
					? err
					: new Error(
							typeof err === 'string'
								? err
								: (() => {
										try {
											return JSON.stringify(err);
										} catch {
											return String(err);
										}
									})()
						);
			logger.error({ tool: tool.name, err: errObj, errMessage: errObj.message }, 'Remote tool call failed');
			const metricsName = getMetricsSafeName(outwardFacingName);
			gradioMetrics.recordFailure(metricsName);
			// Set error if not already set
			if (!error) {
				error = errObj.message;
			}
			throw errObj;
		} finally {
			// Always log the Gradio event, even if there was a crash
			const endTime = Date.now();
			logGradioEvent(connection.name || connection.endpointId, sessionInfo?.clientSessionId || 'unknown', {
				durationMs: endTime - startTime,
				isAuthenticated: !!hfToken,
				clientName: sessionInfo?.clientInfo?.name,
				clientVersion: sessionInfo?.clientInfo?.version,
				success,
				error,
				responseSizeBytes,
				notificationCount,
			});
		}
	};
}

/**
 * Registers multiple remote tools from a Gradio endpoint
 */
export function registerRemoteTools(
	server: McpServer,
	connection: EndpointConnection,
	hfToken?: string,
	sessionInfo?: {
		clientSessionId?: string;
		isAuthenticated?: boolean;
		clientInfo?: { name: string; version: string };
	},
	options: RegisterRemoteToolsOptions = {}
): void {
	connection.tools.forEach((tool, toolIndex) => {
		// Generate tool name
		const outwardFacingName = createGradioToolName(
			tool.name,
			connection.originalIndex,
			connection.isPrivate,
			toolIndex
		);

		// Create display info
		const { title, description } = createToolDisplayInfo(connection, tool);

		// Convert schema
		const schemaShape = convertToolSchemaToZod(tool);

		// Create handler
		const handler = createToolHandler(connection, tool, outwardFacingName, hfToken, sessionInfo, options);

		// Log registration
		logger.trace(
			{
				endpointId: connection.endpointId,
				originalName: tool.name,
				outwardFacingName: outwardFacingName,
				description: tool.description,
			},
			'Registering remote tool'
		);

		// Log the exact structure we're getting
		logger.trace(
			{
				toolName: tool.name,
				inputSchema: tool.inputSchema,
			},
			'Remote tool inputSchema structure'
		);

		// Register the tool
		const theTool = server.tool(
			outwardFacingName,
			description,
			schemaShape,
			{
				openWorldHint: true,
				title: title,
			},
			handler
		);

		if (sessionInfo?.clientInfo?.name == 'openai-mcp') {
			theTool._meta = {
				'openai/outputTemplate': options.gradioWidgetUri || '',
				'openai/toolInvocation/invoking': `Calling the Hugging Face Space ${connection.name || connection.endpointId}`,
				'openai/toolInvocation/invoked': `Your content is being generated`,
			};
		}
	});
}

function convertToolSchemaToZod(tool: Tool): Record<string, z.ZodTypeAny> {
	const schemaShape: Record<string, z.ZodTypeAny> = {};

	if (typeof tool.inputSchema === 'object' && 'properties' in tool.inputSchema) {
		const jsonSchema = tool.inputSchema as JsonSchema;
		const props = jsonSchema.properties || {};
		const required = jsonSchema.required || [];

		for (const [key, jsonSchemaProperty] of Object.entries(props)) {
			const isRequired = required.includes(key);

			// Convert to Zod schema, skipping defaults for required fields
			let zodSchema = convertJsonSchemaToZod(jsonSchemaProperty, isRequired);

			// Make optional if not in required array
			if (!isRequired) {
				zodSchema = zodSchema.optional();
			}

			schemaShape[key] = zodSchema;
		}
	}

	return schemaShape;
}

/**
 * Converts a JSON Schema property to a Zod schema
 * @param jsonSchemaProperty - The JSON schema property to convert
 * @param skipDefault - If true, won't apply default values (useful for required fields)
 */
export function convertJsonSchemaToZod(jsonSchemaProperty: JsonSchemaProperty, skipDefault = false): z.ZodTypeAny {
	let zodSchema: z.ZodTypeAny;

	// Special handling for FileData types
	if (
		jsonSchemaProperty.title === 'FileData' ||
		(jsonSchemaProperty.format === 'a http or https url to a file' &&
			typeof jsonSchemaProperty.default === 'object' &&
			jsonSchemaProperty.default !== null)
	) {
		// Create FileData object schema
		zodSchema = z.object({
			path: z.string(),
			url: z.string().optional(),
			size: z.number().nullable().optional(),
			orig_name: z.string().optional(),
			mime_type: z.string().nullable().optional(),
			is_stream: z.boolean().optional(),
			meta: z
				.object({
					_type: z.string().optional(),
				})
				.optional(),
		});
	} else if (jsonSchemaProperty.enum && Array.isArray(jsonSchemaProperty.enum) && jsonSchemaProperty.enum.length > 0) {
		// Handle enum types
		if (jsonSchemaProperty.enum.every((v): v is string => typeof v === 'string')) {
			const enumValues = jsonSchemaProperty.enum as [string, ...string[]];
			zodSchema = z.enum(enumValues);
		} else {
			// Fallback for non-string enums - create a union of literals
			const literals: z.ZodTypeAny[] = jsonSchemaProperty.enum.map((v) => {
				if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean' || v === null) {
					return z.literal(v);
				}
				// For other types, convert to string
				return z.literal(String(v));
			});

			if (literals.length === 1) {
				// We know literals[0] exists because we checked length === 1
				zodSchema = literals[0] ?? z.any();
			} else if (literals.length >= 2) {
				// Ensure we have at least 2 elements for union
				zodSchema = z.union(literals as [z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]);
			} else {
				// This shouldn't happen due to our length check, but handle it anyway
				zodSchema = z.any();
			}
		}
	} else {
		// Convert based on type
		switch (jsonSchemaProperty.type) {
			case 'string':
				zodSchema = z.string();
				break;
			case 'number':
				zodSchema = z.number();
				break;
			case 'boolean':
				zodSchema = z.boolean();
				break;
			case 'array':
				zodSchema = z.array(z.any()); // Simplified for now
				break;
			case 'object':
				zodSchema = z.object({}); // Simplified for now
				break;
			default:
				zodSchema = z.any();
		}
	}

	// Enhance description for file inputs
	let description = jsonSchemaProperty.description || '';
	if (jsonSchemaProperty.format === 'a http or https url to a file' || jsonSchemaProperty.title === 'FileData') {
		description = description
			? `${description} (File input: provide URL or file path)`
			: 'a http or https url to a file';
	}

	if (description) {
		zodSchema = zodSchema.describe(description);
	}

	// Apply default value from the Schema
	if (!skipDefault && 'default' in jsonSchemaProperty && jsonSchemaProperty.default !== undefined) {
		let defaultValue = jsonSchemaProperty.default;

		// For FileData types, keep the full object as default
		// For other string types with object defaults, extract URL
		if (
			jsonSchemaProperty.type === 'string' &&
			typeof defaultValue === 'object' &&
			defaultValue !== null &&
			'url' in defaultValue &&
			jsonSchemaProperty.title !== 'FileData'
		) {
			const urlValue = (defaultValue as Record<string, unknown>).url;
			if (typeof urlValue === 'string') {
				defaultValue = urlValue;
			}
		}

		zodSchema = zodSchema.default(defaultValue);
	}

	return zodSchema;
}
