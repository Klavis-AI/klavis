import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

dotenv.config();

const INTERCOM_API_URL = 'https://api.intercom.io';

const asyncLocalStorage = new AsyncLocalStorage<{
  intercomClient: IntercomClient;
}>();

let mcpServerInstance: Server | null = null;

export class IntercomClient {
  private accessToken: string;
  private baseUrl: string;

  constructor(accessToken: string, baseUrl: string = INTERCOM_API_URL) {
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
  }

  public async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'Intercom-Version': '2.11',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Intercom API error: ${response.status} ${response.statusText} - ${errorText}`,
      );
    }

    return response.json();
  }
}

function getIntercomClient() {
  const store = asyncLocalStorage.getStore();
  if (!store || !store.intercomClient) {
    throw new Error('Store not found in AsyncLocalStorage');
  }
  if (!store.intercomClient) {
    throw new Error('Intercom client not found in AsyncLocalStorage');
  }
  return store.intercomClient;
}

function safeLog(
  level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency',
  data: any,
): void {
  try {
    const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
    console.log(`[${level.toUpperCase()}] ${logData}`);
  } catch (error) {
    console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
  }
}

export { getIntercomClient, safeLog, asyncLocalStorage, mcpServerInstance };
