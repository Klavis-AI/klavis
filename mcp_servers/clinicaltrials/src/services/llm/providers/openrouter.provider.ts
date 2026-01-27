/**
 * @fileoverview Provides a service class (`OpenRouterProvider`) for interacting with the
 * OpenRouter API. This class is designed to be managed by a dependency injection
 * container, receiving its dependencies via constructor injection.
 * @module src/services/llm/providers/openrouter.provider
 */
import OpenAI from 'openai';
import {
  type ChatCompletion,
  type ChatCompletionChunk,
} from 'openai/resources/chat/completions';
import { Stream } from 'openai/streaming';
import { inject, injectable } from 'tsyringe';

import { config as ConfigType } from '@/config/index.js';
import { AppConfig, Logger, RateLimiterService } from '@/container/index.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { ErrorHandler } from '@/utils/internal/error-handler/index.js';
import { logger as LoggerType } from '@/utils/internal/logger.js';
import {
  type RequestContext,
  requestContextService,
} from '@/utils/internal/requestContext.js';
import { RateLimiter } from '@/utils/security/rateLimiter.js';
import { sanitization } from '@/utils/security/sanitization.js';
import type {
  ILlmProvider,
  OpenRouterChatParams,
} from '@/services/llm/core/ILlmProvider.js';

export interface OpenRouterClientOptions {
  apiKey: string;
  baseURL?: string;
  siteUrl?: string;
  siteName?: string;
}

@injectable()
export class OpenRouterProvider implements ILlmProvider {
  private readonly client: OpenAI;
  private readonly defaultParams: {
    model: string;
    temperature: number | undefined;
    topP: number | undefined;
    maxTokens: number | undefined;
    topK: number | undefined;
    minP: number | undefined;
  };

  constructor(
    @inject(RateLimiterService) private rateLimiter: RateLimiter,
    @inject(AppConfig) private config: typeof ConfigType,
    @inject(Logger) private logger: typeof LoggerType,
  ) {
    const context = requestContextService.createRequestContext({
      operation: 'OpenRouterProvider.constructor',
    });

    if (!this.config.openrouterApiKey) {
      this.logger.fatal(
        'OpenRouter API key is not configured. Please set OPENROUTER_API_KEY.',
        context,
      );
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'OpenRouter API key is not configured.',
        context,
      );
    }

    try {
      const options: OpenRouterClientOptions = {
        apiKey: this.config.openrouterApiKey,
        siteUrl: this.config.openrouterAppUrl,
        siteName: this.config.openrouterAppName,
      };

      this.client = new OpenAI({
        baseURL: options.baseURL || 'https://openrouter.ai/api/v1',
        apiKey: options.apiKey,
        defaultHeaders: {
          'HTTP-Referer': options.siteUrl,
          'X-Title': options.siteName,
        },
        maxRetries: 0,
      });

      this.defaultParams = {
        model: this.config.llmDefaultModel,
        temperature: this.config.llmDefaultTemperature,
        topP: this.config.llmDefaultTopP,
        maxTokens: this.config.llmDefaultMaxTokens,
        topK: this.config.llmDefaultTopK,
        minP: this.config.llmDefaultMinP,
      };

      this.logger.info(
        'OpenRouter provider instance created and ready.',
        context,
      );
    } catch (e: unknown) {
      const error = e as Error;
      this.logger.error('Failed to construct OpenRouter client', {
        ...context,
        error: error.message,
      });
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'Failed to construct OpenRouter client. Please check the configuration.',
        { cause: error },
      );
    }
  }

  // --- PRIVATE METHODS ---

  private _prepareApiParameters(params: OpenRouterChatParams) {
    const {
      model,
      temperature,
      top_p: topP,
      max_tokens: maxTokens,
      stream,
      ...rest
    } = params;

    return {
      ...rest,
      model: model || this.defaultParams.model,
      temperature:
        temperature === null
          ? undefined
          : (temperature ?? this.defaultParams.temperature),
      top_p: topP === null ? undefined : (topP ?? this.defaultParams.topP),
      max_tokens:
        maxTokens === null
          ? undefined
          : (maxTokens ?? this.defaultParams.maxTokens),
      ...(typeof stream === 'boolean' && { stream }),
    };
  }

  private async _openRouterChatCompletionLogic(
    client: OpenAI,
    params: OpenRouterChatParams,
    context: RequestContext,
  ): Promise<ChatCompletion | Stream<ChatCompletionChunk>> {
    this.logger.logInteraction('OpenRouterRequest', {
      context,
      request: params,
    });
    if (params.stream) {
      return client.chat.completions.create(params);
    } else {
      const response = await client.chat.completions.create(params);

      this.logger.logInteraction('OpenRouterResponse', {
        context,
        response,
      });
      return response;
    }
  }

  // --- PUBLIC METHODS (from ILlmProvider interface) ---

  public async chatCompletion(
    params: OpenRouterChatParams,
    context: RequestContext,
  ): Promise<ChatCompletion | Stream<ChatCompletionChunk>> {
    const operation = 'OpenRouterProvider.chatCompletion';
    const sanitizedParams = sanitization.sanitizeForLogging(params);

    return await ErrorHandler.tryCatch(
      async () => {
        const rateLimitKey = context.requestId || 'openrouter_default_key';
        this.rateLimiter.check(rateLimitKey, context);
        const finalApiParams = this._prepareApiParameters(
          params,
        ) as OpenRouterChatParams;
        return await this._openRouterChatCompletionLogic(
          this.client,
          finalApiParams,
          context,
        );
      },
      { operation, context, input: sanitizedParams },
    );
  }

  public async chatCompletionStream(
    params: OpenRouterChatParams,
    context: RequestContext,
  ): Promise<AsyncIterable<ChatCompletionChunk>> {
    const streamParams = { ...params, stream: true };
    const responseStream = (await this.chatCompletion(
      streamParams,
      context,
    )) as Stream<ChatCompletionChunk>;

    const loggingStream = async function* (
      this: OpenRouterProvider,
    ): AsyncGenerator<ChatCompletionChunk> {
      const chunks: ChatCompletionChunk[] = [];
      try {
        for await (const chunk of responseStream) {
          chunks.push(chunk);
          yield chunk;
        }
      } finally {
        this.logger.logInteraction('OpenRouterResponse', {
          context,
          response: chunks,
          streaming: true,
        });
      }
    }.bind(this)();

    return loggingStream;
  }
}
