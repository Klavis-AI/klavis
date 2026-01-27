/**
 * @fileoverview Provides a comprehensive `Sanitization` class for various input cleaning and validation tasks.
 * This module includes utilities for sanitizing HTML, strings, URLs, file paths, JSON, numbers,
 * and for redacting sensitive information from data intended for logging.
 * The path sanitization utilities are only available in a Node.js environment.
 * @module src/utils/security/sanitization
 */
import sanitizeHtml from 'sanitize-html';
import validator from 'validator';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, requestContextService } from '@/utils/index.js';

const isServerless =
  typeof process === 'undefined' || process.env.IS_SERVERLESS === 'true';

// Dynamically import 'path' only in non-serverless environments
let pathModule: typeof import('path') | undefined;
if (!isServerless) {
  import('path')
    .then((mod) => {
      pathModule = mod.default;
    })
    .catch(() => {
      // This might happen in some bundlers, but we have the guard.
    });
}

/**
 * Defines options for path sanitization to control how file paths are processed and validated.
 */
export interface PathSanitizeOptions {
  /** If provided, restricts sanitized paths to be relative to this directory. */
  rootDir?: string;
  /** If true, normalizes Windows backslashes to POSIX forward slashes. */
  toPosix?: boolean;
  /** If true, absolute paths are permitted (subject to `rootDir`). Default: false. */
  allowAbsolute?: boolean;
}

/**
 * Contains information about a path sanitization operation.
 */
export interface SanitizedPathInfo {
  /** The final sanitized and normalized path string. */
  sanitizedPath: string;
  /** The original path string before any processing. */
  originalInput: string;
  /** True if the input path was absolute after initial normalization. */
  wasAbsolute: boolean;
  /** True if an absolute path was converted to relative due to `allowAbsolute: false`. */
  convertedToRelative: boolean;
  /** The effective options used for sanitization, including defaults. */
  optionsUsed: PathSanitizeOptions;
}

/**
 * Defines options for context-specific string sanitization.
 */
export interface SanitizeStringOptions {
  /** The context in which the string will be used. 'javascript' is disallowed. */
  context?: 'text' | 'html' | 'attribute' | 'url' | 'javascript';
  /** Custom allowed HTML tags if `context` is 'html'. */
  allowedTags?: string[];
  /** Custom allowed HTML attributes if `context` is 'html'. */
  allowedAttributes?: Record<string, string[]>;
}

/**
 * Configuration options for HTML sanitization, mirroring `sanitize-html` library options.
 */
export interface HtmlSanitizeConfig {
  /** An array of allowed HTML tag names. */
  allowedTags?: string[];
  /** Specifies allowed attributes, either globally or per tag. */
  allowedAttributes?: sanitizeHtml.IOptions['allowedAttributes'];
  /** If true, HTML comments are preserved. */
  preserveComments?: boolean;
  /** Custom functions to transform tags during sanitization. */
  transformTags?: sanitizeHtml.IOptions['transformTags'];
}

/**
 * A singleton class providing various methods for input sanitization.
 * Aims to protect against common vulnerabilities like XSS and path traversal.
 */
export class Sanitization {
  /** @private */
  private static instance: Sanitization;

  /**
   * Default list of field names considered sensitive for log redaction.
   * Case-insensitive matching is applied.
   * @private
   */
  private sensitiveFields: string[] = [
    'password',
    'token',
    'secret',
    'apiKey',
    'credential',
    'jwt',
    'ssn',
    'cvv',
    'authorization',
    'cookie',
    'clientsecret',
    'client_secret',
    'private_key',
    'privatekey',
  ];

  /**
   * Default configuration for HTML sanitization.
   * @private
   */
  private defaultHtmlSanitizeConfig: HtmlSanitizeConfig = {
    allowedTags: [
      // === Structure & Sectioning ===
      'div',
      'span',
      'p',
      'br',
      'hr',
      'header',
      'footer',
      'nav',
      'article',
      'section',
      'aside',
      // === Headings & Text Content ===
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'strong',
      'em',
      'b',
      'i',
      'strike',
      'blockquote',
      // === Code ===
      'code',
      'pre',
      // === Lists ===
      'ul',
      'ol',
      'li',
      // === Tables ===
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
      // === Media & Links ===
      'a',
      'img',
      'figure',
      'figcaption',
    ],
    allowedAttributes: {
      a: ['href', 'name', 'target', 'rel', 'title'],
      img: ['src', 'alt', 'title', 'width', 'height', 'loading'],
      // Allow data attributes, class, id, and style on all tags
      '*': ['class', 'id', 'style', 'data-*'],
      // Table-specific attributes
      th: ['scope'],
      td: ['colspan', 'rowspan'],
    },
    preserveComments: true,
  };

  /** @private */
  private constructor() {}

  /**
   * Retrieves the singleton instance of the `Sanitization` class.
   * @returns The singleton `Sanitization` instance.
   */
  public static getInstance(): Sanitization {
    if (!Sanitization.instance) {
      Sanitization.instance = new Sanitization();
    }
    return Sanitization.instance;
  }

  /**
   * Sets or extends the list of sensitive field names for log sanitization.
   * @param fields - An array of field names to add to the sensitive list.
   */
  public setSensitiveFields(fields: string[]): void {
    this.sensitiveFields = [
      ...new Set([
        ...this.sensitiveFields,
        ...fields.map((f) => f.toLowerCase()),
      ]),
    ];
    const logContext = requestContextService.createRequestContext({
      operation: 'Sanitization.setSensitiveFields',
      additionalContext: {
        newSensitiveFieldCount: this.sensitiveFields.length,
      },
    });
    logger.debug(
      'Updated sensitive fields list for log sanitization',
      logContext,
    );
  }

  /**
   * Gets a copy of the current list of sensitive field names.
   * @returns An array of sensitive field names.
   */
  public getSensitiveFields(): string[] {
    return [...this.sensitiveFields];
  }

  /**
   * Gets a pino-compliant copy of the current list of sensitive field names.
   * @returns A pino-compliant array of sensitive field names.
   */
  public getSensitivePinoFields(): string[] {
    return this.sensitiveFields.map((field) => field.replace(/[-_]/g, ''));
  }

  /**
   * Sanitizes an HTML string by removing potentially malicious tags and attributes.
   * @param input - The HTML string to sanitize.
   * @param config - Optional custom configuration for `sanitize-html`.
   * @returns The sanitized HTML string. Returns an empty string if input is falsy.
   */
  public sanitizeHtml(input: string, config?: HtmlSanitizeConfig): string {
    if (!input) return '';
    const effectiveConfig = {
      allowedTags:
        config?.allowedTags ?? this.defaultHtmlSanitizeConfig.allowedTags,
      allowedAttributes:
        config?.allowedAttributes ??
        this.defaultHtmlSanitizeConfig.allowedAttributes,
      transformTags: config?.transformTags, // Can be undefined
      preserveComments:
        config?.preserveComments ??
        this.defaultHtmlSanitizeConfig.preserveComments,
    };

    const options: sanitizeHtml.IOptions = {
      allowedTags: effectiveConfig.allowedTags,
      allowedAttributes: effectiveConfig.allowedAttributes,
      transformTags: effectiveConfig.transformTags,
    };

    if (effectiveConfig.preserveComments) {
      // Ensure allowedTags is an array before spreading
      const baseTags = Array.isArray(options.allowedTags)
        ? options.allowedTags
        : [];
      options.allowedTags = [...baseTags, '!--'];
    }
    return sanitizeHtml(input, options);
  }

  /**
   * Sanitizes a string based on its intended context (e.g., HTML, URL, text).
   * **Important:** `context: 'javascript'` is disallowed due to security risks.
   *
   * @param input - The string to sanitize.
   * @param options - Options specifying the sanitization context.
   * @returns The sanitized string. Returns an empty string if input is falsy.
   * @throws {McpError} If `options.context` is 'javascript', or URL validation fails.
   */
  public sanitizeString(
    input: string,
    options: SanitizeStringOptions = {},
  ): string {
    if (!input) return '';

    const context = options.context ?? 'text';

    switch (context) {
      case 'html': {
        const config: HtmlSanitizeConfig = {};
        if (options.allowedTags) {
          config.allowedTags = options.allowedTags;
        }
        if (options.allowedAttributes) {
          config.allowedAttributes = this.convertAttributesFormat(
            options.allowedAttributes,
          );
        }
        return this.sanitizeHtml(input, config);
      }
      case 'attribute':
        return sanitizeHtml(input, { allowedTags: [], allowedAttributes: {} });
      case 'url':
        if (
          !validator.isURL(input, {
            protocols: ['http', 'https'],
            require_protocol: true,
            require_host: true,
          })
        ) {
          logger.warning(
            'Potentially invalid URL detected during string sanitization (context: url)',
            requestContextService.createRequestContext({
              operation: 'Sanitization.sanitizeString.urlWarning',
              additionalContext: { invalidUrlAttempt: input },
            }),
          );
          return '';
        }
        return validator.trim(input);
      case 'javascript':
        logger.error(
          'Attempted JavaScript sanitization via sanitizeString, which is disallowed.',
          requestContextService.createRequestContext({
            operation: 'Sanitization.sanitizeString.jsAttempt',
            additionalContext: { inputSnippet: input.substring(0, 50) },
          }),
        );
        throw new McpError(
          JsonRpcErrorCode.ValidationError,
          'JavaScript sanitization is not supported through sanitizeString due to security risks.',
        );
      case 'text':
      default:
        return sanitizeHtml(input, { allowedTags: [], allowedAttributes: {} });
    }
  }

  /**
   * Converts attribute format for `sanitizeHtml`.
   * @param attrs - Attributes in `{ tagName: ['attr1'] }` format.
   * @returns Attributes in `sanitize-html` expected format.
   * @private
   */
  private convertAttributesFormat(
    attrs: Record<string, string[]>,
  ): sanitizeHtml.IOptions['allowedAttributes'] {
    return attrs;
  }

  /**
   * Sanitizes a URL string by validating its format and protocol.
   * @param input - The URL string to sanitize.
   * @param allowedProtocols - Array of allowed URL protocols. Default: `['http', 'https']`.
   * @returns The sanitized and trimmed URL string.
   * @throws {McpError} If the URL is invalid or uses a disallowed protocol.
   */
  public sanitizeUrl(
    input: string,
    allowedProtocols: string[] = ['http', 'https'],
  ): string {
    try {
      const trimmedInput = input.trim();
      if (
        !validator.isURL(trimmedInput, {
          protocols: allowedProtocols,
          require_protocol: true,
          require_host: true,
        })
      ) {
        throw new Error('Invalid URL format or protocol not in allowed list.');
      }
      const lowercasedInput = trimmedInput.toLowerCase();
      if (
        lowercasedInput.startsWith('javascript:') ||
        lowercasedInput.startsWith('data:') ||
        lowercasedInput.startsWith('vbscript:')
      ) {
        throw new Error(
          'Disallowed pseudo-protocol (javascript:, data:, or vbscript:) in URL.',
        );
      }
      return trimmedInput;
    } catch (error) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        error instanceof Error
          ? error.message
          : 'Invalid or unsafe URL provided.',
        { input },
      );
    }
  }

  /**
   * Sanitizes a file path to prevent path traversal and normalize format.
   * This method is only available in a Node.js environment.
   * @param input - The file path string to sanitize.
   * @param options - Options to control sanitization behavior.
   * @returns An object with the sanitized path and sanitization metadata.
   * @throws {McpError} If the path is invalid, unsafe, or method is called in a non-Node.js environment.
   */
  public sanitizePath(
    input: string,
    options: PathSanitizeOptions = {},
  ): SanitizedPathInfo {
    if (isServerless || !pathModule) {
      throw new McpError(
        JsonRpcErrorCode.InternalError,
        'File-based path sanitization is not supported in this environment.',
      );
    }
    const path = pathModule;

    const originalInput = input;
    const resolvedRootDir = options.rootDir
      ? path.resolve(options.rootDir)
      : undefined;
    const effectiveOptions: PathSanitizeOptions = {
      toPosix: options.toPosix ?? false,
      allowAbsolute: options.allowAbsolute ?? false,
      ...(resolvedRootDir && { rootDir: resolvedRootDir }),
    };

    let wasAbsoluteInitially = false;

    try {
      if (!input || typeof input !== 'string')
        throw new Error('Invalid path input: must be a non-empty string.');
      if (input.includes('\0'))
        throw new Error('Path contains null byte, which is disallowed.');

      let normalized = path.normalize(input);
      wasAbsoluteInitially = path.isAbsolute(normalized);

      if (effectiveOptions.toPosix) {
        normalized = normalized.replace(/\\/g, '/');
      }

      let finalSanitizedPath: string;

      if (resolvedRootDir) {
        const fullPath = path.resolve(resolvedRootDir, normalized);
        if (
          !fullPath.startsWith(resolvedRootDir + path.sep) &&
          fullPath !== resolvedRootDir
        ) {
          throw new Error(
            'Path traversal detected: attempts to escape the defined root directory.',
          );
        }
        finalSanitizedPath = path.relative(resolvedRootDir, fullPath);
        finalSanitizedPath =
          finalSanitizedPath === '' ? '.' : finalSanitizedPath;
        if (
          path.isAbsolute(finalSanitizedPath) &&
          !effectiveOptions.allowAbsolute
        ) {
          throw new Error(
            'Path resolved to absolute outside root when absolute paths are disallowed.',
          );
        }
      } else {
        if (path.isAbsolute(normalized)) {
          if (!effectiveOptions.allowAbsolute) {
            throw new Error(
              'Absolute paths are disallowed by current options.',
            );
          } else {
            finalSanitizedPath = normalized;
          }
        } else {
          const resolvedAgainstCwd = path.resolve(normalized);
          const currentWorkingDir = path.resolve('.');
          if (
            !resolvedAgainstCwd.startsWith(currentWorkingDir + path.sep) &&
            resolvedAgainstCwd !== currentWorkingDir
          ) {
            throw new Error(
              'Relative path traversal detected (escapes current working directory context).',
            );
          }
          finalSanitizedPath = normalized;
        }
      }

      return {
        sanitizedPath: finalSanitizedPath,
        originalInput,
        wasAbsolute: wasAbsoluteInitially,
        convertedToRelative:
          wasAbsoluteInitially &&
          !path.isAbsolute(finalSanitizedPath) &&
          !effectiveOptions.allowAbsolute,
        optionsUsed: effectiveOptions,
      };
    } catch (error) {
      logger.warning(
        'Path sanitization error',
        requestContextService.createRequestContext({
          operation: 'Sanitization.sanitizePath.error',
          additionalContext: {
            originalPathInput: originalInput,
            pathOptionsUsed: effectiveOptions,
            errorMessage:
              error instanceof Error ? error.message : String(error),
          },
        }),
      );
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        error instanceof Error
          ? error.message
          : 'Invalid or unsafe path provided.',
        { input: originalInput },
      );
    }
  }

  /**
   * Sanitizes a JSON string by parsing it to validate its format.
   * Optionally checks if the JSON string exceeds a maximum allowed size.
   * @template T The expected type of the parsed JSON object. Defaults to `unknown`.
   * @param input - The JSON string to sanitize/validate.
   * @param maxSize - Optional maximum allowed size of the JSON string in bytes.
   * @returns The parsed JavaScript object.
   * @throws {McpError} If input is not a string, too large, or invalid JSON.
   */
  public sanitizeJson<T = unknown>(input: string, maxSize?: number): T {
    try {
      if (typeof input !== 'string')
        throw new Error('Invalid input: expected a JSON string.');

      // Cross-environment byte length computation
      const computeBytes = (s: string): number => {
        if (
          typeof Buffer !== 'undefined' &&
          typeof Buffer.byteLength === 'function'
        ) {
          return Buffer.byteLength(s, 'utf8');
        }
        if (typeof TextEncoder !== 'undefined') {
          return new TextEncoder().encode(s).length;
        }
        return s.length;
      };

      if (maxSize !== undefined && computeBytes(input) > maxSize) {
        throw new McpError(
          JsonRpcErrorCode.ValidationError,
          `JSON string exceeds maximum allowed size of ${maxSize} bytes.`,
          { actualSize: computeBytes(input), maxSize },
        );
      }

      return JSON.parse(input) as T;
    } catch (error) {
      if (error instanceof McpError) throw error;
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        error instanceof Error ? error.message : 'Invalid JSON format.',
        {
          inputPreview:
            input.length > 100 ? `${input.substring(0, 100)}...` : input,
        },
      );
    }
  }

  /**
   * Validates and sanitizes a numeric input, converting strings to numbers.
   * Clamps the number to `min`/`max` if provided.
   * @param input - The number or string to validate and sanitize.
   * @param min - Minimum allowed value (inclusive).
   * @param max - Maximum allowed value (inclusive).
   * @returns The sanitized (and potentially clamped) number.
   * @throws {McpError} If input is not a valid number, NaN, or Infinity.
   */
  public sanitizeNumber(
    input: number | string,
    min?: number,
    max?: number,
  ): number {
    let value: number;
    if (typeof input === 'string') {
      const trimmedInput = input.trim();
      if (trimmedInput === '' || !validator.isNumeric(trimmedInput)) {
        throw new McpError(
          JsonRpcErrorCode.ValidationError,
          'Invalid number format: input is empty or not numeric.',
          { input },
        );
      }
      value = parseFloat(trimmedInput);
    } else if (typeof input === 'number') {
      value = input;
    } else {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        'Invalid input type: expected number or string.',
        { input: String(input) },
      );
    }

    if (isNaN(value) || !isFinite(value)) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        'Invalid number value (NaN or Infinity).',
        { input },
      );
    }

    let clamped = false;
    const originalValueForLog = value;
    if (min !== undefined && value < min) {
      value = min;
      clamped = true;
    }
    if (max !== undefined && value > max) {
      value = max;
      clamped = true;
    }
    if (clamped) {
      logger.debug(
        'Number clamped to range.',
        requestContextService.createRequestContext({
          operation: 'Sanitization.sanitizeNumber.clamped',
          additionalContext: {
            originalInput: String(input),
            parsedValue: originalValueForLog,
            minValue: min,
            maxValue: max,
            clampedValue: value,
          },
        }),
      );
    }
    return value;
  }

  /**
   * Sanitizes input for logging by redacting sensitive fields.
   * Creates a deep clone and replaces values of fields matching `this.sensitiveFields`
   * (case-insensitive substring match) with "[REDACTED]".
   *
   * It uses `structuredClone` if available for a high-fidelity deep clone.
   * If `structuredClone` is not available (e.g., in older Node.js environments),
   * it falls back to `JSON.parse(JSON.stringify(input))`. This fallback has limitations:
   * - `Date` objects are converted to ISO date strings.
   * - `undefined` values within objects are removed.
   * - `Map`, `Set`, `RegExp` objects are converted to empty objects (`{}`).
   * - Functions are removed.
   * - `BigInt` values will throw an error during `JSON.stringify` unless a `toJSON` method is provided.
   * - Circular references will cause `JSON.stringify` to throw an error.
   *
   * @param input - The input data to sanitize for logging.
   * @returns A sanitized (deep cloned) version of the input, safe for logging.
   *   Returns original input if not object/array, or "[Log Sanitization Failed]" on error.
   */
  public sanitizeForLogging(input: unknown): unknown {
    try {
      if (!input || typeof input !== 'object') return input;

      const clonedInput: unknown =
        typeof globalThis.structuredClone === 'function'
          ? globalThis.structuredClone(input)
          : JSON.parse(JSON.stringify(input));
      this.redactSensitiveFields(clonedInput);
      return clonedInput;
    } catch (error) {
      logger.error(
        'Error during log sanitization, returning placeholder.',
        requestContextService.createRequestContext({
          operation: 'Sanitization.sanitizeForLogging.error',
          additionalContext: {
            errorMessage:
              error instanceof Error ? error.message : String(error),
          },
        }),
      );
      return '[Log Sanitization Failed]';
    }
  }

  /**
   * Recursively redacts sensitive fields in an object or array in place.
   * @param obj - The object or array to redact.
   * @private
   */
  private redactSensitiveFields(obj: unknown): void {
    if (!obj || typeof obj !== 'object') return;

    if (Array.isArray(obj)) {
      obj.forEach((item) => this.redactSensitiveFields(item));
      return;
    }

    const normalize = (str: string): string =>
      str.toLowerCase().replace(/[^a-z0-9]/g, '');
    const normalizedSensitiveSet = new Set(
      this.sensitiveFields.map((f) => normalize(f)).filter(Boolean),
    );
    const wordSensitiveSet = new Set(
      this.sensitiveFields.map((f) => f.toLowerCase()).filter(Boolean),
    );

    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        const value = (obj as Record<string, unknown>)[key];
        const normalizedKey = normalize(key);
        // Split into words for token-based matching (camelCase, snake_case, kebab-case)
        const keyWords = key
          .replace(/([A-Z])/g, ' $1')
          .toLowerCase()
          .split(/[\s_-]+/)
          .filter(Boolean);

        const isExactSensitive = normalizedSensitiveSet.has(normalizedKey);
        const isWordSensitive = keyWords.some((w) => wordSensitiveSet.has(w));
        const isSensitive = isExactSensitive || isWordSensitive;

        if (isSensitive) {
          (obj as Record<string, unknown>)[key] = '[REDACTED]';
        } else if (value && typeof value === 'object') {
          this.redactSensitiveFields(value);
        }
      }
    }
  }
}

/**
 * Singleton instance of the `Sanitization` class.
 * Use this for all input sanitization tasks.
 */
export const sanitization = Sanitization.getInstance();

/**
 * Convenience function calling `sanitization.sanitizeForLogging`.
 * @param input - The input data to sanitize.
 * @returns A sanitized version of the input, safe for logging.
 */
export const sanitizeInputForLogging = (input: unknown): unknown =>
  sanitization.sanitizeForLogging(input);
