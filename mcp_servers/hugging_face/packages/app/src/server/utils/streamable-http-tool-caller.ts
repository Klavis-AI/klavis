import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';
import { CallToolResultSchema } from '@modelcontextprotocol/sdk/types.js';
import type { ServerNotification, ServerRequest } from '@modelcontextprotocol/sdk/types.js';
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { logger } from './logger.js';

function buildAuthHeaders(hfToken?: string): Record<string, string> | undefined {
	if (!hfToken) {
		return undefined;
	}

	return {
		Authorization: `Bearer ${hfToken}`,
		'X-HF-Authorization': `Bearer ${hfToken}`,
	};
}

/**
 * Calls a remote Streamable HTTP MCP server tool and relays progress notifications
 * back to the calling client when available.
 */
export async function callStreamableHttpTool(
	serverUrl: string,
	toolName: string,
	parameters: Record<string, unknown>,
	hfToken: string | undefined,
	extra: RequestHandlerExtra<ServerRequest, ServerNotification> | undefined
): Promise<CallToolResult> {
	logger.trace(
		{
			serverUrl,
			toolName,
			hasToken: Boolean(hfToken),
			paramKeys: Object.keys(parameters ?? {}),
		},
		'Streamable proxy calling upstream tool'
	);
	logger.info({ serverUrl, toolName, params: parameters }, 'Calling Streamable HTTP tool');

	const client = new Client(
		{
			name: 'hf-mcp-streamable-client',
			version: '1.0.0',
		},
		{
			capabilities: {},
		}
	);

	const headers = buildAuthHeaders(hfToken);
	const transport = new StreamableHTTPClientTransport(new URL(serverUrl), {
		requestInit: headers ? { headers } : undefined,
	});

	await client.connect(transport);
	logger.trace({ serverUrl }, 'Streamable proxy connected upstream');

	try {
		const progressToken = extra?._meta?.progressToken;
		logger.trace({ progressToken: progressToken ?? null }, 'Streamable proxy progress token from client');
		let progressRelayDisabled = false;

		const sendProgressNotification = async (progress: {
			progress?: number;
			total?: number;
			message?: string;
		}) => {
			if (!extra || progressRelayDisabled) {
				return;
			}
			if (extra.signal?.aborted) {
				progressRelayDisabled = true;
				return;
			}
			if (progressToken === undefined) {
				return;
			}
			logger.trace(
				{
					progressToken,
					progress,
				},
				'Streamable proxy upstream progress event'
			);

			try {
				const params: {
					progressToken: number | string;
					progress: number;
					total?: number;
					message?: string;
				} = {
					progressToken,
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
			} catch (error) {
				progressRelayDisabled = true;
				logger.trace({ error }, 'Streamable proxy progress relay failed');
				logger.debug({ error }, 'Failed to relay Streamable HTTP progress notification');
			}
		};

		const requestOptions: {
			onprogress?: (progress: { progress?: number; total?: number; message?: string }) => void;
			resetTimeoutOnProgress?: boolean;
		} = {};

		if (progressToken !== undefined && extra) {
			requestOptions.onprogress = (progress) => {
				void sendProgressNotification(progress);
			};
			requestOptions.resetTimeoutOnProgress = true;
		} else {
			logger.trace(
				{
					hasExtra: Boolean(extra),
					progressToken: progressToken ?? null,
				},
				'Streamable proxy progress relay disabled'
			);
		}

		const result = await client.request(
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

		logger.trace(
			{
				serverUrl,
				toolName,
			},
			'Streamable proxy upstream tool result received'
		);

		return result;
	} finally {
		await client.close();
	}
}
