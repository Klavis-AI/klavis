/**
 * @fileoverview LLM service barrel export.
 * Provides centralized access to LLM providers, interfaces, and types.
 * @module src/services/llm
 */

// Export core interfaces
export type {
  ILlmProvider,
  OpenRouterChatParams,
} from './core/ILlmProvider.js';

// Export provider implementations
export { OpenRouterProvider } from './providers/openrouter.provider.js';

// Export types
export type * from './types.js';
