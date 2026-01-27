/**
 * @fileoverview Type definitions for the Speech service.
 * Provides interfaces for Text-to-Speech (TTS) and Speech-to-Text (STT) operations.
 * @module src/services/speech/types
 */

/**
 * Supported audio formats for speech operations.
 */
export type AudioFormat = 'mp3' | 'wav' | 'ogg' | 'flac' | 'pcm' | 'webm';

/**
 * Voice settings for text-to-speech synthesis.
 */
export interface VoiceSettings {
  /** Voice ID or name (provider-specific) */
  voiceId?: string;
  /** Speech rate/speed (0.5 to 2.0, where 1.0 is normal) */
  speed?: number;
  /** Voice pitch (-20.0 to 20.0, where 0 is normal) */
  pitch?: number;
  /** Volume level (0.0 to 1.0) */
  volume?: number;
  /** Stability setting (0.0 to 1.0, provider-specific) */
  stability?: number;
  /** Similarity boost (0.0 to 1.0, provider-specific) */
  similarityBoost?: number;
  /** Style exaggeration (0.0 to 1.0, provider-specific) */
  style?: number;
}

/**
 * Options for text-to-speech synthesis.
 */
export interface TextToSpeechOptions {
  /** Text to convert to speech */
  text: string;
  /** Voice settings */
  voice?: VoiceSettings;
  /** Output audio format */
  format?: AudioFormat;
  /** Model ID (provider-specific) */
  modelId?: string;
  /** Language code (e.g., 'en-US', 'es-ES') */
  language?: string;
  /** Optional context for request tracing */
  context?: {
    requestId?: string;
    traceId?: string;
    tenantId?: string;
  };
}

/**
 * Result from text-to-speech synthesis.
 */
export interface TextToSpeechResult {
  /** Audio data as Buffer or base64 string */
  audio: Buffer | string;
  /** Audio format */
  format: AudioFormat;
  /** Duration in seconds (if available) */
  duration?: number;
  /** Character count of input text */
  characterCount: number;
  /** Provider-specific metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Options for speech-to-text transcription.
 */
export interface SpeechToTextOptions {
  /** Audio data as Buffer or base64 string */
  audio: Buffer | string;
  /** Audio format */
  format?: AudioFormat;
  /** Language code hint (e.g., 'en', 'es') */
  language?: string;
  /** Model ID (provider-specific) */
  modelId?: string;
  /** Enable word-level timestamps */
  timestamps?: boolean;
  /** Temperature for sampling (0.0 to 1.0) */
  temperature?: number;
  /** Prompt to guide transcription style */
  prompt?: string;
  /** Optional context for request tracing */
  context?: {
    requestId?: string;
    traceId?: string;
    tenantId?: string;
  };
}

/**
 * Word-level timestamp information.
 */
export interface WordTimestamp {
  /** The word or token */
  word: string;
  /** Start time in seconds */
  start: number;
  /** End time in seconds */
  end: number;
  /** Confidence score (0.0 to 1.0) */
  confidence?: number;
}

/**
 * Result from speech-to-text transcription.
 */
export interface SpeechToTextResult {
  /** Transcribed text */
  text: string;
  /** Detected language code */
  language?: string;
  /** Duration in seconds */
  duration?: number;
  /** Word-level timestamps (if requested) */
  words?: WordTimestamp[];
  /** Overall confidence score (0.0 to 1.0) */
  confidence?: number;
  /** Provider-specific metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Available voices from a provider.
 */
export interface Voice {
  /** Voice ID */
  id: string;
  /** Voice name */
  name: string;
  /** Voice description */
  description?: string;
  /** Language codes supported */
  languages?: string[];
  /** Voice category (e.g., 'premade', 'cloned', 'professional') */
  category?: string;
  /** Gender (if applicable) */
  gender?: 'male' | 'female' | 'neutral';
  /** Preview URL (if available) */
  previewUrl?: string;
  /** Provider-specific metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Configuration for speech service providers.
 */
export interface SpeechProviderConfig {
  /** Provider type */
  provider: 'elevenlabs' | 'openai-whisper' | 'mock';
  /** API key */
  apiKey?: string;
  /** API base URL (optional override) */
  baseUrl?: string;
  /** Default voice ID for TTS */
  defaultVoiceId?: string;
  /** Default model ID */
  defaultModelId?: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Additional provider-specific options */
  options?: Record<string, unknown>;
}
