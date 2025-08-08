import { describe, it, expect } from '@jest/globals';
import { z } from 'zod';

// Import schemas - we'll need to export them from index.ts
// For now, let's recreate them in the test file
const GetMeetingDetailsSchema = z.object({
  space_id: z.string()
    .min(1, 'Space ID cannot be empty')
    .max(1000, 'Space ID is too long')
    .regex(/^spaces\/[a-zA-Z0-9\-_]+$/, 'Invalid space ID format. Must be in format: spaces/{space-id}')
    .describe('Meeting space ID (spaces/{space-id})'),
});

const GetPastMeetingsSchema = z.object({
  page_size: z.number()
    .int('Page size must be an integer')
    .positive('Page size must be positive')
    .max(100, 'Page size cannot exceed 100')
    .optional()
    .default(10)
    .describe('Maximum number of records to return'),
  page_token: z.string()
    .max(5000, 'Page token is too long')
    .optional()
    .describe('Token for pagination'),
  filter: z.string()
    .max(2000, 'Filter expression is too long')
    .optional()
    .describe('Filter expression'),
});

const GetPastMeetingDetailsSchema = z.object({
  conference_record_id: z.string()
    .min(1, 'Conference record ID cannot be empty')
    .max(1000, 'Conference record ID is too long')
    .regex(/^conferenceRecords\/[a-zA-Z0-9\-_]+$/, 'Invalid conference record ID format. Must be in format: conferenceRecords/{record-id}')
    .describe('Conference record ID (conferenceRecords/{record-id})'),
});

const GetPastMeetingParticipantsSchema = z.object({
  conference_record_id: z.string()
    .min(1, 'Conference record ID cannot be empty')
    .max(1000, 'Conference record ID is too long')
    .regex(/^conferenceRecords\/[a-zA-Z0-9\-_]+$/, 'Invalid conference record ID format. Must be in format: conferenceRecords/{record-id}')
    .describe('Conference record ID (conferenceRecords/{record-id})'),
  page_size: z.number()
    .int('Page size must be an integer')
    .positive('Page size must be positive')
    .max(100, 'Page size cannot exceed 100')
    .optional()
    .default(10)
    .describe('Maximum number of participants to return'),
  page_token: z.string()
    .max(5000, 'Page token is too long')
    .optional()
    .describe('Token for pagination'),
  filter: z.string()
    .max(2000, 'Filter expression is too long')
    .optional()
    .describe('Filter expression'),
});

describe('Schema Validation Tests', () => {
  describe('GetMeetingDetailsSchema', () => {
    it('should validate correct space_id', () => {
      const validData = { space_id: 'spaces/test-space-123' };
      expect(() => GetMeetingDetailsSchema.parse(validData)).not.toThrow();
    });

    it('should reject empty space_id', () => {
      const invalidData = { space_id: '' };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Space ID cannot be empty');
    });

    it('should reject space_id that is too long', () => {
      const invalidData = { space_id: 'spaces/' + 'a'.repeat(1000) };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Space ID is too long');
    });

    it('should reject invalid space_id format', () => {
      const invalidData = { space_id: 'invalid-format' };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid space ID format');
    });

    it('should handle space_id with special characters', () => {
      const validData = { space_id: 'spaces/test-space_123-456' };
      expect(() => GetMeetingDetailsSchema.parse(validData)).not.toThrow();
    });

    it('should reject space_id with emojis', () => {
      const invalidData = { space_id: 'spaces/test-🚀-space' };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid space ID format');
    });

    it('should reject space_id with whitespace', () => {
      const invalidData = { space_id: 'spaces/test space' };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid space ID format');
    });

    it('should reject space_id with special characters not allowed', () => {
      const invalidData = { space_id: 'spaces/test@space#123' };
      expect(() => GetMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid space ID format');
    });
  });

  describe('GetPastMeetingsSchema', () => {
    it('should validate with default page_size', () => {
      const validData = {};
      const result = GetPastMeetingsSchema.parse(validData);
      expect(result.page_size).toBe(10);
    });

    it('should validate with custom page_size', () => {
      const validData = { page_size: 25 };
      const result = GetPastMeetingsSchema.parse(validData);
      expect(result.page_size).toBe(25);
    });

    it('should reject negative page_size', () => {
      const invalidData = { page_size: -1 };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Page size must be positive');
    });

    it('should reject zero page_size', () => {
      const invalidData = { page_size: 0 };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Page size must be positive');
    });

    it('should reject page_size over 100', () => {
      const invalidData = { page_size: 101 };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Page size cannot exceed 100');
    });

    it('should reject non-integer page_size', () => {
      const invalidData = { page_size: 10.5 };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Page size must be an integer');
    });

    it('should validate with page_token', () => {
      const validData = { page_token: 'valid-token-123' };
      expect(() => GetPastMeetingsSchema.parse(validData)).not.toThrow();
    });

    it('should reject page_token that is too long', () => {
      const invalidData = { page_token: 'a'.repeat(5001) };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Page token is too long');
    });

    it('should validate with filter', () => {
      const validData = { filter: 'startTime>"2024-01-01T00:00:00Z"' };
      expect(() => GetPastMeetingsSchema.parse(validData)).not.toThrow();
    });

    it('should reject filter that is too long', () => {
      const invalidData = { filter: 'a'.repeat(2001) };
      expect(() => GetPastMeetingsSchema.parse(invalidData)).toThrow('Filter expression is too long');
    });

    it('should handle empty strings for optional fields', () => {
      const validData = { page_token: '', filter: '' };
      expect(() => GetPastMeetingsSchema.parse(validData)).not.toThrow();
    });

    it('should handle unicode characters in filter', () => {
      const validData = { filter: 'name contains "测试会议"' };
      expect(() => GetPastMeetingsSchema.parse(validData)).not.toThrow();
    });

    it('should handle emojis in filter', () => {
      const validData = { filter: 'name contains "Meeting 🚀"' };
      expect(() => GetPastMeetingsSchema.parse(validData)).not.toThrow();
    });
  });

  describe('GetPastMeetingDetailsSchema', () => {
    it('should validate correct conference_record_id', () => {
      const validData = { conference_record_id: 'conferenceRecords/test-record-123' };
      expect(() => GetPastMeetingDetailsSchema.parse(validData)).not.toThrow();
    });

    it('should reject empty conference_record_id', () => {
      const invalidData = { conference_record_id: '' };
      expect(() => GetPastMeetingDetailsSchema.parse(invalidData)).toThrow('Conference record ID cannot be empty');
    });

    it('should reject conference_record_id that is too long', () => {
      const invalidData = { conference_record_id: 'conferenceRecords/' + 'a'.repeat(1000) };
      expect(() => GetPastMeetingDetailsSchema.parse(invalidData)).toThrow('Conference record ID is too long');
    });

    it('should reject invalid conference_record_id format', () => {
      const invalidData = { conference_record_id: 'invalid-format' };
      expect(() => GetPastMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid conference record ID format');
    });

    it('should handle conference_record_id with special characters', () => {
      const validData = { conference_record_id: 'conferenceRecords/test-record_123-456' };
      expect(() => GetPastMeetingDetailsSchema.parse(validData)).not.toThrow();
    });

    it('should reject conference_record_id with emojis', () => {
      const invalidData = { conference_record_id: 'conferenceRecords/test-🚀-record' };
      expect(() => GetPastMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid conference record ID format');
    });

    it('should reject conference_record_id with whitespace', () => {
      const invalidData = { conference_record_id: 'conferenceRecords/test record' };
      expect(() => GetPastMeetingDetailsSchema.parse(invalidData)).toThrow('Invalid conference record ID format');
    });
  });

  describe('GetPastMeetingParticipantsSchema', () => {
    it('should validate all fields together', () => {
      const validData = {
        conference_record_id: 'conferenceRecords/test-record-123',
        page_size: 50,
        page_token: 'token-123',
        filter: 'earliestStartTime>"2024-01-01T00:00:00Z"'
      };
      expect(() => GetPastMeetingParticipantsSchema.parse(validData)).not.toThrow();
    });

    it('should validate with minimal required fields', () => {
      const validData = { conference_record_id: 'conferenceRecords/test-record-123' };
      const result = GetPastMeetingParticipantsSchema.parse(validData);
      expect(result.page_size).toBe(10);
    });

    it('should handle edge case values', () => {
      const validData = {
        conference_record_id: 'conferenceRecords/a',
        page_size: 1,
        page_token: 'a',
        filter: 'a'
      };
      expect(() => GetPastMeetingParticipantsSchema.parse(validData)).not.toThrow();
    });

    it('should handle maximum valid values', () => {
      const validData = {
        conference_record_id: 'conferenceRecords/' + 'a'.repeat(982), // 1000 - 'conferenceRecords/'.length (18 chars)
        page_size: 100,
        page_token: 'a'.repeat(5000),
        filter: 'a'.repeat(2000)
      };
      expect(() => GetPastMeetingParticipantsSchema.parse(validData)).not.toThrow();
    });
  });
});
