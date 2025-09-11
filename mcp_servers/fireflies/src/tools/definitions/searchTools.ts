import { z } from 'zod';

export const searchMeetingsSchema = z.object({
  query: z.string().describe('Search query to find in meeting content'),
  limit: z.number().min(1).max(50).default(10).optional().describe('Number of results to return'),
  filters: z
    .object({
      start_date: z.string().optional().describe('Start date filter (YYYY-MM-DD)'),
      end_date: z.string().optional().describe('End date filter (YYYY-MM-DD)'),
      user_id: z.string().optional().describe('Filter by user ID'),
      meeting_title: z.string().optional().describe('Filter by meeting title'),
    })
    .optional()
    .describe('Additional search filters'),
});

export const searchMeetingsDefinition = {
  name: 'fireflies_search_meetings',
  description: 'Search across meeting content using natural language queries with optional filters',
  inputSchema: {
    type: 'object' as const,
    properties: {
      query: {
        type: 'string' as const,
        description: 'Search query to find in meeting content',
      },
      limit: {
        type: 'number' as const,
        description: 'Number of results to return',
        minimum: 1,
        maximum: 50,
        default: 10,
      },
      filters: {
        type: 'object' as const,
        description: 'Additional search filters',
        properties: {
          start_date: {
            type: 'string' as const,
            description: 'Start date filter (YYYY-MM-DD)',
            pattern: '^\\d{4}-\\d{2}-\\d{2}$',
          },
          end_date: {
            type: 'string' as const,
            description: 'End date filter (YYYY-MM-DD)',
            pattern: '^\\d{4}-\\d{2}-\\d{2}$',
          },
          user_id: {
            type: 'string' as const,
            description: 'Filter by user ID',
          },
          meeting_title: {
            type: 'string' as const,
            description: 'Filter by meeting title',
          },
        },
        additionalProperties: false,
      },
    },
    required: ['query'],
    additionalProperties: false,
  },
};

export const getMeetingSummarySchema = z.object({
  transcript_id: z.string().describe('The ID of the transcript to summarize'),
  summary_type: z
    .enum(['overview', 'action_items', 'key_topics', 'decisions'])
    .default('overview')
    .describe('Type of summary to generate'),
  include_timestamps: z
    .boolean()
    .default(false)
    .optional()
    .describe('Include timestamps in summary'),
});

export const getMeetingSummaryDefinition = {
  name: 'fireflies_get_meeting_summary',
  description: 'Extract key insights, action items, decisions, and topics from meeting transcripts',
  inputSchema: {
    type: 'object' as const,
    properties: {
      transcript_id: {
        type: 'string' as const,
        description: 'The ID of the transcript to summarize',
      },
      summary_type: {
        type: 'string' as const,
        enum: ['overview', 'action_items', 'key_topics', 'decisions'],
        description: 'Type of summary to generate',
        default: 'overview',
      },
      include_timestamps: {
        type: 'boolean' as const,
        description: 'Include timestamps in summary',
        default: false,
      },
    },
    required: ['transcript_id'],
    additionalProperties: false,
  },
};
