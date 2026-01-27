/**
 * @fileoverview OpenAI Whisper speech-to-text provider implementation.
 * @module src/services/speech/providers/whisper
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
  WordTimestamp,
} from '../types.js';

/**
 * OpenAI Whisper API response for transcription.
 */
interface WhisperTranscriptionResponse {
  text: string;
  task?: string;
  language?: string;
  duration?: number;
  words?: Array<{
    word: string;
    start: number;
    end: number;
  }>;
}

/**
 * OpenAI Whisper STT provider.
 * Supports high-quality speech-to-text transcription in multiple languages.
 */
@injectable()
export class WhisperProvider implements ISpeechProvider {
  public readonly name = 'openai-whisper';
  public readonly supportsTTS = false;
  public readonly supportsSTT = true;

  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly defaultModelId: string;
  private readonly timeout: number;

  constructor(config: SpeechProviderConfig) {
    if (!config.apiKey) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'OpenAI API key is required',
      );
    }

    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.openai.com/v1';
    this.defaultModelId = config.defaultModelId || 'whisper-1';
    this.timeout = config.timeout || 60000; // Longer timeout for audio processing

    logger.info(
      `OpenAI Whisper STT provider initialized: ${this.baseUrl}, model=${this.defaultModelId}`,
    );
  }

  /**
   * Text-to-speech is not supported by Whisper.
   */
  textToSpeech(_options: TextToSpeechOptions): Promise<TextToSpeechResult> {
    throw new McpError(
      JsonRpcErrorCode.MethodNotFound,
      'Text-to-speech is not supported by Whisper provider',
    );
  }

  /**
   * Convert speech audio to text using OpenAI Whisper API.
   */
  async speechToText(
    options: SpeechToTextOptions,
  ): Promise<SpeechToTextResult> {
    const context = requestContextService.createRequestContext({
      operation: 'whisper-stt',
      ...(options.context || {}),
    });
    const modelId = options.modelId || this.defaultModelId;

    logger.debug('Converting speech to text with Whisper', context);

    // Validate audio input
    if (!options.audio) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'Audio data is required',
        context,
      );
    }

    // Convert audio to Buffer if it's a base64 string
    let audioBuffer: Buffer;
    if (typeof options.audio === 'string') {
      try {
        audioBuffer = Buffer.from(options.audio, 'base64');
      } catch (_error) {
        throw new McpError(
          JsonRpcErrorCode.InvalidParams,
          'Invalid base64 audio data',
          context,
        );
      }
    } else {
      audioBuffer = options.audio;
    }

    // Check file size (Whisper has a 25MB limit)
    const maxSize = 25 * 1024 * 1024; // 25MB
    if (audioBuffer.length > maxSize) {
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        `Audio file exceeds maximum size of 25MB (got ${Math.round(audioBuffer.length / 1024 / 1024)}MB)`,
        context,
      );
    }

    const url = `${this.baseUrl}/audio/transcriptions`;

    // Build form data
    const formData = new FormData();

    // Determine filename with appropriate extension
    const extension = this.getFileExtension(options.format);
    const blob = new Blob([audioBuffer], {
      type: this.getMimeType(options.format),
    });
    formData.append('file', blob, `audio.${extension}`);
    formData.append('model', modelId);

    if (options.language) {
      formData.append('language', options.language);
    }

    if (options.temperature !== undefined) {
      formData.append('temperature', options.temperature.toString());
    }

    if (options.prompt) {
      formData.append('prompt', options.prompt);
    }

    // Request verbose JSON format to get timestamps and metadata
    formData.append(
      'response_format',
      options.timestamps ? 'verbose_json' : 'json',
    );

    if (options.timestamps) {
      formData.append('timestamp_granularities[]', 'word');
    }

    try {
      const response = await fetchWithTimeout(url, this.timeout, context, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          // Don't set Content-Type - let fetch set it with boundary for FormData
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        logger.error(`Whisper API error: ${response.status}`, context);

        throw new McpError(
          JsonRpcErrorCode.InternalError,
          `Whisper API error: ${response.status} - ${errorText}`,
          context,
        );
      }

      const data = (await response.json()) as WhisperTranscriptionResponse;

      // Convert word timestamps if present
      const words: WordTimestamp[] | undefined = data.words?.map((w) => ({
        word: w.word,
        start: w.start,
        end: w.end,
      }));

      logger.info(
        `Speech-to-text transcription successful (${data.text.length} chars)`,
        context,
      );

      return {
        text: data.text,
        ...(data.language !== undefined && { language: data.language }),
        ...(data.duration !== undefined && { duration: data.duration }),
        ...(words !== undefined && { words }),
        metadata: {
          modelId,
          provider: this.name,
          ...(data.task !== undefined && { task: data.task }),
        },
      };
    } catch (error) {
      if (error instanceof McpError) {
        throw error;
      }

      logger.error(
        'Failed to transcribe audio',
        error instanceof Error ? error : new Error(String(error)),
        context,
      );

      throw new McpError(
        JsonRpcErrorCode.InternalError,
        `Failed to transcribe audio: ${error instanceof Error ? error.message : 'Unknown error'}`,
        context,
      );
    }
  }

  /**
   * Get voices is not applicable for STT providers.
   */
  getVoices(): Promise<Voice[]> {
    throw new McpError(
      JsonRpcErrorCode.MethodNotFound,
      'Voice listing is not supported by Whisper provider (STT only)',
    );
  }

  /**
   * Health check for OpenAI Whisper API.
   */
  async healthCheck(): Promise<boolean> {
    try {
      // Simple health check: verify API key by making a models list request
      const context = requestContextService.createRequestContext({
        operation: 'whisper-healthCheck',
      });
      const response = await fetchWithTimeout(
        `${this.baseUrl}/models`,
        5000,
        context,
        {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${this.apiKey}`,
          },
        },
      );

      return response.ok;
    } catch (error) {
      const context = requestContextService.createRequestContext({
        operation: 'whisper-healthCheck',
      });
      logger.error(
        'Whisper health check failed',
        error instanceof Error ? error : new Error(String(error)),
        context,
      );
      return false;
    }
  }

  /**
   * Get file extension for audio format.
   */
  private getFileExtension(format?: string): string {
    const formatMap: Record<string, string> = {
      mp3: 'mp3',
      wav: 'wav',
      ogg: 'ogg',
      flac: 'flac',
      webm: 'webm',
      m4a: 'm4a',
    };

    return format && formatMap[format] ? formatMap[format] : 'mp3';
  }

  /**
   * Get MIME type for audio format.
   */
  private getMimeType(format?: string): string {
    const mimeMap: Record<string, string> = {
      mp3: 'audio/mpeg',
      wav: 'audio/wav',
      ogg: 'audio/ogg',
      flac: 'audio/flac',
      webm: 'audio/webm',
      m4a: 'audio/mp4',
    };

    return format && mimeMap[format] ? mimeMap[format] : 'audio/mpeg';
  }
}
