import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import {
	StreamableHTTPClientTransport,
	type StreamableHTTPClientTransportOptions,
} from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { CallToolResultSchema, type CallToolResult, type ServerNotification, type ServerRequest } from '@modelcontextprotocol/sdk/types.js';
import { Protocol, type RequestHandlerExtra, type RequestOptions } from '@modelcontextprotocol/sdk/shared/protocol.js';
import type { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';
import { logger } from '../../logger.js';

class GradioClient extends Client {
	override async connect(transport: Transport, _options?: RequestOptions): Promise<void> {
		await Protocol.prototype.connect.call(this, transport);
	}
}

export interface GradioCallResult {
	result: CallToolResult;
	capturedHeaders: Record<string, string>;
}

export interface GradioCallOptions {
	/** Called for every response to capture custom headers */
	onHeaders?: (headers: Headers) => void;
	/** Log the X-Proxied-Replica header to stderr once */
	logProxiedReplica?: boolean;
	/** Optional hook for when progress relay fails (e.g., client disconnected) */
	onProgressRelayFailure?: () => void;
}

/**
 * Extract the replica ID from the X-Proxied-Replica header.
 * Example: "oyerizs4-dspr4" => "dspr4"
 */
export function extractReplicaId(headerValue: string | undefined): string | null {
	if (!headerValue) return null;
	const parts = headerValue.split('-');
	if (parts.length < 2) return null;
	const replicaId = parts[parts.length - 1];
	if (!replicaId || replicaId.trim() === '') return null;
	return replicaId;
}

/**
 * Rewrites any Gradio API URLs in text content to include the replica path segment.
 * Example: https://mcp-tools-qwen-image-fast.hf.space/gradio_api =>
 *          https://mcp-tools-qwen-image-fast.hf.space/--replicas/<replica_id>/gradio_api
 */
export function rewriteReplicaUrlsInResult(
	result: CallToolResult,
	proxiedReplicaHeader: string | undefined
): CallToolResult {
	if (process.env.NO_REPLICA_REWRITE) return result;
	const replicaId = extractReplicaId(proxiedReplicaHeader);
	if (!replicaId) return result;

	const urlPattern = /https:\/\/([^\s"']+)\/gradio_api(\S*)?/g;

	const rewriteText = (text: string): string =>
		text.replace(urlPattern, (_match, host, rest = '') => {
			return `https://${host}/--replicas/${replicaId}/gradio_api${rest}`;
		});

	let changed = false;
	const newContent = result.content.map((item) => {
		if (typeof item === 'string') {
			const rewritten = rewriteText(item);
			if (rewritten !== item) {
				changed = true;
				return { type: 'text', text: rewritten } as (typeof result.content)[number];
			}
			return { type: 'text', text: item } as (typeof result.content)[number];
		}

		if (item && typeof item === 'object' && 'text' in item && typeof item.text === 'string') {
			const rewritten = rewriteText(item.text);
			if (rewritten !== item.text) {
				changed = true;
				return { ...item, text: rewritten };
			}
		}

		return item;
	});

	if (!changed) return result;
	return {
		...result,
		content: newContent,
	};
}

/**
 * Shared helper to call a Gradio MCP tool over Streamable HTTP, capturing response headers (including X-Proxied-Replica).
 * This handles Streamable HTTP setup, optional progress relay, and cleans up the client connection.
 */
export async function callGradioToolWithHeaders(
	mcpUrl: string,
	toolName: string,
	parameters: Record<string, unknown>,
	hfToken: string | undefined,
	extra: RequestHandlerExtra<ServerRequest, ServerNotification> | undefined,
	options: GradioCallOptions = {}
): Promise<GradioCallResult> {
	const capturedHeaders: Record<string, string> = {};
	let loggedHeader = false;

	const handleHeaders = (headers: Headers): void => {
		const proxiedReplica = headers.get('x-proxied-replica') ?? '';
		if (proxiedReplica) {
			capturedHeaders['x-proxied-replica'] = proxiedReplica;
		}
		if (options.logProxiedReplica && !loggedHeader) {
			loggedHeader = true;
		}
		options.onHeaders?.(headers);
	};

	const captureHeadersFetch: StreamableHTTPClientTransportOptions['fetch'] = async (url, init) => {
		const method = init?.method ?? 'GET';
		let requestSummary: {
			method?: unknown;
			id?: unknown;
			progressToken?: unknown;
			isBatch?: boolean;
		} | null = null;
		if (typeof init?.body === 'string') {
			try {
				const parsed = JSON.parse(init.body) as
					| { method?: unknown; id?: unknown; params?: { _meta?: { progressToken?: unknown } } }
					| Array<{ method?: unknown; id?: unknown; params?: { _meta?: { progressToken?: unknown } } }>;
				if (Array.isArray(parsed)) {
					requestSummary = {
						isBatch: true,
						method: parsed[0]?.method,
						id: parsed[0]?.id,
						progressToken: parsed[0]?.params?._meta?.progressToken,
					};
				} else if (parsed && typeof parsed === 'object') {
					requestSummary = {
						isBatch: false,
						method: parsed.method,
						id: parsed.id,
						progressToken: parsed.params?._meta?.progressToken,
					};
				}
			} catch {
				requestSummary = null;
			}
		}
		logger.trace('[gradio] upstream fetch', {
			method,
			url: url.toString(),
			hasBody: Boolean(init?.body),
			requestSummary,
		});
		const response = await fetch(url, init);
		logger.trace('[gradio] upstream response', {
			method,
			url: url.toString(),
			status: response.status,
			contentType: response.headers.get('content-type') ?? null,
			mcpSessionId: response.headers.get('mcp-session-id') ?? null,
		});
		handleHeaders(response.headers);
		return response;
	};

	const skipInitialize = process.env.GRADIO_SKIP_INITIALIZE === 'true';

	// Create MCP client
	const clientInfo = {
		name: 'hf-mcp-gradio-client',
		version: '1.0.0',
	};
	const clientOptions = {
		capabilities: {},
	};
	const remoteClient = skipInitialize
		? new GradioClient(clientInfo, clientOptions)
		: new Client(clientInfo, clientOptions);

	// Create Streamable HTTP transport with HF token if available
	const transportOptions: StreamableHTTPClientTransportOptions = {
		fetch: captureHeadersFetch,
	};
	if (hfToken) {
		const customHeaders = {
			'X-HF-Authorization': `Bearer ${hfToken}`,
		};

		// Headers for Streamable HTTP requests
		transportOptions.requestInit = {
			headers: customHeaders,
		};
	}

	logger.trace('[gradio] connecting streamable client', {
		mcpUrl,
		hasToken: Boolean(hfToken),
		skipInitialize,
	});
	const transport = new StreamableHTTPClientTransport(new URL(mcpUrl), transportOptions);
	let isClosing = false;
	transport.onmessage = (message) => {
		const messageInfo =
			message && typeof message === 'object'
				? {
					hasId: 'id' in message,
					id: (message as { id?: unknown }).id ?? null,
					method: 'method' in message ? (message as { method?: unknown }).method : null,
					isResult: 'result' in message,
					isError: 'error' in message,
				}
				: { messageType: typeof message };
		logger.trace('[gradio] transport message', messageInfo);
	};
	transport.onerror = (error) => {
		if (isClosing && error instanceof Error && error.message.includes('AbortError')) {
			logger.trace('[gradio] transport aborted after close', { message: error.message });
			return;
		}
		logger.trace('[gradio] transport error', { error });
	};
	transport.onclose = () => {
		logger.trace('[gradio] transport closed');
	};
	let connectCompleted = false;
	const connectWatchdog = setTimeout(() => {
		if (!connectCompleted) {
			logger.trace('[gradio] connect still pending', { mcpUrl });
		}
	}, 15000);
	await remoteClient.connect(transport);
	connectCompleted = true;
	clearTimeout(connectWatchdog);
	logger.trace('[gradio] connected streamable client', { mcpUrl });

	try {
		// Check if the client is requesting progress notifications
		const progressToken = extra?._meta?.progressToken;
		logger.trace('[gradio] progress setup', {
			hasExtra: Boolean(extra),
			progressToken: progressToken ?? null,
			hasSignal: Boolean(extra?.signal),
		});

		// Track whether we've seen a transport closure to avoid noisy retries
		let progressRelayDisabled = false;

		const sendProgressNotification = async (progress: { progress?: number; total?: number; message?: string }) => {
			if (!extra || progressRelayDisabled) return;
			if (extra.signal?.aborted) {
				progressRelayDisabled = true;
				logger.trace('[gradio] progress relay aborted', {
					progressToken: progressToken ?? null,
				});
				return;
			}
			try {
				logger.trace('[gradio] relaying progress', {
					progressToken: progressToken ?? null,
					progress,
				});
				const params: {
					progressToken: number;
					progress: number;
					total?: number;
					message?: string;
				} = {
					progressToken: progressToken as number,
					progress: progress.progress ?? 0,
				};
				if (progress.total !== undefined) {
					params.total = progress.total;
				}
				if (progress.message !== undefined) {
					params.message = progress.message;
				}
				await extra.sendNotification({
					method: 'notifications/progress',
					params,
				});
			} catch {
				// The underlying transport has likely closed (e.g., client disconnected); disable further relays.
				progressRelayDisabled = true;
				logger.trace('[gradio] progress relay failed', {
					progressToken: progressToken ?? null,
				});
				options.onProgressRelayFailure?.();
			}
		};

		const requestOptions: RequestOptions = {};

		if (progressToken !== undefined && extra) {
			// Fire-and-forget; best-effort relay
			requestOptions.onprogress = (progress) => {
				logger.trace('[gradio] upstream progress event', {
					progressToken: progressToken ?? null,
					progress,
				});
				void sendProgressNotification(progress);
			};
			requestOptions.resetTimeoutOnProgress = true;
		} else {
			logger.trace('[gradio] progress relay disabled', {
				progressToken: progressToken ?? null,
				hasExtra: Boolean(extra),
			});
		}

		logger.trace('[gradio] sending tool request', { toolName, hasProgressToken: progressToken !== undefined });
		const result = await remoteClient.request(
			{
				method: 'tools/call',
				params: {
					name: toolName,
					arguments: parameters,
					_meta: progressToken !== undefined ? { progressToken } : undefined,
				},
			},
			CallToolResultSchema,
			requestOptions
		);
		logger.trace('[gradio] tool request completed', { toolName, isError: result.isError });

		const proxiedReplica = capturedHeaders['x-proxied-replica'];
		const rewritten = rewriteReplicaUrlsInResult(result, proxiedReplica);

		return { result: rewritten, capturedHeaders };
	} finally {
		isClosing = true;
		await remoteClient.close();
	}
}
