export * from './meetingTools.js';
export * from './transcriptTools.js';
export * from './searchTools.js';

import { listMeetingsDefinition } from './meetingTools.js';
import { getTranscriptDefinition, exportTranscriptDefinition } from './transcriptTools.js';
import { searchMeetingsDefinition, getMeetingSummaryDefinition } from './searchTools.js';

export const allToolDefinitions = [
  listMeetingsDefinition,
  getTranscriptDefinition,
  exportTranscriptDefinition,
  searchMeetingsDefinition,
  getMeetingSummaryDefinition,
];
