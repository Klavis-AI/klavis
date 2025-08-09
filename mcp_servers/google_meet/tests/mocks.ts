import { jest } from '@jest/globals';
import { Response } from 'node-fetch';

// Mock fetch response helper
export const createMockResponse = (data: any, status: number = 200, ok: boolean = true): Partial<Response> => ({
  ok,
  status,
  statusText: ok ? 'OK' : 'Error',
  text: jest.fn().mockResolvedValue(JSON.stringify(data)),
  json: jest.fn().mockResolvedValue(data),
  headers: {} as any,
  redirected: false,
  type: 'basic' as any,
  url: '',
  clone: jest.fn(),
  body: null,
  bodyUsed: false,
  arrayBuffer: jest.fn(),
  blob: jest.fn(),
  buffer: jest.fn(),
  textConverted: jest.fn(),
});

// Mock Google Meet API responses
export const mockMeetingSpace = {
  name: 'spaces/test-space-id-123',
  meetingUri: 'https://meet.google.com/abc-defg-hij',
  meetingCode: 'abc-defg-hij',
  config: {
    accessType: 'OPEN',
    entryPointAccess: 'ALL',
  },
};

export const mockConferenceRecord = {
  name: 'conferenceRecords/test-record-123',
  startTime: '2024-01-15T10:00:00Z',
  endTime: '2024-01-15T11:00:00Z',
  expireTime: '2024-01-22T10:00:00Z',
  space: 'spaces/test-space-id-123',
};

export const mockParticipant = {
  name: 'conferenceRecords/test-record-123/participants/test-participant-123',
  earliestStartTime: '2024-01-15T10:05:00Z',
  latestEndTime: '2024-01-15T10:55:00Z',
};

export const mockConferenceRecords = {
  conferenceRecords: [mockConferenceRecord],
  nextPageToken: 'next-page-token-123',
};

export const mockParticipants = {
  participants: [mockParticipant],
  nextPageToken: 'next-participants-token-123',
};
