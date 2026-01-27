/**
 * @fileoverview Lightweight, dependency-free token counters with model-configurable heuristics.
 * This avoids native/WASM dependencies (e.g., tiktoken) while providing a stable extension point
 * to adjust per-model tokenization and overhead later.
 * @module src/utils/metrics/tokenCounter
 */
import { JsonRpcErrorCode } from '@/types-global/errors.js';
import { ErrorHandler, type RequestContext, logger } from '@/utils/index.js';

/** Minimal chat message shape to stay provider-agnostic. */
export type ChatMessage = {
  role: string;
  content:
    | string
    | Array<{ type: string; text?: string; [k: string]: unknown }>
    | null;
  name?: string;
  tool_calls?: Array<{
    id?: string;
    type?: string;
    function?: { name?: string; arguments?: string };
  }> | null;
  tool_call_id?: string | null;
};

/** Heuristic model schema. Extend as needed per model. */
export interface ModelHeuristics {
  charsPerToken: number; // average chars per token; ~4 for English
  tokensPerMessage: number; // message overhead
  tokensPerName: number; // extra if name present
  replyPrimer: number; // priming tokens for assistant reply
}

const DEFAULT_MODEL = 'gpt-4o';

// Known heuristics; tweak as you calibrate
const HEURISTICS: Record<string, ModelHeuristics> = {
  'gpt-4o': {
    charsPerToken: 4,
    tokensPerMessage: 3,
    tokensPerName: 1,
    replyPrimer: 3,
  },
  'gpt-4o-mini': {
    charsPerToken: 4,
    tokensPerMessage: 3,
    tokensPerName: 1,
    replyPrimer: 3,
  },
  default: {
    charsPerToken: 4,
    tokensPerMessage: 3,
    tokensPerName: 1,
    replyPrimer: 3,
  },
};

function getModelHeuristics(model?: string): ModelHeuristics {
  const key = (model ?? DEFAULT_MODEL).toLowerCase();
  const found = HEURISTICS[key];
  return (found ?? HEURISTICS.default) as ModelHeuristics;
}

function nonEmptyString(s: unknown): s is string {
  return typeof s === 'string' && s.length > 0;
}

function approxTokenCount(text: string, charsPerToken: number): number {
  if (!text) return 0;
  const normalized = text.replace(/\s+/g, ' ').trim();
  if (!normalized) return 0;
  return Math.ceil(normalized.length / Math.max(1, charsPerToken));
}

export async function countTokens(
  text: string,
  context?: RequestContext,
  model?: string,
): Promise<number> {
  return ErrorHandler.tryCatch(
    () => {
      const h: ModelHeuristics = getModelHeuristics(model);
      return approxTokenCount(text ?? '', h.charsPerToken);
    },
    {
      operation: 'countTokens',
      ...(context && { context }),
      input: {
        textSample: nonEmptyString(text)
          ? text.length > 53
            ? `${text.slice(0, 50)}...`
            : text
          : '',
      },
      errorCode: JsonRpcErrorCode.InternalError,
    },
  );
}

export async function countChatTokens(
  messages: ReadonlyArray<ChatMessage>,
  context?: RequestContext,
  model?: string,
): Promise<number> {
  return ErrorHandler.tryCatch(
    () => {
      const h: ModelHeuristics = getModelHeuristics(model);
      let tokens = 0;

      for (const message of messages) {
        tokens += h.tokensPerMessage;

        // role contribution (very small; approximate as 1)
        tokens += 1;

        // content
        if (typeof message.content === 'string') {
          tokens += approxTokenCount(message.content, h.charsPerToken);
        } else if (Array.isArray(message.content)) {
          for (const part of message.content) {
            if (part && part.type === 'text' && nonEmptyString(part.text)) {
              tokens += approxTokenCount(part.text, h.charsPerToken);
            } else if (part) {
              logger.warning(
                `Non-text content part found (type: ${String(part.type)}), token count contribution ignored.`,
                context,
              );
            }
          }
        }

        // optional name
        if (message.name) {
          tokens += h.tokensPerName;
          tokens += approxTokenCount(message.name, h.charsPerToken);
        }

        // assistant tool calls
        if (message.role === 'assistant' && Array.isArray(message.tool_calls)) {
          for (const toolCall of message.tool_calls) {
            if (toolCall?.type === 'function') {
              if (toolCall.function?.name) {
                tokens += approxTokenCount(
                  toolCall.function.name,
                  h.charsPerToken,
                );
              }
              if (toolCall.function?.arguments) {
                tokens += approxTokenCount(
                  toolCall.function.arguments,
                  h.charsPerToken,
                );
              }
            }
          }
        }

        // tool message id
        if (message.role === 'tool' && message.tool_call_id) {
          tokens += approxTokenCount(message.tool_call_id, h.charsPerToken);
        }
      }

      tokens += h.replyPrimer;
      return tokens;
    },
    {
      operation: 'countChatTokens',
      ...(context && { context }),
      input: { messageCount: messages.length },
      errorCode: JsonRpcErrorCode.InternalError,
    },
  );
}
// Intentionally no generic helpers; the return above asserts to satisfy
// TypeScript with noUncheckedIndexedAccess while remaining safe at runtime.
