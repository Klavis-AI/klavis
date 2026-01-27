/**
 * @fileoverview Registers core application services with the DI container.
 * This module encapsulates the registration of fundamental services such as
 * configuration, logging, storage, and the LLM provider.
 * @module src/container/registrations/core
 */
import { container, Lifecycle } from 'tsyringe';

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

import { parseConfig } from '@/config/index.js';
import {
  AppConfig,
  ClinicalTrialsProvider,
  LlmProvider,
  Logger,
  RateLimiterService,
  SpeechService,
  StorageService,
  StorageProvider,
  SupabaseAdminClient,
} from '@/container/tokens.js';
import type { IClinicalTrialsProvider } from '@/services/clinical-trials-gov/core/IClinicalTrialsProvider.js';
import { ClinicalTrialsGovProvider } from '@/services/clinical-trials-gov/providers/clinicaltrials-gov.provider.js';
import type { ILlmProvider } from '@/services/llm/core/ILlmProvider.js';
import { OpenRouterProvider } from '@/services/llm/providers/openrouter.provider.js';
import { SpeechService as SpeechServiceClass } from '@/services/speech/index.js';
import { StorageService as StorageServiceClass } from '@/storage/core/StorageService.js';
import { createStorageProvider } from '@/storage/core/storageFactory.js';
import type { Database } from '@/storage/providers/supabase/supabase.types.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger } from '@/utils/index.js';
import { RateLimiter } from '@/utils/security/rateLimiter.js';

/**
 * Registers core application services and values with the tsyringe container.
 */
export const registerCoreServices = () => {
  // Configuration (parsed and registered as a static value)
  const config = parseConfig();
  container.register(AppConfig, { useValue: config });

  // Logger (as a static value)
  container.register(Logger, { useValue: logger });

  type AppConfigType = ReturnType<typeof parseConfig>;

  container.register<SupabaseClient<Database>>(SupabaseAdminClient, {
    useFactory: (c) => {
      const cfg = c.resolve<AppConfigType>(AppConfig);
      if (!cfg.supabase?.url || !cfg.supabase?.serviceRoleKey) {
        throw new McpError(
          JsonRpcErrorCode.ConfigurationError,
          'Supabase URL or service role key is missing for admin client.',
        );
      }
      return createClient<Database>(
        cfg.supabase.url,
        cfg.supabase.serviceRoleKey,
        {
          auth: { persistSession: false, autoRefreshToken: false },
        },
      );
    },
  });

  // --- Refactored Storage Service Registration ---
  // 1. Register the factory for the concrete provider against the provider token.
  // This factory depends on the AppConfig, which is already registered.
  container.register(StorageProvider, {
    useFactory: (c) => createStorageProvider(c.resolve(AppConfig)),
  });

  // 2. Register StorageServiceClass against the service token.
  //    tsyringe will automatically inject the StorageProvider dependency.
  container.register(
    StorageService,
    { useClass: StorageServiceClass },
    { lifecycle: Lifecycle.Singleton },
  );
  // --- End Refactor ---

  // LLM Provider (register the class against the interface token)
  container.register<ILlmProvider>(LlmProvider, {
    useClass: OpenRouterProvider,
  });

  // ClinicalTrials.gov Provider
  container.register<IClinicalTrialsProvider>(ClinicalTrialsProvider, {
    useClass: ClinicalTrialsGovProvider,
  });

  // Register RateLimiter as a singleton service
  container.register<RateLimiter>(
    RateLimiterService,
    { useClass: RateLimiter },
    { lifecycle: Lifecycle.Singleton },
  );

  // Register SpeechService with factory for configuration-based setup
  container.register<SpeechServiceClass>(SpeechService, {
    useFactory: (c) => {
      const cfg = c.resolve<AppConfigType>(AppConfig);

      // Build TTS config (ElevenLabs)
      const ttsConfig =
        cfg.speech?.tts?.enabled && cfg.speech.tts.apiKey
          ? ({
              provider: 'elevenlabs',
              apiKey: cfg.speech.tts.apiKey,
              ...(cfg.speech.tts.baseUrl && {
                baseUrl: cfg.speech.tts.baseUrl,
              }),
              ...(cfg.speech.tts.defaultVoiceId && {
                defaultVoiceId: cfg.speech.tts.defaultVoiceId,
              }),
              ...(cfg.speech.tts.defaultModelId && {
                defaultModelId: cfg.speech.tts.defaultModelId,
              }),
              ...(cfg.speech.tts.timeout && {
                timeout: cfg.speech.tts.timeout,
              }),
            } as const)
          : undefined;

      // Build STT config (Whisper)
      const sttConfig =
        cfg.speech?.stt?.enabled && cfg.speech.stt.apiKey
          ? ({
              provider: 'openai-whisper',
              apiKey: cfg.speech.stt.apiKey,
              ...(cfg.speech.stt.baseUrl && {
                baseUrl: cfg.speech.stt.baseUrl,
              }),
              ...(cfg.speech.stt.defaultModelId && {
                defaultModelId: cfg.speech.stt.defaultModelId,
              }),
              ...(cfg.speech.stt.timeout && {
                timeout: cfg.speech.stt.timeout,
              }),
            } as const)
          : undefined;

      return new SpeechServiceClass(ttsConfig, sttConfig);
    },
  });

  logger.info('Core services registered with the DI container.');
};
