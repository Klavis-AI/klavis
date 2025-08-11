import { z } from 'zod';

export const listMeetingsSchema = z.object({
  limit: z
    .number()
    .min(1)
    .max(100)
    .default(10)
    .optional()
    .describe('Number of meetings to retrieve (1-100)'),
  offset: z
    .number()
    .min(0)
    .default(0)
    .optional()
    .describe('Number of meetings to skip for pagination'),
  start_date: z.string().optional().describe('Start date filter (YYYY-MM-DD format)'),
  end_date: z.string().optional().describe('End date filter (YYYY-MM-DD format)'),
  user_id: z.string().optional().describe('Filter meetings by specific user ID'),
});

export const listMeetingsDefinition = {
  name: 'fireflies_list_meetings',
  description:
    'Retrieve recent meetings from Fireflies with optional filters for date range and user',
  inputSchema: {
    type: 'object' as const,
    properties: {
      limit: {
        type: 'number' as const,
        description: 'Number of meetings to retrieve (1-100)',
        minimum: 1,
        maximum: 100,
        default: 10,
      },
      offset: {
        type: 'number' as const,
        description: 'Number of meetings to skip for pagination',
        minimum: 0,
        default: 0,
      },
      start_date: {
        type: 'string' as const,
        description: 'Start date filter (YYYY-MM-DD format)',
        pattern: '^\\d{4}-\\d{2}-\\d{2}$',
      },
      end_date: {
        type: 'string' as const,
        description: 'End date filter (YYYY-MM-DD format)',
        pattern: '^\\d{4}-\\d{2}-\\d{2}$',
      },
      user_id: {
        type: 'string' as const,
        description: 'Filter meetings by specific user ID',
      },
    },
    additionalProperties: false,
  },
};
