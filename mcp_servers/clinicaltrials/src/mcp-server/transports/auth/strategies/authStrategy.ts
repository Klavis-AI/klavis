/**
 * @fileoverview Defines the interface for all authentication strategies.
 * This interface establishes a contract for verifying authentication tokens,
 * ensuring that any authentication method (JWT, OAuth, etc.) can be used
 * interchangeably by the core authentication middleware.
 * @module src/mcp-server/transports/auth/strategies/AuthStrategy
 */
import type { AuthInfo } from '@/mcp-server/transports/auth/lib/authTypes.js';

export interface AuthStrategy {
  /**
   * Verifies an authentication token.
   * @param token The raw token string extracted from the request.
   * @returns A promise that resolves with the AuthInfo on successful verification.
   * @throws {McpError} if the token is invalid, expired, or fails verification for any reason.
   */
  verify(token: string): Promise<AuthInfo>;
}
