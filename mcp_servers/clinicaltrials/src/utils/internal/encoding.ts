/**
 * @fileoverview Provides cross-platform encoding utilities.
 * @module src/utils/internal/encoding
 */
import { runtimeCaps } from './runtime.js';

/**
 * Encodes an ArrayBuffer into a base64 string in a cross-platform manner.
 * Prefers Node.js Buffer for performance if available, otherwise uses a
 * standard web API fallback.
 *
 * @param buffer - The ArrayBuffer to encode.
 * @returns The base64-encoded string.
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  if (runtimeCaps.hasBuffer) {
    // Node.js environment
    return Buffer.from(buffer).toString('base64');
  } else {
    // Browser/Worker environment
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]!);
    }
    return btoa(binary);
  }
}

/**
 * Encodes a string to base64 in a cross-platform manner.
 * Prefers Node.js Buffer for performance if available, otherwise uses
 * TextEncoder with Web APIs for compatibility with Cloudflare Workers.
 *
 * @param str - The string to encode.
 * @returns The base64-encoded string.
 */
export function stringToBase64(str: string): string {
  if (runtimeCaps.hasBuffer) {
    // Node.js environment - most performant
    return Buffer.from(str, 'utf-8').toString('base64');
  } else {
    // Worker/Browser environment - use Web APIs
    const encoder = new TextEncoder();
    const bytes = encoder.encode(str);
    return arrayBufferToBase64(bytes.buffer as ArrayBuffer);
  }
}

/**
 * Decodes a base64 string to UTF-8 in a cross-platform manner.
 * Prefers Node.js Buffer for performance if available, otherwise uses
 * Web APIs (atob + TextDecoder) for compatibility with Cloudflare Workers.
 *
 * @param base64 - The base64 string to decode.
 * @returns The decoded UTF-8 string.
 * @throws {Error} If the input is not valid base64.
 */
export function base64ToString(base64: string): string {
  if (runtimeCaps.hasBuffer) {
    // Node.js environment - most performant
    return Buffer.from(base64, 'base64').toString('utf-8');
  } else {
    // Worker/Browser environment - use Web APIs
    const decoded = atob(base64);
    const decoder = new TextDecoder();
    const bytes = new Uint8Array(decoded.split('').map((c) => c.charCodeAt(0)));
    return decoder.decode(bytes);
  }
}
