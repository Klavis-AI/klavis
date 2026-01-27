/**
 * @fileoverview Barrel file for the auth module.
 * Exports core utilities and middleware strategies for easier imports.
 * @module src/mcp-server/transports/auth/index
 */

export { authContext } from './lib/authContext.js';
export { withRequiredScopes } from './lib/authUtils.js';
export type { AuthInfo } from './lib/authTypes.js';

export { createAuthStrategy } from './authFactory.js';
export { createAuthMiddleware } from './authMiddleware.js';
export type { AuthStrategy } from './strategies/authStrategy.js';
export { JwtStrategy } from './strategies/jwtStrategy.js';
export { OauthStrategy } from './strategies/oauthStrategy.js';
