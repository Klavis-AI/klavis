/**
 * Supported transport protocol types.
 *
 * - `stdio`: Uses stdin/stdout for communication (default for CLI usage).
 * - `http`: Uses HTTP/SSE for communication (for web-based clients).
 */
export type TransportType = "stdio" | "http";

/**
 * Request payload size limits in bytes for different transport protocols.
 *
 * These limits represent the maximum size of the JSON-RPC request body that can be
 * sent to the MCP server.
 *
 * - `stdio`: Uses stdin/stdout with no inherent protocol limit. The limit is effectively
 *   determined by system memory and buffer sizes. We advertise a conservative 50 MiB limit
 *   but this is **informational only** - not enforced at the transport level.
 *
 * - `http`: Uses Express.js with the body-parser limit configured to 100 KB for JSON payloads.
 *   Note: Express's `bytes` library uses binary (1 KB = 1024 bytes).
 *   This value is **explicitly enforced** via `express.json({ limit })` in the HTTP transport.
 *   Requests exceeding this limit will be rejected with HTTP 413 Payload Too Large.
 *
 * @remarks
 * These values are exposed in each tool's `_meta` field as `com.mongodb/maxRequestPayloadBytes`
 * to inform LLMs about the size constraints when constructing tool call arguments.
 */
export const TRANSPORT_PAYLOAD_LIMITS: Record<TransportType, number> = {
    /** Advertised limit for stdio transport (50 MiB - informational, not enforced) */
    stdio: 50 * 1024 * 1024,
    /** Enforced limit for HTTP transport configured in Express middleware) */
    http: 100 * 1024,
} as const;
