import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { searchMeetingsSchema, getMeetingSummarySchema } from '../definitions/searchTools.js';

export async function handleSearchMeetings(request: CallToolRequest) {
  try {
    const args = searchMeetingsSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query SearchMeetings($searchQuery: String!, $limit: Int, $filters: SearchFilters) {
        search(
          query: $searchQuery
          limit: $limit
          filters: $filters
        ) {
          results {
            transcript {
              id
              title
              date
              duration
              summary {
                overview
                keywords
              }
            }
            matches {
              text
              speaker_name
              start_time
              end_time
              confidence_score
            }
          }
          total_results
          search_time_ms
        }
      }
    `;

    const variables = {
      searchQuery: args.query,
      limit: args.limit,
      filters: args.filters
        ? {
            date_start: args.filters.start_date,
            date_end: args.filters.end_date,
            user_id: args.filters.user_id,
            meeting_title: args.filters.meeting_title,
          }
        : null,
    };

    const result = await client.query(query, variables);

    safeLog(
      'info',
      `Search completed: ${result.search?.total_results || 0} results found in ${result.search?.search_time_ms}ms`,
    );

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                query: args.query,
                results: result.search?.results || [],
                total_results: result.search?.total_results || 0,
                search_time_ms: result.search?.search_time_ms || 0,
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
              tool: 'search_meetings',
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
      query GetMeetingSummary($transcriptId: String!, $summaryType: String!, $includeTimestamps: Boolean!) {
        transcript(id: $transcriptId) {
          id
          title
          date
          summary {
            overview
            action_items {
              text
              assignee
              due_date
              timestamp @include(if: $includeTimestamps)
            }
            key_topics {
              topic
              mentions
              timestamp @include(if: $includeTimestamps)
            }
            decisions {
              text
              decision_maker
              timestamp @include(if: $includeTimestamps)
            }
            keywords
            sentiment_analysis
          }
          ai_filters {
            sentiment
            questions_asked
            talk_time_percentage
          }
        }
      }
    `;

    const variables = {
      transcriptId: args.transcript_id,
      summaryType: args.summary_type,
      includeTimestamps: args.include_timestamps || false,
    };

    const result = await client.query(query, variables);

    if (!result.transcript) {
      throw new Error(`Transcript with ID ${args.transcript_id} not found`);
    }

    let formattedSummary;
    const summary = result.transcript.summary;

    switch (args.summary_type) {
      case 'action_items':
        formattedSummary = {
          type: 'action_items',
          items: summary.action_items || [],
        };
        break;
      case 'key_topics':
        formattedSummary = {
          type: 'key_topics',
          topics: summary.key_topics || [],
        };
        break;
      case 'decisions':
        formattedSummary = {
          type: 'decisions',
          decisions: summary.decisions || [],
        };
        break;
      default: 
        formattedSummary = {
          type: 'overview',
          overview: summary.overview,
          keywords: summary.keywords,
          sentiment: summary.sentiment_analysis,
          ai_insights: result.transcript.ai_filters,
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
                meeting_date: result.transcript.date,
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
              tool: 'get_meeting_summary',
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
