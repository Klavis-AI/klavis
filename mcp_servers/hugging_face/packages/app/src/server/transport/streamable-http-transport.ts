import { StatefulTransport, type TransportOptions, type BaseSession } from './base-transport.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { randomUUID } from 'node:crypto';
import type { Request, Response } from 'express';
import { logger } from '../utils/logger.js';
import { JsonRpcErrors, extractJsonRpcId } from './json-rpc-errors.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { extractQueryParamsToHeaders } from '../utils/query-params.js';
import { buildOAuthResourceHeader } from '../utils/oauth-resource.js';
import { logSystemEvent } from '../utils/query-logger.js';

interface StreamableHttpConnection extends BaseSession<StreamableHTTPServerTransport> {
	activeResponse?: Response;
}

type Session = StreamableHttpConnection;

export class StreamableHttpTransport extends StatefulTransport<Session> {
	override initialize(_options: TransportOptions): Promise<void> {
		this.setupRoutes();
		this.startStaleConnectionCheck();
		this.startPingKeepAlive();

		logger.info(
			{
				heartbeatInterval: this.HEARTBEAT_INTERVAL,
				staleCheckInterval: this.STALE_CHECK_INTERVAL,
				staleTimeout: this.STALE_TIMEOUT,
				pingEnabled: this.PING_ENABLED,
				pingInterval: this.PING_INTERVAL,
			},
			'StreamableHTTP transport initialized'
		);
		return Promise.resolve();
	}

	private setupRoutes(): void {
		// Initialize new session or handle existing session request
		this.app.post('/mcp', (req, res) => {
			this.trackRequest();
			void (async () => {
				await this.handleRequest(req, res, 'POST');
			})();
		});

		// SSE stream endpoint
		this.app.get('/mcp', (req, res) => {
			this.trackRequest();
			void (async () => {
				await this.handleRequest(req, res, 'GET');
			})();
		});

		// Session termination
		this.app.delete('/mcp', (req, res) => {
			this.trackRequest();
			void (async () => {
				await this.handleRequest(req, res, 'DELETE');
			})();
		});
	}

	private async handleRequest(req: Request, res: Response, method: string): Promise<void> {
		try {
			const sessionId = req.headers['mcp-session-id'] as string;

			// Update activity timestamp for existing sessions
			if (sessionId && this.sessions.has(sessionId)) {
				this.updateSessionActivity(sessionId);
			}

			switch (method) {
				case 'POST':
					await this.handlePostRequest(req, res, sessionId);
					break;
				case 'GET':
					await this.handleGetRequest(req, res, sessionId);
					break;
				case 'DELETE':
					await this.handleDeleteRequest(req, res, sessionId);
					break;
			}
		} catch (error) {
			logger.error({ error, method }, 'Request handling error');
			this.trackError(500, error instanceof Error ? error : new Error(String(error)));
			if (!res.headersSent) {
				res.status(500).json(JsonRpcErrors.internalError(extractJsonRpcId(req.body ?? null)));
			}
		}
	}

	private async handlePostRequest(req: Request, res: Response, sessionId?: string): Promise<void> {
		const trackingName = this.extractMethodForTracking(req.body);

		// Increment request count only for actual method calls (not responses or pings)
		if (trackingName && sessionId && this.sessions.has(sessionId)) {
			const session = this.sessions.get(sessionId);
			if (session) {
				session.metadata.requestCount++;
			}
		}

		try {
			// Reject new connections during shutdown
			if (!sessionId && this.isShuttingDown) {
				this.trackError(503);
				// Track method call without timing (stateful mode measures HTTP dispatch time, not MCP processing time)
				this.metrics.trackMethod(trackingName, undefined, true);
				res.status(503).json(JsonRpcErrors.serverShuttingDown(extractJsonRpcId(req.body)));
				return;
			}

			let transport: StreamableHTTPServerTransport;

			if (sessionId && this.sessions.has(sessionId)) {
				const existingSession = this.sessions.get(sessionId);
				if (!existingSession) {
					this.trackError(404);
					this.metrics.trackMethod(trackingName, undefined, true);
					res.status(404).json(JsonRpcErrors.sessionNotFound(sessionId, extractJsonRpcId(req.body)));
					return;
				}
				transport = existingSession.transport;
			} else if (!sessionId && isInitializeRequest(req.body)) {
				// Create new session only for initialization requests
				const headers = req.headers as Record<string, string>;
				extractQueryParamsToHeaders(req, headers);

				// Check HF token validity before creating session
				const authResult = await this.validateAuthAndTrackMetrics(headers);
				if (!authResult.shouldContinue) {
					this.trackError(authResult.statusCode || 401);
					this.metrics.trackMethod(trackingName, undefined, true);
					res.set('WWW-Authenticate', buildOAuthResourceHeader(req));
					res.status(authResult.statusCode || 401).send('Unauthorized');
					return;
				}

				transport = await this.createSession(headers, req);
			} else if (!sessionId) {
				// No session ID and not an initialization request
				this.trackError(400);
				this.metrics.trackMethod(trackingName, undefined, true);
				res
					.status(400)
					.json(
						JsonRpcErrors.invalidRequest(
							extractJsonRpcId(req.body),
							'Missing session ID for non-initialization request'
						)
					);
				return;
			} else {
				// Invalid session ID
				this.trackError(404);
				this.metrics.trackMethod(trackingName, undefined, true);
				res.status(404).json(JsonRpcErrors.sessionNotFound(sessionId, extractJsonRpcId(req.body)));
				return;
			}

			await transport.handleRequest(req, res, req.body);

			// Track successful method call without timing (stateful mode measures HTTP dispatch time, not MCP processing time)
			this.metrics.trackMethod(trackingName, undefined, false);
		} catch (error) {
			// Track failed method call without timing
			this.metrics.trackMethod(trackingName, undefined, true);
			throw error; // Re-throw to be handled by outer error handler
		}
	}

	private async handleGetRequest(req: Request, res: Response, sessionId?: string): Promise<void> {
		if (!sessionId || !this.sessions.has(sessionId)) {
			this.trackError(400);
			res.status(400).json(JsonRpcErrors.sessionNotFound(sessionId || 'missing', null));
			return;
		}

		logger.trace({ sessionId }, 'Streamable proxy client SSE connected');

		const session = this.sessions.get(sessionId);
		if (!session) {
			this.trackError(404);
			res.status(404).json(JsonRpcErrors.sessionNotFound(sessionId, null));
			return;
		}

		const lastEventId = req.headers['last-event-id'];
		if (lastEventId) {
			logger.warn({ sessionId, lastEventId }, 'Client attempting to result with Last-Event-ID');
		}

		// Store the active response for heartbeat monitoring
		session.activeResponse = res;

		// Set up heartbeat to detect stale SSE connections
		this.startHeartbeat(sessionId, res);

		// Set up connection event handlers
		this.setupSseEventHandlers(sessionId, res);

		await session.transport.handleRequest(req, res);
	}

	private async handleDeleteRequest(req: Request, res: Response, sessionId?: string): Promise<void> {
		if (!sessionId || !this.sessions.has(sessionId)) {
			this.trackError(404);
			res.status(404).json(JsonRpcErrors.sessionNotFound(sessionId || 'missing', extractJsonRpcId(req.body)));
			return;
		}

		logger.info({ sessionId }, 'Session termination requested');

		const session = this.sessions.get(sessionId);
		if (!session) {
			this.trackError(404);
			res.status(404).json(JsonRpcErrors.sessionNotFound(sessionId, extractJsonRpcId(req.body)));
			return;
		}

		await session.transport.handleRequest(req, res, req.body);
		await this.removeSession(sessionId);
	}

	private async createSession(requestHeaders?: Record<string, string>, req?: Request): Promise<StreamableHTTPServerTransport> {
		// Create server instance using factory with request headers
		// Note: Auth validation is now done in handlePostRequest before calling this method
		const result = await this.serverFactory(requestHeaders || null);
		const server = result.server;

		// Extract IP address and auth token for tracking
		const ipAddress = req ? this.extractIpAddress(req.headers as Record<string, string | string[] | undefined>, req.ip) : undefined;
		const authToken = requestHeaders?.['authorization']?.replace(/^Bearer\s+/i, '');

		const transport = new StreamableHTTPServerTransport({
			sessionIdGenerator: () => randomUUID(),
			onsessioninitialized: (sessionId: string) => {
				logger.info({ sessionId }, 'Session initialized');

				// Log system initialize event
				logSystemEvent('initialize', sessionId, {
					clientSessionId: sessionId,
					isAuthenticated: !!requestHeaders?.['authorization'],
					ipAddress,
				});

				// Create session object and store it immediately
				const session: Session = {
					transport,
					server,
					metadata: {
						id: sessionId,
						connectedAt: new Date(),
						lastActivity: new Date(),
						requestCount: 0,
						isAuthenticated: !!requestHeaders?.['authorization'],
						capabilities: {},
						ipAddress,
						authToken,
					},
					cleaningUp: false,
				};

				this.sessions.set(sessionId, session);
				// Track the session creation for metrics
				this.trackSessionCreated(sessionId);
			},
		});

		// Set up cleanup on transport close
		transport.onclose = () => {
			const sessionId = transport.sessionId;
			if (sessionId && this.sessions.has(sessionId)) {
				logger.debug({ sessionId }, 'Transport closed, cleaning up session');
				void this.removeSession(sessionId);
			}
		};

		// Set up error tracking for server errors
		server.server.onerror = (error) => {
			this.trackError(undefined, error);
			logger.error({ error, sessionId: transport.sessionId }, 'StreamableHTTP server error');
		};

		// Set up client info capture when initialized
		server.server.oninitialized = () => {
			const sessionId = transport.sessionId;
			if (sessionId) {
				this.createClientInfoCapture(sessionId)();
			}
		};

		// Connect to session-specific server
		await server.connect(transport);

		return transport;
	}

	private async removeSession(sessionId: string): Promise<void> {
		await this.cleanupSession(sessionId);
		logSystemEvent('session_delete', sessionId, {
			clientSessionId: sessionId,
		});
	}

	/**
	 * Remove a stale session - implementation for StatefulTransport
	 */
	protected override async removeStaleSession(sessionId: string): Promise<void> {
		await this.cleanupSession(sessionId);
	}

	override async cleanup(): Promise<void> {
		// Stop stale checker using base class helper
		this.stopStaleConnectionCheck();

		// Use base class cleanup method
		await this.cleanupAllSessions();

		logger.info('StreamableHTTP transport cleanup complete');
	}
}
