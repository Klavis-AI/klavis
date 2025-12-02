export * from './definitions/index.js';
export * from './handlers/index.js';

import type { MiroToolName, AllMiroTools } from './definitions/index.js';
import { createHandlers, type HandlerCollection } from './handlers/index.js';
import { MiroClient } from '../client/miroClient.js';

/**
 * Create a complete Miro tools instance with both handlers and tool definitions
 */
export function createMiroTools(miroClient: MiroClient) {
  const handlers = createHandlers(miroClient);

  return {
    handlers,
  };
}

export type { MiroToolName, AllMiroTools, HandlerCollection };
