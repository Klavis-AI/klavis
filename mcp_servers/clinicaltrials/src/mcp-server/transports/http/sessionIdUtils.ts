/**
 * @fileoverview Utilities for generating and validating cryptographically secure session IDs.
 * @module src/mcp-server/transports/http/sessionIdUtils
 */
import { randomBytes } from 'crypto';

import { runtimeCaps } from '@/utils/internal/runtime.js';

/**
 * Generates a cryptographically secure session ID.
 *
 * Uses 32 bytes (256 bits) of entropy, which provides sufficient security
 * for session identification per OWASP guidelines.
 *
 * @returns A 64-character hexadecimal session ID
 *
 * @example
 * ```typescript
 * const sessionId = generateSecureSessionId();
 * // Returns: "a1b2c3d4e5f6...048" (64 hex characters)
 * ```
 */
export function generateSecureSessionId(): string {
  if (runtimeCaps.isNode && runtimeCaps.hasBuffer) {
    // Node.js environment - use crypto.randomBytes
    const bytes = randomBytes(32); // 256 bits
    return bytes.toString('hex');
  } else {
    // Worker/Browser environment - use Web Crypto API
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  }
}

/**
 * Validates a session ID format.
 *
 * Session IDs must be exactly 64 hexadecimal characters (representing 32 bytes).
 * This validation helps prevent injection attacks and ensures consistency.
 *
 * @param sessionId - The session ID to validate
 * @returns True if the session ID has a valid format, false otherwise
 *
 * @example
 * ```typescript
 * validateSessionIdFormat('abc123'); // false - too short
 * validateSessionIdFormat('g1h2...'); // false - invalid hex
 * validateSessionIdFormat('a1b2c3...048'); // true - 64 hex chars
 * ```
 */
export function validateSessionIdFormat(sessionId: string): boolean {
  // Must be exactly 64 hexadecimal characters (32 bytes)
  return /^[a-f0-9]{64}$/.test(sessionId);
}
