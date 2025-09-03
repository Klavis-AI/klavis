import { beforeAll } from 'vitest';
import { config } from 'dotenv';

beforeAll(() => {
  // Load environment variables from .env file
  config();
  
  // Setup global test environment
  process.env.NODE_ENV = 'test';
  
  // Ensure API token is available for tests
  if (!process.env.VERCEL_API_TOKEN) {
    console.warn('⚠️ VERCEL_API_TOKEN not found in environment variables');
    console.warn('Make sure you have a .env file with VERCEL_API_TOKEN set');
  }
});
