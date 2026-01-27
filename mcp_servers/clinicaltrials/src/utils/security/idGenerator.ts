/**
 * @fileoverview Provides a utility class `IdGenerator` for creating customizable, prefixed unique identifiers,
 * and a standalone `generateUUID` function for generating standard UUIDs.
 * The `IdGenerator` supports entity-specific prefixes, custom character sets, and lengths.
 *
 * Note: Logging has been removed from this module to prevent circular dependencies
 * with the `requestContextService`, which itself uses `generateUUID` from this module.
 * This was causing `ReferenceError: Cannot access 'generateUUID' before initialization`
 * during application startup.
 * @module src/utils/security/idGenerator
 */
import { randomUUID as cryptoRandomUUID, randomBytes } from 'crypto';

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';

// Removed: import { logger, requestContextService } from "../index.js";

/**
 * Defines the structure for configuring entity prefixes.
 * Keys are entity type names (e.g., "project", "task"), and values are their corresponding ID prefixes (e.g., "PROJ", "TASK").
 */
export interface EntityPrefixConfig {
  [key: string]: string;
}

/**
 * Defines options for customizing ID generation.
 */
export interface IdGenerationOptions {
  length?: number;
  separator?: string;
  charset?: string;
}

/**
 * A generic ID Generator class for creating and managing unique, prefixed identifiers.
 * Allows defining custom prefixes, generating random strings, and validating/normalizing IDs.
 */
export class IdGenerator {
  /**
   * Default character set for the random part of the ID.
   * @private
   */
  private static DEFAULT_CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  /**
   * Default separator character between prefix and random part.
   * @private
   */
  private static DEFAULT_SEPARATOR = '_';
  /**
   * Default length for the random part of the ID.
   * @private
   */
  private static DEFAULT_LENGTH = 6;

  /**
   * Stores the mapping of entity types to their prefixes.
   * @private
   */
  private entityPrefixes: EntityPrefixConfig = {};
  /**
   * Stores a reverse mapping from prefixes (case-insensitive) to entity types.
   * @private
   */
  private prefixToEntityType: Record<string, string> = {};

  /**
   * Constructs an `IdGenerator` instance.
   * @param entityPrefixes - An initial map of entity types to their prefixes.
   */
  constructor(entityPrefixes: EntityPrefixConfig = {}) {
    // Logging removed to prevent circular dependency with requestContextService.
    this.setEntityPrefixes(entityPrefixes);
  }

  /**
   * Sets or updates the entity prefix configuration and rebuilds the internal reverse lookup map.
   * @param entityPrefixes - A map where keys are entity type names and values are their desired ID prefixes.
   */
  public setEntityPrefixes(entityPrefixes: EntityPrefixConfig): void {
    // Logging removed.
    this.entityPrefixes = { ...entityPrefixes };

    this.prefixToEntityType = Object.entries(this.entityPrefixes).reduce(
      (acc, [type, prefix]) => {
        acc[prefix.toLowerCase()] = type; // Store lowercase for case-insensitive lookup
        return acc;
      },
      {} as Record<string, string>,
    );
  }

  /**
   * Retrieves a copy of the current entity prefix configuration.
   * @returns The current entity prefix configuration.
   */
  public getEntityPrefixes(): EntityPrefixConfig {
    return { ...this.entityPrefixes };
  }

  /**
   * Generates a cryptographically secure random string.
   * @param length - The desired length of the random string. Defaults to `IdGenerator.DEFAULT_LENGTH`.
   * @param charset - The character set to use. Defaults to `IdGenerator.DEFAULT_CHARSET`.
   * @returns The generated random string.
   */
  public generateRandomString(
    length: number = IdGenerator.DEFAULT_LENGTH,
    charset: string = IdGenerator.DEFAULT_CHARSET,
  ): string {
    let result = '';
    // Determine the largest multiple of charset.length that is less than or equal to 256
    // This is the threshold for rejection sampling to avoid bias.
    const maxValidByteValue = Math.floor(256 / charset.length) * charset.length;

    while (result.length < length) {
      const byteBuffer = randomBytes(1); // Get one random byte
      const byte = byteBuffer[0];

      // If the byte is within the valid range (i.e., it won't introduce bias),
      // use it to select a character from the charset. Otherwise, discard and try again.
      if (byte !== undefined && byte < maxValidByteValue) {
        const charIndex = byte % charset.length;
        const char = charset[charIndex];
        if (char) {
          result += char;
        }
      }
    }
    return result;
  }

  /**
   * Generates a unique ID, optionally prepended with a prefix.
   * @param prefix - An optional prefix for the ID.
   * @param options - Optional parameters for ID generation (length, separator, charset).
   * @returns A unique identifier string.
   */
  public generate(prefix?: string, options: IdGenerationOptions = {}): string {
    // Logging removed.
    const {
      length = IdGenerator.DEFAULT_LENGTH,
      separator = IdGenerator.DEFAULT_SEPARATOR,
      charset = IdGenerator.DEFAULT_CHARSET,
    } = options;

    const randomPart = this.generateRandomString(length, charset);
    const generatedId = prefix
      ? `${prefix}${separator}${randomPart}`
      : randomPart;
    return generatedId;
  }

  /**
   * Generates a unique ID for a specified entity type, using its configured prefix.
   * @param entityType - The type of entity (must be registered).
   * @param options - Optional parameters for ID generation.
   * @returns A unique identifier string for the entity (e.g., "PROJ_A6B3J0").
   * @throws {McpError} If the `entityType` is not registered.
   */
  public generateForEntity(
    entityType: string,
    options: IdGenerationOptions = {},
  ): string {
    const prefix = this.entityPrefixes[entityType];
    if (!prefix) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Unknown entity type: ${entityType}. No prefix registered.`,
      );
    }
    return this.generate(prefix, options);
  }

  /**
   * Validates if an ID conforms to the expected format for a specific entity type.
   * @param id - The ID string to validate.
   * @param entityType - The expected entity type of the ID.
   * @param options - Optional parameters used during generation for validation consistency.
   *                  The `charset` from these options will be used for validation.
   * @returns `true` if the ID is valid, `false` otherwise.
   */
  public isValid(
    id: string,
    entityType: string,
    options: IdGenerationOptions = {},
  ): boolean {
    const prefix = this.entityPrefixes[entityType];
    const {
      length = IdGenerator.DEFAULT_LENGTH,
      separator = IdGenerator.DEFAULT_SEPARATOR,
      charset = IdGenerator.DEFAULT_CHARSET, // Use charset from options or default
    } = options;

    if (!prefix) {
      return false;
    }

    // Build regex character class from the charset
    // Escape characters that have special meaning inside a regex character class `[]`
    const escapedCharsetForClass = charset.replace(/[[\]\\^-]/g, '\\$&');
    const charsetRegexPart = `[${escapedCharsetForClass}]`;

    const pattern = new RegExp(
      `^${this.escapeRegex(prefix)}${this.escapeRegex(separator)}${charsetRegexPart}{${length}}$`,
    );
    return pattern.test(id);
  }

  /**
   * Escapes special characters in a string for use in a regular expression.
   * @param str - The string to escape.
   * @returns The escaped string.
   * @private
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Strips the prefix and separator from an ID string.
   * @param id - The ID string (e.g., "PROJ_A6B3J0").
   * @param separator - The separator used in the ID. Defaults to `IdGenerator.DEFAULT_SEPARATOR`.
   * @returns The ID part without the prefix, or the original ID if separator not found.
   */
  public stripPrefix(
    id: string,
    separator: string = IdGenerator.DEFAULT_SEPARATOR,
  ): string {
    const parts = id.split(separator);
    return parts.length > 1 ? parts.slice(1).join(separator) : id; // Handle separators in random part
  }

  /**
   * Determines the entity type from an ID string by its prefix (case-insensitive).
   * @param id - The ID string (e.g., "PROJ_A6B3J0").
   * @param separator - The separator used in the ID. Defaults to `IdGenerator.DEFAULT_SEPARATOR`.
   * @returns The determined entity type.
   * @throws {McpError} If ID format is invalid or prefix is unknown.
   */
  public getEntityType(
    id: string,
    separator: string = IdGenerator.DEFAULT_SEPARATOR,
  ): string {
    const parts = id.split(separator);
    if (parts.length < 2 || !parts[0]) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Invalid ID format: ${id}. Expected format like: PREFIX${separator}RANDOMLPART`,
      );
    }

    const prefix = parts[0];
    const entityType = this.prefixToEntityType[prefix.toLowerCase()];

    if (!entityType) {
      throw new McpError(
        JsonRpcErrorCode.ValidationError,
        `Unknown entity type for prefix: ${prefix}`,
      );
    }
    return entityType;
  }

  /**
   * Normalizes an entity ID to ensure the prefix matches the registered case
   * and the random part is uppercase. Note: This assumes the charset characters
   * have a meaningful uppercase version if case-insensitivity is desired for the random part.
   * For default charset (A-Z0-9), this is fine. For custom charsets, behavior might vary.
   * @param id - The ID to normalize (e.g., "proj_a6b3j0").
   * @param separator - The separator used in the ID. Defaults to `IdGenerator.DEFAULT_SEPARATOR`.
   * @returns The normalized ID (e.g., "PROJ_A6B3J0").
   * @throws {McpError} If the entity type cannot be determined from the ID.
   */
  public normalize(
    id: string,
    separator: string = IdGenerator.DEFAULT_SEPARATOR,
  ): string {
    const entityType = this.getEntityType(id, separator);
    const registeredPrefix = this.entityPrefixes[entityType];
    const idParts = id.split(separator);
    const randomPart = idParts.slice(1).join(separator);

    // Consider if randomPart.toUpperCase() is always correct for custom charsets.
    // For now, maintaining existing behavior.
    return `${registeredPrefix}${separator}${randomPart.toUpperCase()}`;
  }
}

/**
 * Default singleton instance of the `IdGenerator`.
 * Initialize with `idGenerator.setEntityPrefixes({})` to configure.
 */
export const idGenerator = new IdGenerator();

/**
 * Generates a standard Version 4 UUID (Universally Unique Identifier).
 * Uses the Node.js `crypto` module.
 * @returns A new UUID string.
 */
export const generateUUID = (): string => {
  return cryptoRandomUUID();
};

/**
 * Generates a unique 10-character alphanumeric ID with a hyphen in the middle (e.g., `ABCDE-FGHIJ`).
 * This function is specifically for request contexts to provide a shorter, more readable ID.
 * It contains its own random string generation logic to remain self-contained and avoid circular dependencies.
 * @returns A new unique ID string.
 */
export const generateRequestContextId = (): string => {
  /**
   * Generates a cryptographically secure random string of a given length from a given charset.
   * @param length The desired length of the string.
   * @param charset The characters to use for generation.
   * @returns The generated random string.
   */
  const generateSecureRandomString = (
    length: number,
    charset: string,
  ): string => {
    let result = '';
    const maxValidByteValue = Math.floor(256 / charset.length) * charset.length;

    while (result.length < length) {
      const byteBuffer = randomBytes(1);
      const byte = byteBuffer[0];

      if (byte !== undefined && byte < maxValidByteValue) {
        const charIndex = byte % charset.length;
        const char = charset[charIndex];
        if (char) {
          result += char;
        }
      }
    }
    return result;
  };

  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const part1 = generateSecureRandomString(5, charset);
  const part2 = generateSecureRandomString(5, charset);
  return `${part1}-${part2}`;
};
