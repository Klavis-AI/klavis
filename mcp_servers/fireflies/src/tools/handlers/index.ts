export { handleListMeetings } from './meetingHandler.js';
export { handleGetTranscript, handleExportTranscript } from './transcriptHandler.js';
export { handleSearchMeetings, handleGetMeetingSummary } from './searchHandler.js';

import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { handleListMeetings } from './meetingHandler.js';
import { handleGetTranscript, handleExportTranscript } from './transcriptHandler.js';
import { handleSearchMeetings, handleGetMeetingSummary } from './searchHandler.js';

export async function handleToolCall(request: CallToolRequest) {
  const toolName = request.params.name;

  switch (toolName) {
    case 'fireflies_list_meetings':
      return handleListMeetings(request);

    case 'fireflies_get_transcript':
      return handleGetTranscript(request);

    case 'fireflies_export_transcript':
      return handleExportTranscript(request);

    case 'fireflies_search_meetings':
      return handleSearchMeetings(request);

    case 'fireflies_get_meeting_summary':
      return handleGetMeetingSummary(request);

    default:
      throw new Error(`Unknown tool: ${toolName}`);
  }
}
