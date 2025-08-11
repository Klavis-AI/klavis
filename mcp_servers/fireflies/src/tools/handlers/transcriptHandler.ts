import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { getTranscriptSchema, exportTranscriptSchema } from '../definitions/transcriptTools.js';

export async function handleGetTranscript(request: CallToolRequest) {
  try {
    const args = getTranscriptSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query GetTranscript($transcriptId: String!, $includeSummary: Boolean!, $includeActionItems: Boolean!) {
        transcript(id: $transcriptId) {
          id
          title
          date
          duration
          sentences {
            text
            speaker_name
            start_time
            end_time
          }
          summary @include(if: $includeSummary) {
            overview
            keywords
            outline
          }
          action_items @include(if: $includeActionItems) {
            text
            assignee
            due_date
          }
          participants {
            name
            email
            talk_time
          }
        }
      }
    `;

    const variables = {
      transcriptId: args.transcript_id,
      includeSummary: args.include_summary || false,
      includeActionItems: args.include_action_items || false,
    };

    const result = await client.query(query, variables);

    if (!result.transcript) {
      throw new Error(`Transcript with ID ${args.transcript_id} not found`);
    }

    safeLog('info', `Retrieved transcript: ${result.transcript.title}`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: result.transcript,
            },
            null,
            2,
          ),
        },
      ],
    };
  } catch (error) {
    safeLog('error', `Error in handleGetTranscript: ${error}`);
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
              tool: 'get_transcript',
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

export async function handleExportTranscript(request: CallToolRequest) {
  try {
    const args = exportTranscriptSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const mutation = `
      mutation ExportTranscript($transcriptId: String!, $format: String!, $includeTimestamps: Boolean!, $includeSpeakerLabels: Boolean!) {
        exportTranscript(
          transcript_id: $transcriptId
          format: $format
          include_timestamps: $includeTimestamps
          include_speaker_labels: $includeSpeakerLabels
        ) {
          download_url
          file_name
          format
          expires_at
        }
      }
    `;

    const variables = {
      transcriptId: args.transcript_id,
      format: args.format,
      includeTimestamps: args.include_timestamps,
      includeSpeakerLabels: args.include_speaker_labels,
    };

    const result = await client.mutate(mutation, variables);

    safeLog(
      'info',
      `Generated export for transcript ${args.transcript_id} in ${args.format} format`,
    );

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                export_info: result.exportTranscript,
                message: `Transcript exported successfully. Download URL will expire at ${result.exportTranscript?.expires_at}`,
              },
            },
            null,
            2,
          ),
        },
      ],
    };
  } catch (error) {
    safeLog('error', `Error in handleExportTranscript: ${error}`);
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: false,
              error: error instanceof Error ? error.message : 'Unknown error occurred',
              tool: 'export_transcript',
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
