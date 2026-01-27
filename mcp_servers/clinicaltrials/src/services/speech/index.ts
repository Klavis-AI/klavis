/**
 * @fileoverview Speech service barrel export.
 * Provides unified access to TTS and STT capabilities.
 * @module src/services/speech
 */

// Export core interfaces and service
export type { ISpeechProvider } from './core/ISpeechProvider.js';
export { supportsTTS, supportsSTT } from './core/ISpeechProvider.js';
export { SpeechService, createSpeechProvider } from './core/SpeechService.js';

// Export provider implementations
export { ElevenLabsProvider } from './providers/elevenlabs.provider.js';
export { WhisperProvider } from './providers/whisper.provider.js';

// Export types
export type {
  SpeechProviderConfig,
  TextToSpeechOptions,
  TextToSpeechResult,
  SpeechToTextOptions,
  SpeechToTextResult,
  Voice,
  VoiceSettings,
  WordTimestamp,
  AudioFormat,
} from './types.js';
