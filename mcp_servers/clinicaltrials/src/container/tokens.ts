/**
 * @fileoverview Defines all dependency injection tokens for the application.
 * This file centralizes the Symbols used for registering and resolving dependencies
 * in the container, breaking circular reference issues.
 * @module src/container/tokens
 */

// Use tokens for non-class dependencies or for multi-injection.
export const AppConfig = Symbol('AppConfig');
export const Logger = Symbol('Logger');
export const StorageService = Symbol('StorageService');
export const StorageProvider = Symbol('IStorageProvider');
export const LlmProvider = Symbol('ILlmProvider');
export const ToolDefinitions = Symbol('ToolDefinitions');
export const ResourceDefinitions = Symbol('ResourceDefinitions');
export const CreateMcpServerInstance = Symbol('CreateMcpServerInstance');
export const RateLimiterService = Symbol('RateLimiterService');
export const TransportManagerToken = Symbol('TransportManager');
export const SupabaseAdminClient = Symbol('SupabaseAdminClient');
export const SpeechService = Symbol('SpeechService');
export const ClinicalTrialsProvider = Symbol('IClinicalTrialsProvider');
