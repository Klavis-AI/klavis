import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { safeLog } from './client/firefliesClient.js';
import { listMeetingsDefinition } from './tools/definitions/meetingTools.js';
import {
  getTranscriptDefinition,
  exportTranscriptDefinition,
} from './tools/definitions/transcriptTools.js';
import {
  searchMeetingsDefinition,
  getMeetingSummaryDefinition,
} from './tools/definitions/searchTools.js';
import { handleListMeetings } from './tools/handlers/meetingHandler.js';
import { handleGetTranscript, handleExportTranscript } from './tools/handlers/transcriptHandler.js';
import { handleSearchMeetings, handleGetMeetingSummary } from './tools/handlers/searchHandler.js';
import { createErrorResponse } from './utils/errors.js';

let mcpServerInstance: Server | null = null;

export const getFirefliesMcpServer = () => {
  if (!mcpServerInstance) {
    mcpServerInstance = new Server(
      {
        name: 'fireflies-mcp-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      },
    );

    mcpServerInstance.setRequestHandler(ListToolsRequestSchema, async () => {
      safeLog('info', 'Listing available Fireflies tools');
      return {
        tools: [
          listMeetingsDefinition,
          getTranscriptDefinition,
          exportTranscriptDefinition,
          searchMeetingsDefinition,
          getMeetingSummaryDefinition,
        ],
      };
    });

    mcpServerInstance.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      safeLog('info', `Calling tool: ${toolName}`);

      try {
        switch (toolName) {
          case 'fireflies_list_meetings':
            return await handleListMeetings(request);

          case 'fireflies_get_transcript':
            return await handleGetTranscript(request);

          case 'fireflies_export_transcript':
            return await handleExportTranscript(request);

          case 'fireflies_search_meetings':
            return await handleSearchMeetings(request);

          case 'fireflies_get_meeting_summary':
            return await handleGetMeetingSummary(request);

          default:
            throw new Error(`Unknown tool: ${toolName}`);
        }
      } catch (error) {
        safeLog('error', `Tool ${toolName} failed: ${error}`);
        return createErrorResponse(error, toolName);
      }
    });

    safeLog('info', 'Fireflies MCP server initialized with all 5 tools');
  }

  return mcpServerInstance;
};

/**
 * Create a new server instance (useful for testing)
 */
export function createFirefliesMcpServer(): Server {
  const server = new Server(
    {
      name: 'fireflies-mcp-server',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    safeLog('info', 'Listing available Fireflies tools');
    return {
      tools: [
        listMeetingsDefinition,
        getTranscriptDefinition,
        exportTranscriptDefinition,
        searchMeetingsDefinition,
        getMeetingSummaryDefinition,
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const toolName = request.params.name;
    safeLog('info', `Calling tool: ${toolName}`);

    try {
      switch (toolName) {
        case 'fireflies_list_meetings':
          return await handleListMeetings(request);

        case 'fireflies_get_transcript':
          return await handleGetTranscript(request);

        case 'fireflies_export_transcript':
          return await handleExportTranscript(request);

        case 'fireflies_search_meetings':
          return await handleSearchMeetings(request);

        case 'fireflies_get_meeting_summary':
          return await handleGetMeetingSummary(request);

        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }
    } catch (error) {
      safeLog('error', `Tool ${toolName} failed: ${error}`);
      return createErrorResponse(error, toolName);
    }
  });

  safeLog('info', 'New Fireflies MCP server instance created with all tools');

  return server;
}

/**
 * Reset the singleton server instance (useful for testing)
 */
export function resetServerInstance(): void {
  mcpServerInstance = null;
  safeLog('info', 'Fireflies MCP server instance reset');
}

/**
 * Get server info
 */
export function getServerInfo() {
  return {
    name: 'fireflies-mcp-server',
    version: '1.0.0',
    description: 'MCP server for Fireflies.ai meeting transcription and analysis integration',
    capabilities: ['tools'],
    tools: {
      count: 5,
      available: [
        'fireflies_list_meetings',
        'fireflies_get_transcript',
        'fireflies_export_transcript',
        'fireflies_search_meetings',
        'fireflies_get_meeting_summary',
      ],
    },
    categories: {
      meeting_management: ['fireflies_list_meetings'],
      transcript_operations: ['fireflies_get_transcript', 'fireflies_export_transcript'],
      search_and_analysis: ['fireflies_search_meetings', 'fireflies_get_meeting_summary'],
    },
  };
}
