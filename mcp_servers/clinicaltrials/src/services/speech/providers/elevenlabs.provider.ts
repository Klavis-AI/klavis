/**
 * @fileoverview ElevenLabs text-to-speech provider implementation.
 * @module src/services/speech/providers/elevenlabs
 */

import { injectable } from 'tsyringe';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  fetchWithTimeout,
  logger,
  requestContextService,
} from '@/utils/index.js';

import type { ISpeechProvider } from '../core/ISpeechProvider.js';
import type {
  SpeechProviderConfig,
  SpeechToTextOptions,
  SpeechToTextResult,
  TextToSpeechOptions,
  TextToSpeechResult,
  Voice,
} from '../types.js';

/**
 * ElevenLabs API response for voice list.
 */
interface ElevenLabsVoice {
  voice_id: string;
  name: string;
  description?: string;
  category?: string;
  labels?: Record<string, string>;
  preview_url?: string;
}

interface ElevenLabsVoicesResponse {
  voices: ElevenLabsVoice[];
}

/**
 * ElevenLabs TTS provider.
 * Supports high-quality text-to-speech synthesis with customizable voices.
 */
@injectable()
export class ElevenLabsProvider implements ISpeechProvider {
  public readonly name = 'elevenlabs';
  public readonly supportsTTS = true;
  public readonly supportsSTT = false;

  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly defaultVoiceId: string;
  private readonly defaultModelId: string;
  private readonly timeout: number;

  constructor(config: SpeechProviderConfig) {
    if (!config.apiKey) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'ElevenLabs API key is required',
      );
    }

    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.elevenlabs.io/v1';
    this.defaultVoiceId = config.defaultVoiceId || 'EXAVITQu4vr4xnSDxMaL'; // Default: Bella
    this.defaultModelId = config.defaultModelId || 'eleven_monolingual_v1';
    this.timeout = config.timeout || 30000;

    logger.info(
      `ElevenLabs TTS provider initialized: ${this.baseUrl}, voice=${this.defaultVoiceId}`,
    );
  }

  /**
   * Convert text to speech using ElevenLabs API.
   */
  async textToSpeech(
    options: TextToSpeechOptions,
  ): Promise<TextToSpeechResult> {
    const context = requestContextService.createRequestContext({
      operation: 'elevenlabs-tts',
      ...(options.context || {}),
    });
    const voiceId = options.voice?.voiceId || this.defaultVoiceId;
    const modelId = options.modelId || this.defaultModelId;

    logger.debug('Converting text to speech with ElevenLabs', context);

    if (!options.text || options.text.trim().length === 0) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'Text cannot be empty',
        context,
      );
    }

    if (options.text.length > 5000) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'Text exceeds maximum length of 5000 characters',
        context,
      );
    }

    const url = `${this.baseUrl}/text-to-speech/${voiceId}`;

    // Build voice settings
    const voiceSettings = {
      stability: options.voice?.stability ?? 0.5,
      similarity_boost: options.voice?.similarityBoost ?? 0.75,
      style: options.voice?.style ?? 0.0,
      use_speaker_boost: true,
    };

    const requestBody = {
      text: options.text,
      model_id: modelId,
      voice_settings: voiceSettings,
    };

    try {
      const response = await fetchWithTimeout(url, this.timeout, context, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': this.apiKey,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorText = await response.text();
        logger.error(`ElevenLabs API error: ${response.status}`, context);

        throw new McpError(
          JsonRpcErrorCode.InternalError,
          `ElevenLabs API error: ${response.status} - ${errorText}`,
          context,
        );
      }

      const audioBuffer = Buffer.from(await response.arrayBuffer());

      logger.info(
        `Text-to-speech conversion successful (voice=${voiceId}, ${audioBuffer.length} bytes)`,
        context,
      );

      return {
        audio: audioBuffer,
        format: 'mp3',
        characterCount: options.text.length,
        metadata: {
          voiceId,
          modelId,
          provider: this.name,
        },
      };
    } catch (error) {
      if (error instanceof McpError) {
        throw error;
      }

      logger.error(
        'Failed to convert text to speech',
        error instanceof Error ? error : new Error(String(error)),
        context,
      );

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to convert text to speech: ${error instanceof Error ? error.message : 'Unknown error'}`,
        context,
      );
    }
  }

  /**
   * Speech-to-text is not supported by ElevenLabs.
   */
  speechToText(_options: SpeechToTextOptions): Promise<SpeechToTextResult> {
    throw new McpError(
      JsonRpcErrorCode.MethodNotFound,
      'Speech-to-text is not supported by ElevenLabs provider',
    );
  }

  /**
   * Get available voices from ElevenLabs.
   */
  async getVoices(): Promise<Voice[]> {
    const context = requestContextService.createRequestContext({
      operation: 'elevenlabs-getVoices',
    });
    logger.debug('Fetching available voices from ElevenLabs', context);

    const url = `${this.baseUrl}/voices`;

    try {
      const response = await fetchWithTimeout(url, this.timeout, context, {
        method: 'GET',
        headers: {
          'xi-api-key': this.apiKey,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        logger.error(`Failed to fetch voices: ${response.status}`, context);

        throw new McpError(
          JsonRpcErrorCode.InternalError,
          `Failed to fetch voices: ${response.status} - ${errorText}`,
        );
      }

      const data = (await response.json()) as ElevenLabsVoicesResponse;

      const voices: Voice[] = data.voices.map((v) => ({
        id: v.voice_id,
        name: v.name,
        ...(v.description !== undefined && { description: v.description }),
        ...(v.category !== undefined && { category: v.category }),
        ...(v.preview_url !== undefined && { previewUrl: v.preview_url }),
        ...(v.labels?.gender !== undefined && {
          gender: v.labels.gender as 'male' | 'female' | 'neutral',
        }),
        metadata: {
          labels: v.labels,
        },
      }));

      logger.info(`Successfully fetched ${voices.length} voices`, context);

      return voices;
    } catch (error) {
      if (error instanceof McpError) {
        throw error;
      }

      logger.error(
        'Failed to fetch voices',
        error instanceof Error ? error : new Error(String(error)),
        context,
      );

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to fetch voices: ${error instanceof Error ? error.message : 'Unknown error'}`,
      );
    }
  }

  /**
   * Health check for ElevenLabs API.
   */
  async healthCheck(): Promise<boolean> {
    try {
      // Simple health check: try to fetch voices
      await this.getVoices();
      return true;
    } catch (error) {
      const context = requestContextService.createRequestContext({
        operation: 'elevenlabs-healthCheck',
      });
      logger.error(
        'ElevenLabs health check failed',
        error instanceof Error ? error : new Error(String(error)),
        context,
      );
      return false;
    }
  }
}
