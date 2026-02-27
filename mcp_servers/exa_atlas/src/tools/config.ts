import { z } from "zod";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { AsyncLocalStorage } from 'async_hooks';

export interface ToolRegistry {
  name: string;        // Unique name for the tool
  description: string; // Human-readable description
  schema: z.ZodRawShape;      // Zod schema for tool parameters
  handler: (
    args: { [key: string]: any }, 
    extra: any
  ) => Promise<{
    content: {
      type: "text";
      text: string;
    }[];
    isError?: boolean;
  }>;   // Function to execute when tool is called
  enabled: boolean;    // Whether the tool is enabled by default
}

// Configuration for API
export const API_CONFIG = {
  BASE_URL: 'https://api.exa.ai',
  ENDPOINTS: {
    SEARCH: '/search'
  },
  DEFAULT_NUM_RESULTS: 5,
  DEFAULT_MAX_CHARACTERS: 3000
} as const;

// AsyncLocalStorage for per-request auth context
export const asyncLocalStorage = new AsyncLocalStorage<{ apiKey: string }>();

/**
 * Get the current API key from AsyncLocalStorage (per-request) or environment.
 */
export function getApiKey(): string {
  const store = asyncLocalStorage.getStore();
  if (store?.apiKey) return store.apiKey;
  return process.env.EXA_API_KEY || '';
}

// Tool registry that will be populated by tool modules
export const toolRegistry: Record<string, ToolRegistry> = {}; 
