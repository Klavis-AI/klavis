import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

dotenv.config();

const MIRO_API_URL = 'https://api.miro.com/v2';

const asyncLocalStorage = new AsyncLocalStorage<{
  miroClient: MiroClient;
}>();

let mcpServerInstance: Server | null = null;

export class MiroClient {
  private accessToken: string;
  private baseUrl: string;

  constructor(accessToken: string, baseUrl: string = MIRO_API_URL) {
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;
  }

  public async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      Authorization: `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Miro API error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }
}

function getMiroClient() {
  const store = asyncLocalStorage.getStore();
  if (!store || !store.miroClient) {
    throw new Error('Store not found in AsyncLocalStorage');
  }
  if (!store.miroClient) {
    throw new Error('Miro client not found in AsyncLocalStorage');
  }
  return store.miroClient;
}

function safeLog(
  level: 'error' | 'debug' | 'info' | 'notice' | 'warning' | 'critical' | 'alert' | 'emergency',
  data: any
): void {
  try {
    const logData = typeof data === 'object' ? JSON.stringify(data, null, 2) : data;
    console.log(`[${level.toUpperCase()}] ${logData}`);
  } catch (error) {
    console.log(`[${level.toUpperCase()}] [LOG_ERROR] Could not serialize log data`);
  }
}

export { getMiroClient, safeLog, asyncLocalStorage, mcpServerInstance };
