import { AsyncLocalStorage } from 'async_hooks';
import { Request } from 'express';

export const asyncLocalStorage = new AsyncLocalStorage<{ accessToken: string; authData?: any }>();

export function extractAuthData(req: Request): { authToken: string; authData: any } {
  let authDataStr = process.env.AUTH_DATA;

  if (!authDataStr && req.headers['x-auth-data']) {
    try {
      authDataStr = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data header:', error);
    }
  }

  if (!authDataStr) {
    return { authToken: '', authData: null };
  }

  try {
    const authData = JSON.parse(authDataStr);
    return {
      authToken: authData.access_token ?? '',
      authData,
    };
  } catch (error) {
    console.error('Error parsing auth data JSON:', error);
    return { authToken: '', authData: null };
  }
}

export function getAccessToken(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.accessToken) return store.accessToken;
  // Fallback to env var (for stdio / local testing)
  return process.env.ACCESS_TOKEN || '';
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
