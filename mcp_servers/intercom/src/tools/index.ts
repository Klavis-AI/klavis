export * from './definitions/index.js';
export * from './handlers/index.js';

import type { IntercomToolName, AllIntercomTools } from './definitions/index.js';
import { createHandlers, type HandlerCollection } from './handlers/index.js';
import { IntercomClient } from '../client/intercomClient.js';

/**
 * Create a complete Intercom tools instance with both handlers and tool definitions
 */
export function createIntercomTools(intercomClient: IntercomClient) {
  const handlers = createHandlers(intercomClient);

  return {
    handlers,
  };
}

export type { IntercomToolName, AllIntercomTools, HandlerCollection };
