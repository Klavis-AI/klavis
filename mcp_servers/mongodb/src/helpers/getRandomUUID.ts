import { UUID } from "bson";
/**
 * Generates a random UUID that works in both Node.js and browser environments.
 * Attempts to use Node.js crypto first, then falls back to Web Crypto API.
 */
export function getRandomUUID(): string {
    try {
        // Try Node.js crypto module first
        // Using require to avoid import errors in browser environments
        // eslint-disable-next-line @typescript-eslint/no-require-imports, @typescript-eslint/consistent-type-imports
        const nodeCrypto = require("crypto") as typeof import("crypto");
        return nodeCrypto.randomUUID();
    } catch {
        // Fall back to Web Crypto API (available in browsers and modern Node.js)
        if (
            typeof globalThis !== "undefined" &&
            globalThis.crypto &&
            typeof globalThis.crypto.randomUUID === "function"
        ) {
            return globalThis.crypto.randomUUID();
        }

        // If neither is available, use the BSON UUID
        return new UUID().toString();
    }
}
