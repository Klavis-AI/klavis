import { z } from 'zod';
import { FirefliesValidationError } from './errors.js';

/**
 * Common validation schemas
 */
export const commonSchemas = {
  transcriptId: z.string().min(1, 'Transcript ID is required').max(100, 'Transcript ID too long'),
  userId: z.string().min(1, 'User ID is required').max(100, 'User ID too long'),
  meetingId: z.string().min(1, 'Meeting ID is required').max(100, 'Meeting ID too long'),

  dateString: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  isoDateString: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/, 'Invalid ISO date format'),

  limit: z.number().int().min(1, 'Limit must be at least 1').max(100, 'Limit cannot exceed 100'),
  offset: z.number().int().min(0, 'Offset must be non-negative'),

  searchQuery: z.string().min(1, 'Search query cannot be empty').max(500, 'Search query too long'),
  title: z.string().min(1, 'Title is required').max(200, 'Title too long'),
  email: z.string().email('Invalid email format'),

  exportFormat: z.enum(['txt', 'pdf', 'docx', 'srt', 'vtt'], {
    errorMap: () => ({
      message: 'Invalid export format. Must be one of: txt, pdf, docx, srt, vtt',
    }),
  }),
  summaryType: z.enum(['overview', 'action_items', 'key_topics', 'decisions'], {
    errorMap: () => ({
      message:
        'Invalid summary type. Must be one of: overview, action_items, key_topics, decisions',
    }),
  }),
};

/**
 * Date range validation
 */
export const dateRangeSchema = z
  .object({
    start_date: commonSchemas.dateString.optional(),
    end_date: commonSchemas.dateString.optional(),
  })
  .refine(
    (data) => {
      if (data.start_date && data.end_date) {
        return new Date(data.start_date) <= new Date(data.end_date);
      }
      return true;
    },
    {
      message: 'Start date must be before or equal to end date',
      path: ['end_date'],
    },
  );

/**
 * Validation utility class
 */
export class ValidationUtils {
  /**
   * Validate API key format
   */
  static validateApiKey(apiKey: string): boolean {
    if (!apiKey || typeof apiKey !== 'string') {
      return false;
    }

    return apiKey.length >= 32 && /^[a-zA-Z0-9_-]+$/.test(apiKey);
  }

  /**
   * Validate date range
   */
  static validateDateRange(startDate?: string, endDate?: string): void {
    if (startDate && !this.isValidDateString(startDate)) {
      throw new FirefliesValidationError('Invalid start date format. Use YYYY-MM-DD', 'start_date');
    }

    if (endDate && !this.isValidDateString(endDate)) {
      throw new FirefliesValidationError('Invalid end date format. Use YYYY-MM-DD', 'end_date');
    }

    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);

      if (start > end) {
        throw new FirefliesValidationError(
          'Start date must be before or equal to end date',
          'date_range',
        );
      }

      const now = new Date();
      const maxFutureDate = new Date(now.getTime() + 365 * 24 * 60 * 60 * 1000);

      if (end > maxFutureDate) {
        throw new FirefliesValidationError(
          'End date cannot be more than 1 year in the future',
          'end_date',
        );
      }
    }
  }

  /**
   * Validate date string format
   */
  static isValidDateString(dateString: string): boolean {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(dateString)) {
      return false;
    }

    const date = new Date(dateString);
    return (
      date instanceof Date && !isNaN(date.getTime()) && date.toISOString().startsWith(dateString)
    );
  }

  /**
   * Validate pagination parameters
   */
  static validatePagination(limit?: number, offset?: number): void {
    if (limit !== undefined) {
      if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
        throw new FirefliesValidationError('Limit must be an integer between 1 and 100', 'limit');
      }
    }

    if (offset !== undefined) {
      if (!Number.isInteger(offset) || offset < 0) {
        throw new FirefliesValidationError('Offset must be a non-negative integer', 'offset');
      }
    }
  }

  /**
   * Validate search query
   */
  static validateSearchQuery(query: string): void {
    if (!query || typeof query !== 'string') {
      throw new FirefliesValidationError('Search query is required and must be a string', 'query');
    }

    if (query.trim().length === 0) {
      throw new FirefliesValidationError('Search query cannot be empty', 'query');
    }

    if (query.length > 500) {
      throw new FirefliesValidationError('Search query cannot exceed 500 characters', 'query');
    }

    const dangerousPatterns = [/<script/i, /javascript:/i, /on\w+\s*=/i, /<iframe/i];

    if (dangerousPatterns.some((pattern) => pattern.test(query))) {
      throw new FirefliesValidationError(
        'Search query contains potentially unsafe content',
        'query',
      );
    }
  }

  /**
   * Validate transcript ID
   */
  static validateTranscriptId(transcriptId: string): void {
    if (!transcriptId || typeof transcriptId !== 'string') {
      throw new FirefliesValidationError(
        'Transcript ID is required and must be a string',
        'transcript_id',
      );
    }

    if (transcriptId.trim().length === 0) {
      throw new FirefliesValidationError('Transcript ID cannot be empty', 'transcript_id');
    }

    if (transcriptId.length > 100) {
      throw new FirefliesValidationError(
        'Transcript ID cannot exceed 100 characters',
        'transcript_id',
      );
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(transcriptId)) {
      throw new FirefliesValidationError(
        'Transcript ID contains invalid characters',
        'transcript_id',
      );
    }
  }

  /**
   * Validate export format
   */
  static validateExportFormat(format: string): void {
    const validFormats = ['txt', 'pdf', 'docx', 'srt', 'vtt'];

    if (!validFormats.includes(format)) {
      throw new FirefliesValidationError(
        `Invalid export format '${format}'. Must be one of: ${validFormats.join(', ')}`,
        'format',
      );
    }
  }

  /**
   * Validate summary type
   */
  static validateSummaryType(summaryType: string): void {
    const validTypes = ['overview', 'action_items', 'key_topics', 'decisions'];

    if (!validTypes.includes(summaryType)) {
      throw new FirefliesValidationError(
        `Invalid summary type '${summaryType}'. Must be one of: ${validTypes.join(', ')}`,
        'summary_type',
      );
    }
  }

  /**
   * Sanitize string input
   */
  static sanitizeString(input: string): string {
    if (typeof input !== 'string') {
      return '';
    }

    return input
      .trim()
      .replace(/[\x00-\x1f\x7f-\x9f]/g, '')
      .replace(/\s+/g, ' ');
  }

  /**
   * Validate email format
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate boolean parameters
   */
  static validateBoolean(value: any, fieldName: string): boolean {
    if (value === undefined || value === null) {
      return false;
    }

    if (typeof value === 'boolean') {
      return value;
    }

    if (typeof value === 'string') {
      const lowerValue = value.toLowerCase();
      if (lowerValue === 'true' || lowerValue === '1') {
        return true;
      }
      if (lowerValue === 'false' || lowerValue === '0') {
        return false;
      }
    }

    throw new FirefliesValidationError(`Invalid boolean value for ${fieldName}`, fieldName);
  }

  /**
   * Validate and parse number
   */
  static validateNumber(value: any, fieldName: string, min?: number, max?: number): number {
    let numValue: number;

    if (typeof value === 'number') {
      numValue = value;
    } else if (typeof value === 'string') {
      numValue = parseFloat(value);
    } else {
      throw new FirefliesValidationError(`${fieldName} must be a number`, fieldName);
    }

    if (isNaN(numValue)) {
      throw new FirefliesValidationError(`${fieldName} must be a valid number`, fieldName);
    }

    if (min !== undefined && numValue < min) {
      throw new FirefliesValidationError(`${fieldName} must be at least ${min}`, fieldName);
    }

    if (max !== undefined && numValue > max) {
      throw new FirefliesValidationError(`${fieldName} cannot exceed ${max}`, fieldName);
    }

    return numValue;
  }
}

/**
 * Tool-specific validation schemas
 */
export const toolValidationSchemas = {
  listMeetings: z
    .object({
      limit: commonSchemas.limit.optional(),
      offset: commonSchemas.offset.optional(),
      start_date: commonSchemas.dateString.optional(),
      end_date: commonSchemas.dateString.optional(),
      user_id: commonSchemas.userId.optional(),
    })
    .and(dateRangeSchema),

  getTranscript: z.object({
    transcript_id: commonSchemas.transcriptId,
    include_summary: z.boolean().optional(),
    include_action_items: z.boolean().optional(),
  }),

  exportTranscript: z.object({
    transcript_id: commonSchemas.transcriptId,
    format: commonSchemas.exportFormat,
    include_timestamps: z.boolean().optional(),
    include_speaker_labels: z.boolean().optional(),
  }),

  searchMeetings: z.object({
    query: commonSchemas.searchQuery,
    limit: commonSchemas.limit.optional(),
    filters: z
      .object({
        start_date: commonSchemas.dateString.optional(),
        end_date: commonSchemas.dateString.optional(),
        user_id: commonSchemas.userId.optional(),
        meeting_title: commonSchemas.title.optional(),
      })
      .optional(),
  }),

  getMeetingSummary: z.object({
    transcript_id: commonSchemas.transcriptId,
    summary_type: commonSchemas.summaryType,
    include_timestamps: z.boolean().optional(),
  }),
};

/**
 * Validate tool arguments using Zod schema
 */
export function validateToolArguments<T>(schema: z.ZodSchema<T>, args: unknown): T {
  try {
    return schema.parse(args);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const firstError = error.errors[0];
      throw new FirefliesValidationError(
        `Validation error: ${firstError.message}`,
        firstError.path.join('.'),
      );
    }
    throw error;
  }
}

/**
 * Environment variable validation
 */
export const envSchema = z.object({
  FIREFLIES_API_KEY: z.string().min(1, 'FIREFLIES_API_KEY is required'),
  FIREFLIES_API_URL: z.string().url().optional(),
  PORT: z.string().optional(),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).optional(),
});

/**
 * Validate environment variables
 */
export function validateEnvironment() {
  try {
    return envSchema.parse(process.env);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const missingVars = error.errors.map((err) => err.path.join('.')).join(', ');
      throw new FirefliesValidationError(
        `Missing or invalid environment variables: ${missingVars}`,
      );
    }
    throw error;
  }
}
