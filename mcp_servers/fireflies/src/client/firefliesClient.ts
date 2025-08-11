import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { AsyncLocalStorage } from 'async_hooks';
import { GraphQLClient } from 'graphql-request';
import dotenv from 'dotenv';

dotenv.config();

const FIREFLIES_API_URL = 'https://api.fireflies.ai/graphql';

const asyncLocalStorage = new AsyncLocalStorage<{
  firefliesClient: FirefliesClient;
}>();

let mcpServerInstance: Server | null = null;

export class FirefliesClient {
  private accessToken: string;
  private graphqlClient: GraphQLClient;
  private baseUrl: string;

  constructor(accessToken: string, baseUrl: string = FIREFLIES_API_URL) {
    this.accessToken = accessToken;
    this.baseUrl = baseUrl;

    this.graphqlClient = new GraphQLClient(this.baseUrl, {
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Execute a GraphQL query
   */
  public async query<T = any>(query: string, variables?: Record<string, any>): Promise<T> {
    try {
      const result = await this.graphqlClient.request<T>(query, variables);
      return result;
    } catch (error) {
      throw new Error(
        `Fireflies API error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
    }
  }

  /**
   * Execute a GraphQL mutation
   */
  public async mutate<T = any>(mutation: string, variables?: Record<string, any>): Promise<T> {
    try {
      const result = await this.graphqlClient.request<T>(mutation, variables);
      return result;
    } catch (error) {
      throw new Error(
        `Fireflies API mutation error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
    }
  }

  /**
   * Make a direct HTTP request (for non-GraphQL endpoints if needed)
   */
  public async makeRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
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
      throw new Error(
        `Fireflies API error: ${response.status} ${response.statusText} - ${errorText}`,
      );
    }

    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return response.json();
    } else if (contentType?.includes('text/')) {
      return response.text();
    } else {
      return response.blob();
    }
  }

  /**
   * Test the API connection
   */
  public async testConnection(): Promise<boolean> {
    try {
      const testQuery = `
        query {
          user {
            user_id
            email
          }
        }
      `;
      await this.query(testQuery);
      return true;
    } catch (error) {
      safeLog('error', `Failed to connect to Fireflies API: ${error}`);
      return false;
    }
  }
}

function getFirefliesClient(): FirefliesClient {
  const store = asyncLocalStorage.getStore();
  if (!store || !store.firefliesClient) {
    throw new Error('Store not found in AsyncLocalStorage');
  }
  if (!store.firefliesClient) {
    throw new Error('Fireflies client not found in AsyncLocalStorage');
  }
  return store.firefliesClient;
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

export { getFirefliesClient, safeLog, asyncLocalStorage, mcpServerInstance };
