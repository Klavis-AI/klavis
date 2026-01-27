/**
 * @fileoverview Simple in-memory session store for MCP HTTP transport.
 * Implements session management as per MCP Spec 2025-06-18.
 * @see {@link https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#session-management | MCP Session Management}
 * @module src/mcp-server/transports/http/sessionStore
 */

import { validateSessionIdFormat } from '@/mcp-server/transports/http/sessionIdUtils.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, requestContextService } from '@/utils/index.js';

/**
 * Identity information for binding sessions to authenticated users.
 * Used to prevent session hijacking across tenants/clients.
 */
export interface SessionIdentity {
  /** Tenant ID from JWT 'tid' claim */
  tenantId?: string;
  /** Client ID from JWT 'cid'/'client_id' claim */
  clientId?: string;
  /** Subject from JWT 'sub' claim */
  subject?: string;
}

/**
 * Represents a stateful MCP session with identity binding.
 * Sessions are bound to the authenticated identity to prevent hijacking.
 */
interface Session {
  id: string;
  createdAt: Date;
  lastAccessedAt: Date;

  // Identity binding for security
  tenantId?: string;
  clientId?: string;
  subject?: string;
}

/**
 * Simple in-memory session store for stateful MCP sessions.
 * In production, consider using Redis or another persistent store.
 */
export class SessionStore {
  private sessions: Map<string, Session> = new Map();
  private staleTimeout: number;

  constructor(staleTimeoutMs: number) {
    this.staleTimeout = staleTimeoutMs;
    // Clean up stale sessions every minute
    setInterval(() => this.cleanupStaleSessions(), 60_000);
  }

  /**
   * Creates or retrieves a session with optional identity binding.
   * If identity is provided, binds the session to prevent cross-tenant/client hijacking.
   *
   * @param sessionId - The session identifier
   * @param identity - Optional identity info (tenantId, clientId, subject)
   * @returns The session object
   * @throws {McpError} If session ID format is invalid
   */
  getOrCreate(sessionId: string, identity?: SessionIdentity): Session {
    // Validate session ID format to prevent injection attacks
    if (!validateSessionIdFormat(sessionId)) {
      const context = requestContextService.createRequestContext({
        operation: 'SessionStore.getOrCreate',
        sessionIdPrefix: sessionId.substring(0, 16),
      });
      logger.warning('Invalid session ID format rejected', context);
      throw new McpError(
        JsonRpcErrorCode.InvalidParams,
        'Invalid session ID format. Session IDs must be 64 hexadecimal characters.',
        context,
      );
    }

    let session = this.sessions.get(sessionId);

    if (!session) {
      // Build session object conditionally to satisfy exactOptionalPropertyTypes
      const newSession: Session = {
        id: sessionId,
        createdAt: new Date(),
        lastAccessedAt: new Date(),
      };

      // Only set identity fields if they have actual values (not undefined)
      if (identity?.tenantId) newSession.tenantId = identity.tenantId;
      if (identity?.clientId) newSession.clientId = identity.clientId;
      if (identity?.subject) newSession.subject = identity.subject;

      session = newSession;
      this.sessions.set(sessionId, session);
      const context = requestContextService.createRequestContext({
        operation: 'SessionStore.create',
        sessionId,
        tenantId: identity?.tenantId,
      });
      logger.debug('Session created with identity binding', context);
    } else {
      session.lastAccessedAt = new Date();

      // Bind identity on first authenticated request (lazy binding)
      // This handles sessions created before authentication
      if (identity && !session.tenantId) {
        if (identity.tenantId) session.tenantId = identity.tenantId;
        if (identity.clientId) session.clientId = identity.clientId;
        if (identity.subject) session.subject = identity.subject;
        const context = requestContextService.createRequestContext({
          operation: 'SessionStore.bindIdentity',
          sessionId,
          tenantId: identity.tenantId,
        });
        logger.debug(
          'Session identity bound on authenticated request',
          context,
        );
      }
    }

    return session;
  }

  /**
   * Validates a session with identity binding checks.
   * Prevents session hijacking by verifying the session belongs to the requesting identity.
   *
   * Security checks:
   * 1. Session existence
   * 2. Staleness timeout
   * 3. Tenant ID match (if session has tenantId)
   * 4. Client ID match (if session has clientId)
   *
   * @param sessionId - The session identifier
   * @param identity - The identity to validate against (from auth)
   * @returns True if session is valid and matches identity
   */
  isValidForIdentity(sessionId: string, identity?: SessionIdentity): boolean {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }

    // Check staleness
    const isStale =
      Date.now() - session.lastAccessedAt.getTime() > this.staleTimeout;
    if (isStale) {
      this.terminate(sessionId);
      return false;
    }

    // If session has no identity bound, allow (backwards compatibility / no-auth mode)
    if (!session.tenantId && !session.clientId) {
      return true;
    }

    // If request has no identity but session does, reject (security: session was authenticated)
    if (!identity) {
      const context = requestContextService.createRequestContext({
        operation: 'SessionStore.isValidForIdentity',
        sessionId,
      });
      logger.warning(
        'Session requires authentication but request has no identity',
        context,
      );
      return false;
    }

    // Verify tenant ID match
    if (session.tenantId && identity.tenantId) {
      if (session.tenantId !== identity.tenantId) {
        const context = requestContextService.createRequestContext({
          operation: 'SessionStore.isValidForIdentity',
          sessionId,
        });
        logger.warning('Session tenant mismatch - possible hijacking attempt', {
          ...context,
          sessionTenant: session.tenantId,
          requestTenant: identity.tenantId,
        });
        return false;
      }
    }

    // Verify client ID match
    if (session.clientId && identity.clientId) {
      if (session.clientId !== identity.clientId) {
        const context = requestContextService.createRequestContext({
          operation: 'SessionStore.isValidForIdentity',
          sessionId,
        });
        logger.warning('Session client mismatch - possible hijacking attempt', {
          ...context,
          sessionClient: session.clientId,
          requestClient: identity.clientId,
        });
        return false;
      }
    }

    return true;
  }

  /**
   * Terminates a session.
   * @param sessionId - The session identifier
   */
  terminate(sessionId: string): void {
    const deleted = this.sessions.delete(sessionId);
    if (deleted) {
      const context = requestContextService.createRequestContext({
        operation: 'SessionStore.terminate',
        sessionId,
      });
      logger.info('Session terminated', context);
    }
  }

  /**
   * Cleans up stale sessions that haven't been accessed recently.
   */
  private cleanupStaleSessions(): void {
    const now = Date.now();
    let cleanedCount = 0;

    for (const [id, session] of this.sessions.entries()) {
      if (now - session.lastAccessedAt.getTime() > this.staleTimeout) {
        this.sessions.delete(id);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      const context = requestContextService.createRequestContext({
        operation: 'SessionStore.cleanup',
      });
      logger.debug('Cleaned up stale sessions', {
        ...context,
        count: cleanedCount,
      });
    }
  }

  /**
   * Gets the current number of active sessions.
   * @returns The number of sessions
   */
  getSessionCount(): number {
    return this.sessions.size;
  }
}
