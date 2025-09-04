import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { listMeetingsSchema } from '../definitions/meetingTools.js';

export async function handleListMeetings(request: CallToolRequest) {
  try {
    const args = listMeetingsSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query Transcripts($limit: Int, $skip: Int, $userId: String, $hostEmail: String, $participantEmail: String, $title: String) {
        transcripts(
          limit: $limit
          skip: $skip
          user_id: $userId
          host_email: $hostEmail
          participant_email: $participantEmail
          title: $title
        ) {
          id
          title
          date
          duration
          host_email
          participants
          summary {
            overview
            action_items
            keywords
          }
        }
      }
    `;

    const variables: Record<string, any> = {};

    if (args.limit) variables.limit = args.limit;
    if (args.offset) variables.skip = args.offset;
    if (args.user_id) variables.userId = args.user_id;

    const result = await client.query(query, variables);

    safeLog('info', `Retrieved ${result.transcripts?.length || 0} meetings`);

    let filteredTranscripts = result.transcripts || [];

    if (args.start_date || args.end_date) {
      filteredTranscripts = filteredTranscripts.filter((transcript: any) => {
        const transcriptDate = new Date(transcript.date);

        if (args.start_date && transcriptDate < new Date(args.start_date)) {
          return false;
        }

        if (args.end_date && transcriptDate > new Date(args.end_date)) {
          return false;
        }

        return true;
      });
    }

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                meetings: filteredTranscripts,
                total_count: filteredTranscripts.length,
                pagination: {
                  limit: args.limit || 10,
                  offset: args.offset || 0,
                },
                api_response: 'Successfully retrieved meetings from Fireflies API',
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
              tool: 'fireflies_list_meetings',
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
