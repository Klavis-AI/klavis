import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ServerCapabilities } from '@modelcontextprotocol/sdk/types.js';
import type { McpApiClient } from './mcp-api-client.js';
import { logger } from './logger.js';

export interface RegisterCapabilitiesOptions {
	/**
	 * Whether resources have been registered on the server
	 * If true, the resources capability will be included
	 */
	hasResources?: boolean;
}

/**
 * Registers MCP capabilities on a server instance
 *
 * This utility function handles:
 * - Configuring tools, prompts, and resources capabilities
 * - Determining listChanged flags based on transport mode
 * - Removing auto-added completions capability
 *
 * @param server - The McpServer instance to register capabilities on
 * @param sharedApiClient - The shared API client for transport info
 * @param options - Configuration options for capabilities
 */
export function registerCapabilities(
	server: McpServer,
	sharedApiClient: McpApiClient,
	options: RegisterCapabilitiesOptions = {}
): void {
	const transportInfo = sharedApiClient.getTransportInfo();
	const { hasResources = false } = options;

	const capabilities: ServerCapabilities = {
		tools: {
			listChanged: !transportInfo?.jsonResponseEnabled,
		},
		prompts: {
			listChanged: false,
		},
		...(hasResources
			? {
					resources: {
						listChanged: false,
					},
				}
			: {}),
	};

	server.server.registerCapabilities(capabilities);

	// Remove the completions capability that was auto-added by prompt registration
	// The MCP SDK automatically adds this when prompts are registered, but we don't want it
	// https://github.com/modelcontextprotocol/typescript-sdk/pull/1024
	// @ts-expect-error quick workaround for an SDK issue (adding prompt/resource adds completions)
	if (server.server._capabilities?.completions) {
		// @ts-expect-error quick workaround for an SDK issue (adding prompt/resource adds completions)
		delete server.server._capabilities.completions;
		logger.debug('Removed auto-added completions capability');
	}
}
