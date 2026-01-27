/**
 * @fileoverview Implements the OAuth 2.1 authentication strategy.
 * This module provides a concrete implementation of the AuthStrategy for validating
 * JWTs against a remote JSON Web Key Set (JWKS), as is common in OAuth 2.1 flows.
 * @module src/mcp-server/transports/auth/strategies/OauthStrategy
 */
import { type JWTVerifyResult, createRemoteJWKSet, jwtVerify } from 'jose';
import { inject, injectable } from 'tsyringe';

import { type config as ConfigType } from '@/config/index.js';
import { AppConfig, Logger } from '@/container/tokens.js';
import type { AuthInfo } from '@/mcp-server/transports/auth/lib/authTypes.js';
import type { AuthStrategy } from '@/mcp-server/transports/auth/strategies/authStrategy.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  ErrorHandler,
  type logger as LoggerType,
  requestContextService,
} from '@/utils/index.js';

@injectable()
export class OauthStrategy implements AuthStrategy {
  private readonly jwks: ReturnType<typeof createRemoteJWKSet>;

  constructor(
    @inject(AppConfig) private config: typeof ConfigType,
    @inject(Logger) private logger: typeof LoggerType,
  ) {
    const context = requestContextService.createRequestContext({
      operation: 'OauthStrategy.constructor',
    });
    this.logger.debug('Initializing OauthStrategy...', context);

    if (this.config.mcpAuthMode !== 'oauth') {
      // This check is for internal consistency, so a standard Error is acceptable here.
      throw new Error('OauthStrategy instantiated for non-oauth auth mode.');
    }
    if (!this.config.oauthIssuerUrl || !this.config.oauthAudience) {
      this.logger.fatal(
        'CRITICAL: OAUTH_ISSUER_URL and OAUTH_AUDIENCE must be set for OAuth mode.',
        context,
      );
      // This is a user-facing configuration error, so McpError is appropriate.
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'OAUTH_ISSUER_URL and OAUTH_AUDIENCE must be set for OAuth mode.',
        context,
      );
    }

    try {
      const jwksUrl = new URL(
        this.config.oauthJwksUri ||
          `${this.config.oauthIssuerUrl.replace(
            /\/$/,
            '',
          )}/.well-known/jwks.json`,
      );
      this.jwks = createRemoteJWKSet(jwksUrl, {
        cooldownDuration: this.config.oauthJwksCooldownMs,
        timeoutDuration: this.config.oauthJwksTimeoutMs,
      });
      this.logger.info(
        `JWKS client initialized for URL: ${jwksUrl.href}`,
        context,
      );
    } catch (error) {
      this.logger.fatal('Failed to initialize JWKS client.', {
        ...context,
        error: error instanceof Error ? error.message : String(error),
      });
      // This is a critical startup failure, so a specific McpError is warranted.
      throw new McpError(
        JsonRpcErrorCode.ServiceUnavailable,
        'Could not initialize JWKS client for OAuth strategy.',
        {
          ...context,
          originalError: error instanceof Error ? error.message : 'Unknown',
        },
      );
    }
  }

  async verify(token: string): Promise<AuthInfo> {
    const context = requestContextService.createRequestContext({
      operation: 'OauthStrategy.verify',
    });
    this.logger.debug('Attempting to verify OAuth token via JWKS.', context);

    try {
      const { payload }: JWTVerifyResult = await jwtVerify(token, this.jwks, {
        issuer: this.config.oauthIssuerUrl!,
        audience: this.config.oauthAudience!,
      });
      this.logger.debug('OAuth token signature verified successfully.', {
        ...context,
        claims: payload,
      });

      // RFC 8707 Resource Indicators validation (MCP 2025-06-18 requirement)
      // Validate that the token was issued for this specific MCP server
      if (this.config.mcpServerResourceIdentifier) {
        const resourceClaim = payload.resource || payload.aud;
        const expectedResource = this.config.mcpServerResourceIdentifier;

        const isResourceValid =
          (Array.isArray(resourceClaim) &&
            resourceClaim.includes(expectedResource)) ||
          resourceClaim === expectedResource;

        if (!isResourceValid) {
          this.logger.warning(
            'Token resource indicator mismatch. Token was not issued for this MCP server.',
            {
              ...context,
              expected: expectedResource,
              received: resourceClaim,
            },
          );
          throw new McpError(
            JsonRpcErrorCode.Forbidden,
            'Token was not issued for this MCP server. Resource indicator mismatch.',
            {
              expected: expectedResource,
              received: resourceClaim,
            },
          );
        }

        this.logger.debug(
          'RFC 8707 resource indicator validated successfully.',
          {
            ...context,
            resource: expectedResource,
          },
        );
      }

      const scopes =
        typeof payload.scope === 'string' ? payload.scope.split(' ') : [];
      if (scopes.length === 0) {
        this.logger.warning(
          "Invalid token: missing or empty 'scope' claim.",
          context,
        );
        throw new McpError(
          JsonRpcErrorCode.Unauthorized,
          'Token must contain valid, non-empty scopes.',
          context,
        );
      }

      const clientId =
        typeof payload.client_id === 'string' ? payload.client_id : undefined;
      if (!clientId) {
        this.logger.warning(
          "Invalid token: missing 'client_id' claim.",
          context,
        );
        throw new McpError(
          JsonRpcErrorCode.Unauthorized,
          "Token must contain a 'client_id' claim.",
          context,
        );
      }

      const subject = typeof payload.sub === 'string' ? payload.sub : undefined;
      const tenantId =
        typeof payload.tid === 'string' ? payload.tid : undefined;
      const authInfo: AuthInfo = {
        token,
        clientId,
        scopes,
        ...(subject && { subject }),
        ...(tenantId && { tenantId }),
      };
      this.logger.info('OAuth token verification successful.', {
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
          : 'OAuth token verification failed.';

      this.logger.warning(`OAuth token verification failed: ${message}`, {
        ...context,
        errorName: error instanceof Error ? error.name : 'Unknown',
      });

      // For all other errors, use the ErrorHandler to wrap them.
      throw ErrorHandler.handleError(error, {
        operation: 'OauthStrategy.verify',
        context,
        rethrow: true,
        errorCode: JsonRpcErrorCode.Unauthorized,
        errorMapper: () =>
          new McpError(JsonRpcErrorCode.Unauthorized, message, context),
      });
    }
  }
}
