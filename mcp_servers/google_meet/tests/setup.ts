import { jest } from '@jest/globals';

// Mock node-fetch globally
jest.mock('node-fetch');

// Mock dotenv
jest.mock('dotenv', () => ({
  config: jest.fn(),
}));

// Setup global test timeout
jest.setTimeout(10000);

// Global test setup
beforeEach(() => {
  jest.clearAllMocks();
});
