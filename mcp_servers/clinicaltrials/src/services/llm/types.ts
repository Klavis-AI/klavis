/**
 * @fileoverview Type definitions for the LLM service.
 * Provides shared types and interfaces for LLM operations.
 * @module src/services/llm/types
 */

/**
 * Re-export OpenRouter-specific types from the interface.
 * This keeps types centralized while allowing provider-specific extensions.
 */
export type { OpenRouterChatParams } from './core/ILlmProvider.js';
