import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { listMeetingsSchema } from '../definitions/meetingTools.js';

export async function handleListMeetings(request: CallToolRequest) {
  try {
    const args = listMeetingsSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query GetMeetings($limit: Int, $offset: Int, $startDate: String, $endDate: String, $userId: String) {
        transcripts(
          limit: $limit
          offset: $offset
          date_start: $startDate
          date_end: $endDate
          user_id: $userId
        ) {
          id
          title
          date
          duration
          meeting_url
          summary {
            overview
            action_items
            keywords
          }
          participants {
            name
            email
          }
          ai_filters {
            sentiment
            talk_time
          }
        }
      }
    `;

    const variables = {
      limit: args.limit,
      offset: args.offset,
      startDate: args.start_date,
      endDate: args.end_date,
      userId: args.user_id,
    };

    const result = await client.query(query, variables);

    safeLog('info', `Retrieved ${result.transcripts?.length || 0} meetings`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                meetings: result.transcripts || [],
                total_count: result.transcripts?.length || 0,
                pagination: {
                  limit: args.limit,
                  offset: args.offset,
                },
              },
            },
            null,
            2,
          ),
        },
      ],
    };
  } catch (error) {
    safeLog('error', `Error in handleListMeetings: ${error}`);
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
              tool: 'list_meetings',
            },
            null,
            2,
          ),
        },
      ],
      isError: true,
    };
  }
}
