/**
 * @fileoverview Implements the JWT authentication strategy.
 * This module provides a concrete implementation of the AuthStrategy for validating
 * JSON Web Tokens (JWTs). It encapsulates all logic related to JWT verification,
 * including secret key management and payload validation.
 * @module src/mcp-server/transports/auth/strategies/JwtStrategy
 */
import { jwtVerify } from 'jose';
import { injectable, inject } from 'tsyringe';

import { config as ConfigType } from '@/config/index.js';
import { AppConfig, Logger } from '@/container/tokens.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  ErrorHandler,
  logger as LoggerType,
  requestContextService,
} from '@/utils/index.js';
import type { AuthInfo } from '@/mcp-server/transports/auth/lib/authTypes.js';
import type { AuthStrategy } from '@/mcp-server/transports/auth/strategies/authStrategy.js';

@injectable()
export class JwtStrategy implements AuthStrategy {
  private readonly secretKey: Uint8Array | null;
  private readonly env: string;
  private readonly devMcpClientId: string;
  private readonly devMcpScopes: string[];

  constructor(
    @inject(AppConfig) private config: typeof ConfigType,
    @inject(Logger) private logger: typeof LoggerType,
  ) {
    const context = requestContextService.createRequestContext({
      operation: 'JwtStrategy.constructor',
    });
    this.logger.debug('Initializing JwtStrategy...', context);
    this.env = this.config.environment;
    this.devMcpClientId = this.config.devMcpClientId || 'dev-client-id';
    this.devMcpScopes = this.config.devMcpScopes || ['dev-scope'];
    const secretKey = this.config.mcpAuthSecretKey;

    if (this.env === 'production' && !secretKey) {
      this.logger.fatal(
        'CRITICAL: MCP_AUTH_SECRET_KEY is not set in production for JWT auth.',
        context,
      );
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'MCP_AUTH_SECRET_KEY must be set for JWT auth in production.',
        context,
      );
    } else if (!secretKey) {
      this.logger.warning(
        'MCP_AUTH_SECRET_KEY is not set. JWT auth will be bypassed (DEV ONLY).',
        context,
      );
      this.secretKey = null;
    } else {
      this.logger.info('JWT secret key loaded successfully.', context);
      this.secretKey = new TextEncoder().encode(secretKey);
    }
  }

  async verify(token: string): Promise<AuthInfo> {
    const context = requestContextService.createRequestContext({
      operation: 'JwtStrategy.verify',
    });
    this.logger.debug('Attempting to verify JWT.', context);

    // Handle development mode bypass
    if (!this.secretKey) {
      if (this.env !== 'production') {
        this.logger.warning(
          'Bypassing JWT verification: No secret key (DEV ONLY).',
          context,
        );
        return {
          token: 'dev-mode-placeholder-token',
          clientId: this.devMcpClientId,
          scopes: this.devMcpScopes,
        };
      }
      // This path is defensive. The constructor should prevent this state in production.
      this.logger.crit('Auth secret key is missing in production.', context);
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'Auth secret key is missing in production. This indicates a server configuration error.',
        context,
      );
    }

    try {
      const { payload: decoded } = await jwtVerify(token, this.secretKey);
      this.logger.debug('JWT signature verified successfully.', {
        ...context,
        claims: decoded,
      });

      const clientId =
        typeof decoded.cid === 'string'
          ? decoded.cid
          : typeof decoded.client_id === 'string'
            ? decoded.client_id
            : undefined;

      if (!clientId) {
        this.logger.warning(
          "Invalid token: missing 'cid' or 'client_id' claim.",
          context,
        );
        throw new McpError(
          JsonRpcErrorCode.Unauthorized,
          "Invalid token: missing 'cid' or 'client_id' claim.",
          context,
        );
      }

      let scopes: string[] = [];
      if (
        Array.isArray(decoded.scp) &&
        decoded.scp.every((s) => typeof s === 'string')
      ) {
        scopes = decoded.scp;
      } else if (typeof decoded.scope === 'string' && decoded.scope.trim()) {
        scopes = decoded.scope.split(' ').filter(Boolean);
      }

      if (scopes.length === 0) {
        this.logger.warning(
          "Invalid token: missing or empty 'scp' or 'scope' claim.",
          context,
        );
        throw new McpError(
          JsonRpcErrorCode.Unauthorized,
          'Token must contain valid, non-empty scopes.',
          context,
        );
      }

      const tenantId =
        typeof decoded.tid === 'string' ? decoded.tid : undefined;

      const authInfo: AuthInfo = {
        token,
        clientId,
        scopes,
        ...(decoded.sub && { subject: decoded.sub }),
        ...(tenantId && { tenantId }),
      };
      this.logger.info('JWT verification successful.', {
        ...context,
        clientId,
        scopes,
        ...(tenantId ? { tenantId } : {}),
      });
      return authInfo;
    } catch (error) {
      // If the error is already a structured McpError, re-throw it directly.
      if (error instanceof McpError) {
        throw error;
      }

      const message =
        error instanceof Error && error.name === 'JWTExpired'
          ? 'Token has expired.'
          : 'Token verification failed.';

      this.logger.warning(`JWT verification failed: ${message}`, {
        ...context,
        errorName: error instanceof Error ? error.name : 'Unknown',
      });

      throw ErrorHandler.handleError(error, {
        operation: 'JwtStrategy.verify',
        context,
        rethrow: true,
        errorCode: JsonRpcErrorCode.Unauthorized,
        errorMapper: () =>
          new McpError(JsonRpcErrorCode.Unauthorized, message, context),
      });
    }
  }
}
