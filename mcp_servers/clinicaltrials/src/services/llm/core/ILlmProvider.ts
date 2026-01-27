/**
 * @fileoverview Defines the interface for a generic Large Language Model (LLM) provider.
 * This contract ensures that any LLM service implementation can be used interchangeably.
 * @module src/services/llm-providers/ILlmProvider
 */
import type {
  ChatCompletion,
  ChatCompletionChunk,
  ChatCompletionCreateParamsNonStreaming,
  ChatCompletionCreateParamsStreaming,
} from 'openai/resources/chat/completions';
import type { Stream } from 'openai/streaming';

import type { RequestContext } from '@/utils/index.js';

export type OpenRouterChatParams =
  | ChatCompletionCreateParamsNonStreaming
  | ChatCompletionCreateParamsStreaming;

export interface ILlmProvider {
  /**
   * Creates a chat completion. Can be streaming or non-streaming.
   * @param params - The parameters for the chat completion request.
   * @param context - The request context for logging and tracing.
   * @returns A promise that resolves to a ChatCompletion or a Stream of ChatCompletionChunks.
   */
  chatCompletion(
    params: OpenRouterChatParams, // We can generalize this type later if needed
    context: RequestContext,
  ): Promise<ChatCompletion | Stream<ChatCompletionChunk>>;

  /**
   * Creates a streaming chat completion.
   * @param params - The parameters for the chat completion request.
   * @param context - The request context for logging and tracing.
   * @returns A promise that resolves to an async iterable of ChatCompletionChunks.
   */
  chatCompletionStream(
    params: OpenRouterChatParams,
    context: RequestContext,
  ): Promise<AsyncIterable<ChatCompletionChunk>>;
}
