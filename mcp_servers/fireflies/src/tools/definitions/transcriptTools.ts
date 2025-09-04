import { z } from 'zod';

export const getTranscriptSchema = z.object({
  transcript_id: z.string().describe('The ID of the transcript to retrieve'),
  include_summary: z
    .boolean()
    .default(false)
    .optional()
    .describe('Include meeting summary in response'),
  include_action_items: z
    .boolean()
    .default(false)
    .optional()
    .describe('Include action items in response'),
});

export const getTranscriptDefinition = {
  name: 'fireflies_get_transcript',
  description:
    'Fetch full meeting transcript by transcript ID with optional summary and action items',
  inputSchema: {
    type: 'object' as const,
    properties: {
      transcript_id: {
        type: 'string' as const,
        description: 'The ID of the transcript to retrieve',
      },
      include_summary: {
        type: 'boolean' as const,
        description: 'Include meeting summary in response',
        default: false,
      },
      include_action_items: {
        type: 'boolean' as const,
        description: 'Include action items in response',
        default: false,
      },
    },
    required: ['transcript_id'],
    additionalProperties: false,
  },
};

export const exportTranscriptSchema = z.object({
  transcript_id: z.string().describe('The ID of the transcript to export'),
  format: z.enum(['txt', 'pdf', 'docx', 'srt', 'vtt']).default('txt').describe('Export format'),
  include_timestamps: z.boolean().default(true).optional().describe('Include timestamps in export'),
  include_speaker_labels: z
    .boolean()
    .default(true)
    .optional()
    .describe('Include speaker labels in export'),
});

export const exportTranscriptDefinition = {
  name: 'fireflies_export_transcript',
  description: 'Download transcript in various formats (txt, pdf, docx, srt, vtt)',
  inputSchema: {
    type: 'object' as const,
    properties: {
      transcript_id: {
        type: 'string' as const,
        description: 'The ID of the transcript to export',
      },
      format: {
        type: 'string' as const,
        enum: ['txt', 'pdf', 'docx', 'srt', 'vtt'],
        description: 'Export format',
        default: 'txt',
      },
      include_timestamps: {
        type: 'boolean' as const,
        description: 'Include timestamps in export',
        default: true,
      },
      include_speaker_labels: {
        type: 'boolean' as const,
        description: 'Include speaker labels in export',
        default: true,
      },
    },
    required: ['transcript_id'],
    additionalProperties: false,
  },
};
