import { AsyncLocalStorage } from 'async_hooks';
import { Request } from 'express';

export const asyncLocalStorage = new AsyncLocalStorage<{ accessToken: string; authData?: any; apiKey?: string }>();

export function extractAuthData(req: Request): { authToken: string; authData: any; apiKey: string } {
  let authDataStr = process.env.AUTH_DATA;

  if (!authDataStr && req.headers['x-auth-data']) {
    try {
      authDataStr = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data header:', error);
    }
  }

  if (!authDataStr) {
    return { authToken: '', authData: null, apiKey: process.env.YOUTUBE_API_KEY || '' };
  }

  try {
    const authData = JSON.parse(authDataStr);
    return {
      authToken: authData.access_token ?? '',
      authData,
      apiKey: authData.api_key ?? process.env.YOUTUBE_API_KEY ?? '',
    };
  } catch {
    // If it's not JSON, treat the decoded string as the API key directly
    return { authToken: '', authData: null, apiKey: authDataStr };
  }
}

export function getAccessToken(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.accessToken) return store.accessToken;
  // Fallback to env var (for stdio / local testing)
  return process.env.ACCESS_TOKEN || '';
}

export function getApiKey(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.apiKey) return store.apiKey;
  // Fallback to env var (for stdio / local testing)
  return process.env.YOUTUBE_API_KEY || '';
}

export function getAuthData(): any {
  const store = asyncLocalStorage.getStore();
  if (store?.authData) return store.authData;
  // Fallback to env var (for stdio / local testing)
  const authDataStr = process.env.AUTH_DATA;
  if (authDataStr) {
    try {
      return JSON.parse(authDataStr);
    } catch {
      return null;
    }
  }
  return null;
}
