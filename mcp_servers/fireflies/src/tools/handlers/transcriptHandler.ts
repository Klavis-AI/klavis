import { CallToolRequest } from '@modelcontextprotocol/sdk/types.js';
import { getFirefliesClient, safeLog } from '../../client/firefliesClient.js';
import { getTranscriptSchema, exportTranscriptSchema } from '../definitions/transcriptTools.js';

export async function handleGetTranscript(request: CallToolRequest) {
  try {
    const args = getTranscriptSchema.parse(request.params.arguments || {});
    const client = getFirefliesClient();

    const query = `
      query GetTranscript($transcriptId: String!) {
        transcript(id: $transcriptId) {
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

    const variables = {
      transcriptId: args.transcript_id,
    };

    const result = await client.query(query, variables);

    if (!result.transcript) {
      throw new Error(`Transcript with ID ${args.transcript_id} not found`);
    }

    const response: any = {
      id: result.transcript.id,
      title: result.transcript.title,
      date: result.transcript.date,
      duration: result.transcript.duration,
      host_email: result.transcript.host_email,
      participants: result.transcript.participants,
      sentences: result.transcript.sentences,
    };

    if (args.include_summary) {
      response.summary = result.transcript.summary;
    }

    if (args.include_action_items) {
      response.action_items = result.transcript.summary?.action_items;
    }

    safeLog('info', `Retrieved transcript: ${result.transcript.title}`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: response,
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
              tool: 'fireflies_get_transcript',
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

    const query = `
      query GetTranscript($transcriptId: String!) {
        transcript(id: $transcriptId) {
          id
          title
          date
          duration
          host_email
          participants
          sentences {
            text
            speaker_name
            start_time
            end_time
          }
        }
      }
    `;

    const result = await client.query(query, { transcriptId: args.transcript_id });

    if (!result.transcript) {
      throw new Error(`Transcript with ID ${args.transcript_id} not found`);
    }

    let formattedContent = '';
    const transcript = result.transcript;

    if (args.format === 'txt') {
      formattedContent = `Meeting: ${transcript.title}\nDate: ${new Date(transcript.date).toLocaleString()}\nDuration: ${transcript.duration}s\n\n`;

      transcript.sentences.forEach((sentence: any) => {
        if (args.include_timestamps) {
          formattedContent += `[${sentence.start_time}s] `;
        }
        if (args.include_speaker_labels) {
          formattedContent += `${sentence.speaker_name}: `;
        }
        formattedContent += `${sentence.text}\n`;
      });
    }

    safeLog('info', `Exported transcript ${args.transcript_id} in ${args.format} format`);

    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(
            {
              success: true,
              data: {
                transcript_id: args.transcript_id,
                format: args.format,
                content: formattedContent,
                filename: `${transcript.title}_${new Date(transcript.date).toISOString().split('T')[0]}.${args.format}`,
                note: 'Export functionality simulated - Fireflies API may not support direct file export',
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
              tool: 'fireflies_export_transcript',
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
