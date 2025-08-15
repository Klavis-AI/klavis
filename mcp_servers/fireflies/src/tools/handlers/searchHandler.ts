import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { searchMeetingsSchema, getMeetingSummarySchema } from '../definitions/searchTools.js';

export async function handleSearchMeetings(request: CallToolRequest) {
  try {
    const args = searchMeetingsSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query SearchTranscripts($limit: Int, $title: String) {
        transcripts(limit: $limit, title: $title) {
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
          sentences {
            text
            speaker_name
            start_time
            end_time
          }
        }
      }
    `;

    const variables: Record<string, any> = {
      limit: args.limit || 50,
    };

    if (args.filters?.meeting_title) {
      variables.title = args.filters.meeting_title;
    }

    const result = await client.query(query, variables);
    const transcripts = result.transcripts || [];

    const searchResults = transcripts
      .filter((transcript: any) => {
        const searchQuery = args.query.toLowerCase();

        if (transcript.title?.toLowerCase().includes(searchQuery)) return true;

        if (transcript.summary?.overview?.toLowerCase().includes(searchQuery)) return true;

        if (transcript.summary?.action_items?.toLowerCase().includes(searchQuery)) return true;

        if (
          transcript.summary?.keywords?.some((keyword: string) =>
            keyword.toLowerCase().includes(searchQuery),
          )
        )
          return true;

        if (
          transcript.sentences?.some((sentence: any) =>
            sentence.text?.toLowerCase().includes(searchQuery),
          )
        )
          return true;

        return false;
      })
      .slice(0, args.limit || 10);

    safeLog('info', `Search completed: ${searchResults.length} results found for "${args.query}"`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                query: args.query,
                results: searchResults,
                total_results: searchResults.length,
                note: 'Search performed client-side across transcript content',
              },
            },
            null,
            2,
          ),
        },
      ],
    };
  } catch (error) {
    safeLog('error', `Error in handleSearchMeetings: ${error}`);
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
              tool: 'fireflies_search_meetings',
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

export async function handleGetMeetingSummary(request: CallToolRequest) {
  try {
    const args = getMeetingSummarySchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query GetTranscript($transcriptId: String!) {
        transcript(id: $transcriptId) {
          id
          title
          date
          duration
          summary {
            overview
            action_items
            keywords
          }
        }
      }
    `;

    const result = await client.query(query, { transcriptId: args.transcript_id });

    if (!result.transcript) {
      throw new Error(`Transcript with ID ${args.transcript_id} not found`);
    }

    let formattedSummary;
    const summary = result.transcript.summary;

    switch (args.summary_type) {
      case 'action_items':
        formattedSummary = {
          type: 'action_items',
          content: summary?.action_items || 'No action items found',
        };
        break;
      case 'key_topics':
        formattedSummary = {
          type: 'key_topics',
          content: summary?.keywords || [],
        };
        break;
      case 'decisions':
        const decisions =
          summary?.overview?.match(/निर्णय|ठरवण्यात आले|निश्चित केले|([^।]*निर्णय[^।]*)/gi) || [];
        formattedSummary = {
          type: 'decisions',
          content: decisions,
        };
        break;
      default:
        formattedSummary = {
          type: 'overview',
          content: summary?.overview || 'No overview available',
          keywords: summary?.keywords || [],
          action_items: summary?.action_items || 'No action items found',
        };
    }

    safeLog('info', `Generated ${args.summary_type} summary for transcript ${args.transcript_id}`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                transcript_id: args.transcript_id,
                meeting_title: result.transcript.title,
                meeting_date: new Date(result.transcript.date).toLocaleString(),
                summary: formattedSummary,
              },
            },
            null,
            2,
          ),
        },
      ],
    };
  } catch (error) {
    safeLog('error', `Error in handleGetMeetingSummary: ${error}`);
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
              tool: 'fireflies_get_meeting_summary',
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
