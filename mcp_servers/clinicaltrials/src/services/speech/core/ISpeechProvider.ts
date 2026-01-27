/**
 * @fileoverview Core interface definition for speech service providers.
 * Provides the contract for Text-to-Speech (TTS) and Speech-to-Text (STT) operations.
 * @module src/services/speech/core/ISpeechProvider
 */

import type {
  SpeechToTextOptions,
  SpeechToTextResult,
  TextToSpeechOptions,
  TextToSpeechResult,
  Voice,
} from '../types.js';

/**
 * Main interface for speech service providers.
 * Providers may implement TTS, STT, or both.
 */
export interface ISpeechProvider {
  /**
   * Provider name for identification.
   */
  readonly name: string;

  /**
   * Whether this provider supports text-to-speech.
   */
  readonly supportsTTS: boolean;

  /**
   * Whether this provider supports speech-to-text.
   */
  readonly supportsSTT: boolean;

  /**
   * Convert text to speech audio.
   * @throws {McpError} if TTS is not supported or operation fails
   */
  textToSpeech(options: TextToSpeechOptions): Promise<TextToSpeechResult>;

  /**
   * Convert speech audio to text.
   * @throws {McpError} if STT is not supported or operation fails
   */
  speechToText(options: SpeechToTextOptions): Promise<SpeechToTextResult>;

  /**
   * Get available voices (for TTS providers).
   * @throws {McpError} if operation fails or not supported
   */
  getVoices(): Promise<Voice[]>;

  /**
   * Health check for the provider.
   * @returns true if provider is healthy and configured correctly
   */
  healthCheck(): Promise<boolean>;
}

/**
 * Type guard to check if a provider supports TTS.
 */
export function supportsTTS(
  provider: ISpeechProvider,
): provider is ISpeechProvider {
  return provider.supportsTTS;
}

/**
 * Type guard to check if a provider supports STT.
 */
export function supportsSTT(
  provider: ISpeechProvider,
): provider is ISpeechProvider {
  return provider.supportsSTT;
}
