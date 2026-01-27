/**
 * @fileoverview Speech service orchestrator.
 * Manages multiple speech providers for TTS and STT operations.
 * @module src/services/speech/core/SpeechService
 */

import { McpError, JsonRpcErrorCode } from '@/types-global/errors.js';
import { logger } from '@/utils/index.js';

import { ElevenLabsProvider } from '../providers/elevenlabs.provider.js';
import { WhisperProvider } from '../providers/whisper.provider.js';
import type { ISpeechProvider } from './ISpeechProvider.js';
import type { SpeechProviderConfig } from '../types.js';

/**
 * Factory function to create speech provider instances.
 */
export function createSpeechProvider(
  config: SpeechProviderConfig,
): ISpeechProvider {
  logger.debug(`Creating speech provider: ${config.provider}`);

  switch (config.provider) {
    case 'elevenlabs':
      return new ElevenLabsProvider(config);

    case 'openai-whisper':
      return new WhisperProvider(config);

    case 'mock':
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'Mock provider not yet implemented',
      );

    default: {
      const _exhaustive: never = config.provider;
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        `Unknown speech provider: ${String(_exhaustive)}`,
      );
    }
  }
}

/**
 * Main speech service that manages multiple providers.
 * Allows using different providers for TTS and STT.
 */
export class SpeechService {
  private ttsProvider?: ISpeechProvider;
  private sttProvider?: ISpeechProvider;

  constructor(
    ttsConfig?: SpeechProviderConfig,
    sttConfig?: SpeechProviderConfig,
  ) {
    if (ttsConfig) {
      this.ttsProvider = createSpeechProvider(ttsConfig);
      if (!this.ttsProvider.supportsTTS) {
        logger.warning(
          `TTS provider ${ttsConfig.provider} does not support text-to-speech`,
        );
      }
    }

    if (sttConfig) {
      this.sttProvider = createSpeechProvider(sttConfig);
      if (!this.sttProvider.supportsSTT) {
        logger.warning(
          `STT provider ${sttConfig.provider} does not support speech-to-text`,
        );
      }
    }

    logger.info(
      `Speech service initialized: TTS=${this.ttsProvider?.name ?? 'none'}, STT=${this.sttProvider?.name ?? 'none'}`,
    );
  }

  /**
   * Get the TTS provider.
   */
  getTTSProvider(): ISpeechProvider {
    if (!this.ttsProvider) {
      throw new McpError(
        JsonRpcErrorCode.InvalidRequest,
        'No TTS provider configured',
      );
    }
    return this.ttsProvider;
  }

  /**
   * Get the STT provider.
   */
  getSTTProvider(): ISpeechProvider {
    if (!this.sttProvider) {
      throw new McpError(
        JsonRpcErrorCode.InvalidRequest,
        'No STT provider configured',
      );
    }
    return this.sttProvider;
  }

  /**
   * Check if TTS is available.
   */
  hasTTS(): boolean {
    return this.ttsProvider?.supportsTTS ?? false;
  }

  /**
   * Check if STT is available.
   */
  hasSTT(): boolean {
    return this.sttProvider?.supportsSTT ?? false;
  }

  /**
   * Health check for all configured providers.
   */
  async healthCheck(): Promise<{
    tts: boolean;
    stt: boolean;
  }> {
    const ttsHealth = this.ttsProvider
      ? await this.ttsProvider.healthCheck()
      : false;
    const sttHealth = this.sttProvider
      ? await this.sttProvider.healthCheck()
      : false;

    return {
      tts: ttsHealth,
      stt: sttHealth,
    };
  }
}
