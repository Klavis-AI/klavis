/**
 * @fileoverview Shared types for authentication middleware.
 * @module src/mcp-server/transports/auth/core/auth.types
 */
import type { AuthInfo as SdkAuthInfo } from '@modelcontextprotocol/sdk/server/auth/types.js';

/**
 * Defines the structure for authentication information derived from a token.
 * It extends the base SDK type to include common optional claims.
 */
export type AuthInfo = SdkAuthInfo & {
  subject?: string;
  /** The unique identifier for the tenant associated with this authentication context. */
  tenantId?: string;
};

// The declaration for `http.IncomingMessage` is no longer needed here,
// as the new architecture avoids direct mutation where possible and handles
// the attachment within the Hono context.