import { AsyncLocalStorage } from 'async_hooks';
import { Request } from 'express';

export const asyncLocalStorage = new AsyncLocalStorage<{ apiKey: string }>();

export function extractAuthData(req: Request): { authToken: string; authData?: any } {
  let authDataStr = process.env.AUTH_DATA;

  if (!authDataStr && req.headers['x-auth-data']) {
    try {
      authDataStr = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data header:', error);
    }
  }

  if (!authDataStr) {
    console.error('Error: YouTube API key is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return { authToken: '' };
  }

  try {
    const authData = JSON.parse(authDataStr);
    return {
      authToken: authData.access_token ?? '',
      authData: authData,
    };
  } catch (error) {
    console.error('Error parsing auth data JSON:', error);
    return { authToken: '' };
  }
}

export function getApiKey(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.apiKey) return store.apiKey;
  // Fallback to env var (for stdio / local testing)
  return process.env.YOUTUBE_API_KEY || '';
}
