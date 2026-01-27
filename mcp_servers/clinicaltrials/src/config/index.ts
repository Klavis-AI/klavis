/**
 * @fileoverview Loads, validates, and exports application configuration.
 * This module centralizes configuration management, sourcing values from
 * environment variables. It uses Zod for schema validation to ensure type safety
 * and correctness of configuration parameters, and is designed to be
 * environment-agnostic (e.g., Node.js, Cloudflare Workers).
 *
 * @module src/config/index
 */
import dotenv from 'dotenv';
import { z } from 'zod';

import packageJson from '../../package.json' with { type: 'json' };
import { JsonRpcErrorCode, McpError } from '../types-global/errors.js';

type PackageManifest = {
  name?: string;
  version?: string;
  description?: string;
};

const packageManifest = packageJson as PackageManifest;
const hasFileSystemAccess =
  typeof process !== 'undefined' &&
  typeof process.versions === 'object' &&
  process.versions !== null &&
  typeof process.versions.node === 'string';

// Suppress dotenv's noisy initial log message as suggested by its output.
dotenv.config({ quiet: true });

// --- Helper Functions ---
const emptyStringAsUndefined = (val: unknown) => {
  if (typeof val === 'string' && val.trim() === '') {
    return undefined;
  }
  return val;
};

// --- Schema Definition ---
const ConfigSchema = z.object({
  // Package information sourced from environment variables
  pkg: z.object({
    name: z.string(),
    version: z.string(),
    description: z.string().optional(),
  }),
  mcpServerName: z.string(), // Will be derived from pkg.name
  mcpServerVersion: z.string(), // Will be derived from pkg.version
  mcpServerDescription: z.string().optional(), // Will be derived from pkg.description
  logLevel: z
    .preprocess(
      (val) => {
        const str = emptyStringAsUndefined(val);
        if (typeof str === 'string') {
          const lower = str.toLowerCase();
          const aliasMap: Record<string, string> = {
            warning: 'warn',
            err: 'error',
            information: 'info',
          };
          return aliasMap[lower] ?? lower;
        }
        return str;
      },
      z.enum(['fatal', 'error', 'warn', 'info', 'debug', 'trace', 'silent']),
    )
    .default('debug'),
  logsPath: z.string().optional(), // Made optional as it's Node-specific
  environment: z
    .preprocess(
      (val) => {
        const str = emptyStringAsUndefined(val);
        if (typeof str === 'string') {
          const lower = str.toLowerCase();
          const aliasMap: Record<string, string> = {
            dev: 'development',
            prod: 'production',
            test: 'testing',
          };
          return aliasMap[lower] ?? lower;
        }
        return str;
      },
      z.enum(['development', 'production', 'testing']),
    )
    .default('development'),
  mcpTransportType: z.preprocess(
    emptyStringAsUndefined,
    z.enum(['stdio', 'http']).default('stdio'),
  ),
  mcpSessionMode: z.preprocess(
    emptyStringAsUndefined,
    z.enum(['stateless', 'stateful', 'auto']).default('auto'),
  ),
  mcpHttpPort: z.coerce.number().default(3017),
  mcpHttpHost: z.string().default('127.0.0.1'),
  mcpHttpEndpointPath: z.string().default('/mcp'),
  mcpHttpMaxPortRetries: z.coerce.number().default(15),
  mcpHttpPortRetryDelayMs: z.coerce.number().default(50),
  mcpStatefulSessionStaleTimeoutMs: z.coerce.number().default(1_800_000),
  mcpAllowedOrigins: z.array(z.string()).optional(),
  mcpAuthSecretKey: z.string().optional(),
  mcpAuthMode: z.preprocess(
    emptyStringAsUndefined,
    z.enum(['jwt', 'oauth', 'none']).default('none'),
  ),
  oauthIssuerUrl: z.string().url().optional(),
  oauthJwksUri: z.string().url().optional(),
  oauthAudience: z.string().optional(),
  oauthJwksCooldownMs: z.coerce.number().default(300_000), // 5 minutes
  oauthJwksTimeoutMs: z.coerce.number().default(5_000), // 5 seconds
  mcpServerResourceIdentifier: z.string().url().optional(), // RFC 8707 resource indicator
  devMcpClientId: z.string().optional(),
  devMcpScopes: z.array(z.string()).optional(),
  openrouterAppUrl: z.string().default('http://localhost:3000'),
  openrouterAppName: z.string(),
  openrouterApiKey: z.string().optional(),
  llmDefaultModel: z.string().default('google/gemini-2.5-flash'),
  llmDefaultTemperature: z.coerce.number().optional(),
  llmDefaultTopP: z.coerce.number().optional(),
  llmDefaultMaxTokens: z.coerce.number().optional(),
  llmDefaultTopK: z.coerce.number().optional(),
  llmDefaultMinP: z.coerce.number().optional(),
  oauthProxy: z
    .object({
      authorizationUrl: z.string().url().optional(),
      tokenUrl: z.string().url().optional(),
      revocationUrl: z.string().url().optional(),
      issuerUrl: z.string().url().optional(),
      serviceDocumentationUrl: z.string().url().optional(),
      defaultClientRedirectUris: z.array(z.string()).optional(),
    })
    .optional(),
  supabase: z
    .object({
      url: z.string().url(),
      anonKey: z.string(),
      serviceRoleKey: z.string().optional(),
    })
    .optional(),
  storage: z.object({
    providerType: z
      .preprocess(
        (val) => {
          const str = emptyStringAsUndefined(val);
          if (typeof str === 'string') {
            const lower = str.toLowerCase();
            const aliasMap: Record<string, string> = {
              mem: 'in-memory',
              fs: 'filesystem',
            };
            return aliasMap[lower] ?? lower;
          }
          return str;
        },
        z.enum([
          'in-memory',
          'filesystem',
          'supabase',
          'cloudflare-r2',
          'cloudflare-kv',
        ]),
      )
      .default('in-memory'),
    filesystemPath: z.string().default('./.storage'), // This remains, but will only be used if providerType is 'filesystem'
  }),
  clinicalTrialsDataPath: z.string().optional(),
  maxStudiesForAnalysis: z.coerce.number().int().positive().default(5000),
  openTelemetry: z.object({
    enabled: z.coerce.boolean().default(false),
    serviceName: z.string(),
    serviceVersion: z.string(),
    tracesEndpoint: z.string().url().optional(),
    metricsEndpoint: z.string().url().optional(),
    samplingRatio: z.coerce.number().default(1.0),
    logLevel: z
      .preprocess(
        (val) => {
          const str = emptyStringAsUndefined(val);
          if (typeof str === 'string') {
            const lower = str.toLowerCase();
            const aliasMap: Record<string, string> = {
              err: 'ERROR',
              warning: 'WARN',
              information: 'INFO',
            };
            return aliasMap[lower] ?? str.toUpperCase();
          }
          return str;
        },
        z.enum(['NONE', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'VERBOSE', 'ALL']),
      )
      .default('INFO'),
  }),
  speech: z
    .object({
      tts: z
        .object({
          enabled: z.coerce.boolean().default(false),
          provider: z.enum(['elevenlabs']).default('elevenlabs'),
          apiKey: z.string().optional(),
          baseUrl: z.string().url().optional(),
          defaultVoiceId: z.string().optional(),
          defaultModelId: z.string().optional(),
          timeout: z.coerce.number().optional(),
        })
        .optional(),
      stt: z
        .object({
          enabled: z.coerce.boolean().default(false),
          provider: z.enum(['openai-whisper']).default('openai-whisper'),
          apiKey: z.string().optional(),
          baseUrl: z.string().url().optional(),
          defaultModelId: z.string().optional(),
          timeout: z.coerce.number().optional(),
        })
        .optional(),
    })
    .optional(),
});

// --- Parsing Logic ---
const parseConfig = () => {
  const env = process.env;

  const rawConfig = {
    pkg: {
      name: env.PACKAGE_NAME ?? packageManifest.name,
      version: env.PACKAGE_VERSION ?? packageManifest.version,
      description: env.PACKAGE_DESCRIPTION ?? packageManifest.description,
    },
    logLevel: env.MCP_LOG_LEVEL,
    logsPath: env.LOGS_DIR,
    environment: env.NODE_ENV,
    mcpTransportType: env.MCP_TRANSPORT_TYPE,
    mcpSessionMode: env.MCP_SESSION_MODE,
    mcpHttpPort: env.MCP_HTTP_PORT,
    mcpHttpHost: env.MCP_HTTP_HOST,
    mcpHttpEndpointPath: env.MCP_HTTP_ENDPOINT_PATH,
    mcpHttpMaxPortRetries: env.MCP_HTTP_MAX_PORT_RETRIES,
    mcpHttpPortRetryDelayMs: env.MCP_HTTP_PORT_RETRY_DELAY_MS,
    mcpStatefulSessionStaleTimeoutMs: env.MCP_STATEFUL_SESSION_STALE_TIMEOUT_MS,
    mcpAllowedOrigins: env.MCP_ALLOWED_ORIGINS?.split(',')
      .map((o) => o.trim())
      .filter(Boolean),
    mcpAuthSecretKey: env.MCP_AUTH_SECRET_KEY,
    mcpAuthMode: env.MCP_AUTH_MODE,
    oauthIssuerUrl: env.OAUTH_ISSUER_URL,
    oauthJwksUri: env.OAUTH_JWKS_URI,
    oauthAudience: env.OAUTH_AUDIENCE,
    oauthJwksCooldownMs: env.OAUTH_JWKS_COOLDOWN_MS,
    oauthJwksTimeoutMs: env.OAUTH_JWKS_TIMEOUT_MS,
    mcpServerResourceIdentifier: env.MCP_SERVER_RESOURCE_IDENTIFIER,
    devMcpClientId: env.DEV_MCP_CLIENT_ID,
    devMcpScopes: env.DEV_MCP_SCOPES?.split(',').map((s) => s.trim()),
    openrouterAppUrl: env.OPENROUTER_APP_URL,
    openrouterAppName: env.OPENROUTER_APP_NAME,
    openrouterApiKey: env.OPENROUTER_API_KEY,
    llmDefaultModel: env.LLM_DEFAULT_MODEL,
    llmDefaultTemperature: env.LLM_DEFAULT_TEMPERATURE,
    llmDefaultTopP: env.LLM_DEFAULT_TOP_P,
    llmDefaultMaxTokens: env.LLM_DEFAULT_MAX_TOKENS,
    llmDefaultTopK: env.LLM_DEFAULT_TOP_K,
    llmDefaultMinP: env.LLM_DEFAULT_MIN_P,
    oauthProxy:
      env.OAUTH_PROXY_AUTHORIZATION_URL || env.OAUTH_PROXY_TOKEN_URL
        ? {
            authorizationUrl: env.OAUTH_PROXY_AUTHORIZATION_URL,
            tokenUrl: env.OAUTH_PROXY_TOKEN_URL,
            revocationUrl: env.OAUTH_PROXY_REVOCATION_URL,
            issuerUrl: env.OAUTH_PROXY_ISSUER_URL,
            serviceDocumentationUrl: env.OAUTH_PROXY_SERVICE_DOCUMENTATION_URL,
            defaultClientRedirectUris:
              env.OAUTH_PROXY_DEFAULT_CLIENT_REDIRECT_URIS?.split(',')
                .map((uri) => uri.trim())
                .filter(Boolean),
          }
        : undefined,
    supabase:
      env.SUPABASE_URL && env.SUPABASE_ANON_KEY
        ? {
            url: env.SUPABASE_URL,
            anonKey: env.SUPABASE_ANON_KEY,
            serviceRoleKey: env.SUPABASE_SERVICE_ROLE_KEY,
          }
        : undefined,
    storage: {
      providerType: env.STORAGE_PROVIDER_TYPE,
      filesystemPath: env.STORAGE_FILESYSTEM_PATH,
    },
    clinicalTrialsDataPath: env.CLINICALTRIALS_DATA_PATH,
    maxStudiesForAnalysis: env.MAX_STUDIES_FOR_ANALYSIS,
    openTelemetry: {
      enabled: env.OTEL_ENABLED,
      serviceName: env.OTEL_SERVICE_NAME,
      serviceVersion: env.OTEL_SERVICE_VERSION,
      tracesEndpoint: env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
      metricsEndpoint: env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT,
      samplingRatio: env.OTEL_TRACES_SAMPLER_ARG,
      logLevel: env.OTEL_LOG_LEVEL,
    },
    speech:
      env.SPEECH_TTS_ENABLED || env.SPEECH_STT_ENABLED
        ? {
            tts: env.SPEECH_TTS_ENABLED
              ? {
                  enabled: env.SPEECH_TTS_ENABLED,
                  provider: env.SPEECH_TTS_PROVIDER,
                  apiKey: env.SPEECH_TTS_API_KEY,
                  baseUrl: env.SPEECH_TTS_BASE_URL,
                  defaultVoiceId: env.SPEECH_TTS_DEFAULT_VOICE_ID,
                  defaultModelId: env.SPEECH_TTS_DEFAULT_MODEL_ID,
                  timeout: env.SPEECH_TTS_TIMEOUT,
                }
              : undefined,
            stt: env.SPEECH_STT_ENABLED
              ? {
                  enabled: env.SPEECH_STT_ENABLED,
                  provider: env.SPEECH_STT_PROVIDER,
                  apiKey: env.SPEECH_STT_API_KEY,
                  baseUrl: env.SPEECH_STT_BASE_URL,
                  defaultModelId: env.SPEECH_STT_DEFAULT_MODEL_ID,
                  timeout: env.SPEECH_STT_TIMEOUT,
                }
              : undefined,
          }
        : undefined,
    // The following fields will be derived and are not directly from env
    mcpServerName: env.MCP_SERVER_NAME,
    mcpServerVersion: env.MCP_SERVER_VERSION,
    mcpServerDescription: env.MCP_SERVER_DESCRIPTION,
  };

  // Use a temporary schema to parse package info and provide defaults
  const pkgSchema = z.object({
    name: z.string(),
    version: z.string(),
    description: z.string().optional(),
  });
  const parsedPkg = pkgSchema.parse(rawConfig.pkg);

  // Now add the derived values to the main rawConfig object to be parsed
  const finalRawConfig = {
    ...rawConfig,
    pkg: parsedPkg,
    logsPath: rawConfig.logsPath ?? (hasFileSystemAccess ? 'logs' : undefined),
    mcpServerName: env.MCP_SERVER_NAME ?? parsedPkg.name,
    mcpServerVersion: env.MCP_SERVER_VERSION ?? parsedPkg.version,
    mcpServerDescription: env.MCP_SERVER_DESCRIPTION ?? parsedPkg.description,
    openTelemetry: {
      ...rawConfig.openTelemetry,
      serviceName: env.OTEL_SERVICE_NAME ?? parsedPkg.name,
      serviceVersion: env.OTEL_SERVICE_VERSION ?? parsedPkg.version,
    },
    openrouterAppName: env.OPENROUTER_APP_NAME ?? parsedPkg.name,
  };

  const parsedConfig = ConfigSchema.safeParse(finalRawConfig);

  if (!parsedConfig.success) {
    // Keep existing TTY error logging for developer convenience.
    if (process.stdout.isTTY) {
      console.error(
        '❌ Invalid configuration found. Please check your environment variables.',
        parsedConfig.error.flatten().fieldErrors,
      );
    }
    // Throw a specific, typed error instead of exiting.
    throw new McpError(
      JsonRpcErrorCode.ConfigurationError,
      'Invalid application configuration.',
      {
        validationErrors: parsedConfig.error.flatten().fieldErrors,
      },
    );
  }

  return parsedConfig.data;
};

const config = parseConfig();

/**
 * Export the runtime configuration, parser, and schema, plus a static AppConfig type.
 */
export type AppConfig = z.infer<typeof ConfigSchema>;

export { config, ConfigSchema, parseConfig };
