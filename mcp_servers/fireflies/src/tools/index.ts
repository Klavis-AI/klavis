import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { allToolDefinitions } from './definitions/index.js';
import { handleToolCall } from './handlers/index.js';
import { safeLog } from '../client/firefliesClient.js';

/**
 * Register all Fireflies tools with the MCP server
 */
export function registerTools(server: Server): void {
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    safeLog('info', 'Listing available Fireflies tools');
    return {
      tools: allToolDefinitions,
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const toolName = request.params.name;
    safeLog('info', `Calling tool: ${toolName}`);

    try {
      const result = await handleToolCall(request);
      safeLog('info', `Tool ${toolName} executed successfully`);
      return result;
    } catch (error) {
      safeLog('error', `Tool ${toolName} failed: ${error}`);
      throw error;
    }
  });

  safeLog('info', `Registered ${allToolDefinitions.length} Fireflies tools`);
}

/**
 * Get all available tool definitions
 */
export function getToolDefinitions() {
  return allToolDefinitions;
}

/**
 * Get tool definition by name
 */
export function getToolDefinition(toolName: string) {
  return allToolDefinitions.find((tool) => tool.name === toolName);
}

/**
 * Get list of all tool names
 */
export function getToolNames(): string[] {
  return allToolDefinitions.map((tool) => tool.name);
}

export * from './definitions/index.js';
export * from './handlers/index.js';

export const FIREFLIES_TOOLS = {
  MEETINGS: {
    LIST: 'fireflies_list_meetings',
  },
  TRANSCRIPTS: {
    GET: 'fireflies_get_transcript',
    EXPORT: 'fireflies_export_transcript',
  },
  SEARCH: {
    MEETINGS: 'fireflies_search_meetings',
    SUMMARY: 'fireflies_get_meeting_summary',
  },
} as const;

export const TOOL_CATEGORIES = {
  meeting_management: ['fireflies_list_meetings'],
  transcript_operations: ['fireflies_get_transcript', 'fireflies_export_transcript'],
  search_and_analysis: ['fireflies_search_meetings', 'fireflies_get_meeting_summary'],
} as const;

/**
 * Check if a tool name is valid
 */
export function isValidTool(toolName: string): boolean {
  return getToolNames().includes(toolName);
}

/**
 * Get tools by category
 */
export function getToolsByCategory(category: keyof typeof TOOL_CATEGORIES): readonly string[] {
  return TOOL_CATEGORIES[category] || [];
}
