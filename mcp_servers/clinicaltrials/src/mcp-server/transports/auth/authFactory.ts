/**
 * @fileoverview Factory for creating an authentication strategy based on configuration.
 * This module centralizes the logic for selecting and instantiating the correct
 * authentication strategy, promoting loose coupling and easy extensibility.
 * @module src/mcp-server/transports/auth/authFactory
 */
import { container } from 'tsyringe';

import { config } from '@/config/index.js';
import { logger, requestContextService } from '@/utils/index.js';
import type { AuthStrategy } from '@/mcp-server/transports/auth/strategies/authStrategy.js';
import { JwtStrategy } from '@/mcp-server/transports/auth/strategies/jwtStrategy.js';
import { OauthStrategy } from '@/mcp-server/transports/auth/strategies/oauthStrategy.js';

// Register strategies in the container.
// The container will manage their lifecycle and dependencies.
container.register(JwtStrategy, { useClass: JwtStrategy });
container.register(OauthStrategy, { useClass: OauthStrategy });

/**
 * Creates and returns an authentication strategy instance based on the
 * application's configuration (`config.mcpAuthMode`).
 *
 * @returns An instance of a class that implements the `AuthStrategy` interface,
 *          or `null` if authentication is disabled (`none`).
 * @throws {Error} If the auth mode is unknown or misconfigured.
 */
export function createAuthStrategy(): AuthStrategy | null {
  const context = requestContextService.createRequestContext({
    operation: 'createAuthStrategy',
    authMode: config.mcpAuthMode,
  });
  logger.info('Creating authentication strategy...', context);

  switch (config.mcpAuthMode) {
    case 'jwt':
      logger.debug('Resolving JWT strategy from container.', context);
      return container.resolve(JwtStrategy);
    case 'oauth':
      logger.debug('Resolving OAuth strategy from container.', context);
      return container.resolve(OauthStrategy);
    case 'none':
      logger.info("Authentication is disabled ('none' mode).", context);
      return null; // No authentication
    default:
      // This ensures that if a new auth mode is added to the config type
      // but not to this factory, we get a compile-time or runtime error.
      logger.error(
        `Unknown authentication mode: ${String(config.mcpAuthMode)}`,
        context,
      );
      throw new Error(
        `Unknown authentication mode: ${String(config.mcpAuthMode)}`,
      );
  }
}
