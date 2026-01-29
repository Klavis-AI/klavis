import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import type { Express } from 'express';
import { logger } from '../utils/logger.js';
import type { TransportMetrics } from '../../shared/transport-metrics.js';
import { MetricsCounter } from '../../shared/transport-metrics.js';
import type { AppSettings } from '../../shared/settings.js';
import { JsonRpcErrors, extractJsonRpcId } from './json-rpc-errors.js';
import { whoAmI, HubApiError, type WhoAmI } from '@huggingface/hub';
import { extractAuthBouquetAndMix } from '../utils/auth-utils.js';
import { getMetricsSafeName } from '../utils/gradio-metrics.js';
import { isGradioTool } from '../utils/gradio-utils.js';
import { GRADIO_FILES_TOOL_CONFIG } from '@llmindset/hf-mcp';
import { getProxyToolDefinition, type ProxyToolResponseType } from '../utils/proxy-tools-config.js';

/**
 * Result returned by ServerFactory containing the server instance and optional user details
 */
export interface ServerFactoryResult {
	server: McpServer;
	userDetails?: WhoAmI;
	enabledToolIds?: string[];
}

/**
 * Factory function to create server instances
 * This should be provided during transport construction to enable per-connection server instances
 * Returns both the server instance and optional user details from authentication
 */
export type ServerFactory = (
	headers: Record<string, string> | null,
	userSettings?: AppSettings,
	skipGradio?: boolean,
	sessionInfo?: {
		clientSessionId?: string;
		isAuthenticated?: boolean;
		clientInfo?: { name: string; version: string };
	}
) => Promise<ServerFactoryResult>;

export interface TransportOptions {
	port?: number;
	onClientInfoUpdate?: (clientInfo: { name: string; version: string }) => void;
}

/**
 * Standardized session metadata structure for all transports
 */
export interface SessionMetadata {
	id: string;
	connectedAt: Date;
	lastActivity: Date;
	requestCount: number;
	isAuthenticated: boolean;
	clientInfo?: {
		name: string;
		version: string;
	};
	capabilities: {
		sampling?: boolean;
		roots?: boolean;
	};
	pingFailures?: number;
	lastPingAttempt?: Date;
	ipAddress?: string;
	authToken?: string;
}

/**
 * Base session interface that all transport sessions should extend
 * This provides common fields while allowing transport-specific extensions
 */
export interface BaseSession<T = unknown> {
	transport: T;
	server: McpServer;
	metadata: SessionMetadata;
	heartbeatInterval?: NodeJS.Timeout;
	cleaningUp?: boolean;
}

/**
 * Special constant for stateless transports to distinguish from zero active connections
 */
export const STATELESS_MODE = -1;

/**
 * Base class for all transport implementations
 */
export abstract class BaseTransport {
	protected serverFactory: ServerFactory;
	protected app: Express;
	protected metrics: MetricsCounter;

	constructor(serverFactory: ServerFactory, app: Express) {
		this.serverFactory = serverFactory;
		this.app = app;
		this.metrics = new MetricsCounter();
	}

	/**
	 * Initialize the transport with the given options
	 */
	abstract initialize(options: TransportOptions): Promise<void>;

	/**
	 * Clean up the transport resources
	 */
	abstract cleanup(): Promise<void>;

	/**
	 * Mark transport as shutting down
	 * Optional method for transports that need to reject new connections
	 */
	shutdown?(): void;

	/**
	 * Get the number of active connections
	 * Returns -1 (STATELESS_MODE) for stateless transports
	 */
	abstract getActiveConnectionCount(): number;

	/**
	 * Get all active sessions with their metadata
	 * Returns an array of session metadata for connection dashboard
	 */
	getSessions(): SessionMetadata[] {
		return [];
	}

	/**
	 * Get current transport metrics
	 */
	getMetrics(): TransportMetrics {
		return this.metrics.getMetrics();
	}

	/**
	 * Get configuration settings (only relevant for stateful transports)
	 */
	getConfiguration(): {
		heartbeatInterval?: number;
		staleCheckInterval?: number;
		staleTimeout?: number;
		pingEnabled?: boolean;
		pingInterval?: number;
		pingFailureThreshold?: number;
	} {
		return {};
	}

	/**
	 * Track a new request received by the transport
	 */
	protected trackRequest(): void {
		this.metrics.trackRequest();
	}

	/**
	 * Track an error in the transport
	 */
	protected trackError(statusCode?: number, error?: Error): void {
		this.metrics.trackError(statusCode, error);
	}

	/**
	 * Track a new connection established (global counter)
	 */
	protected trackNewConnection(): void {
		this.metrics.trackNewConnection();
	}

	/**
	 * Track an IP address for unique IP metrics
	 */
	protected trackIpAddress(ipAddress: string | undefined): void {
		this.metrics.trackIpAddress(ipAddress);
	}

	/**
	 * Track an IP address for a specific client
	 */
	protected trackClientIpAddress(ipAddress: string | undefined, clientInfo?: { name: string; version: string }): void {
		this.metrics.trackClientIpAddress(ipAddress, clientInfo);
	}

	/**
	 * Track auth status for a specific client
	 */
	protected trackClientAuth(authToken: string | undefined, clientInfo?: { name: string; version: string }): void {
		this.metrics.trackClientAuth(authToken, clientInfo);
	}

	/**
	 * Extract IP address from request headers
	 * Handles x-forwarded-for, x-real-ip, and direct IP
	 */
	protected extractIpAddress(
		headers: Record<string, string | string[] | undefined>,
		directIp?: string
	): string | undefined {
		// Try x-forwarded-for first (most reliable for proxied traffic)
		const forwardedFor = headers['x-forwarded-for'];
		if (forwardedFor) {
			// x-forwarded-for can be a comma-separated list, take the first one (original client)
			const ip = Array.isArray(forwardedFor) ? forwardedFor[0] : forwardedFor;
			return ip?.split(',')[0]?.trim();
		}

		// Try x-real-ip (nginx)
		const realIp = headers['x-real-ip'];
		if (realIp) {
			return Array.isArray(realIp) ? realIp[0] : realIp;
		}

		// Fallback to direct IP (no proxy scenario)
		return directIp;
	}

	/**
	 * Associate a session with a client identity when client info becomes available
	 */
	protected associateSessionWithClient(clientInfo: { name: string; version: string }): void {
		this.metrics.associateSessionWithClient(clientInfo);
	}

	/**
	 * Update client activity when a request is made
	 */
	protected updateClientActivity(clientInfo?: { name: string; version: string }): void {
		this.metrics.updateClientActivity(clientInfo);
	}

	/**
	 * Mark a client connection as disconnected
	 */
	protected disconnectClient(clientInfo?: { name: string; version: string }): void {
		this.metrics.disconnectClient(clientInfo);
	}

	/**
	 * Extract method name from JSON-RPC request body for tracking
	 * Handles special cases for tools/call and prompts/get to include tool/prompt names
	 * Returns null for responses (which should not be tracked as methods)
	 */
	protected extractMethodForTracking(requestBody: unknown): string | null {
		const body = requestBody as
			| { method?: string; params?: { name?: string }; id?: unknown; result?: unknown; error?: unknown }
			| undefined;

		// If this is a JSON-RPC response (has id and result/error but no method), don't track it
		if (body && 'id' in body && !('method' in body)) {
			return null;
		}

		const methodName = body?.method || 'unknown';

		// For tools/call, extract the tool name as well
		if (methodName === 'tools/call' && body?.params && typeof body.params === 'object' && 'name' in body.params) {
			const toolName = body.params.name;
			if (typeof toolName === 'string') {
				// Use utility function to get metrics-safe name
				const safeToolName = getMetricsSafeName(toolName);
				return `tools/call:${safeToolName}`;
			}
		}

		// For prompts/get, extract the prompt name as well
		if (methodName === 'prompts/get' && body?.params && typeof body.params === 'object' && 'name' in body.params) {
			const promptName = body.params.name;
			if (typeof promptName === 'string') {
				return `prompts/get:${promptName}`;
			}
		}

		return methodName;
	}

	/**
	 * Determine if Gradio endpoints should be skipped based on request type
	 * Returns true for initialize requests or non-Gradio tool calls
	 */
	/**
	 * Determines if a request is a tools/call targeting a Gradio endpoint
	 * @param requestBody - The JSON-RPC request body
	 * @returns true if this is a tools/call for a Gradio tool, false otherwise
	 */
	protected isGradioToolCall(requestBody: unknown): boolean {
		const body = requestBody as { method?: string; params?: { name?: string; arguments?: unknown } } | undefined;
		const methodName = body?.method || 'unknown';

		// Check if this is a tools/call with a valid tool name
		if (methodName === 'tools/call' && body?.params && typeof body.params === 'object' && 'name' in body.params) {
			const toolName = body.params.name;
			if (typeof toolName === 'string') {
				// Check for standard Gradio tools (gr<number>_ or grp<number>_)
				if (isGradioTool(toolName)) {
					return true;
				}

				// Special case: dynamic_space with "invoke" operation needs streaming
				if (toolName === 'dynamic_space' && body.params.arguments) {
					const args = body.params.arguments as { operation?: string } | undefined;
					if (args?.operation === 'invoke') {
						return true;
					}
				}
			}
		}

		return false;
	}

	/**
	 * Determines if a request is a tools/call targeting a Streamable HTTP proxy tool
	 * that should respond over SSE (response_type=SSE).
	 */
	protected isStreamableHttpToolCall(requestBody: unknown): boolean {
		const body = requestBody as { method?: string; params?: { name?: string } } | undefined;
		const methodName = body?.method || 'unknown';

		if (methodName === 'tools/call' && body?.params && typeof body.params === 'object' && 'name' in body.params) {
			const toolName = body.params.name;
			if (typeof toolName === 'string') {
				const responseType = this.getStreamableHttpResponseType(toolName);
				return responseType === 'SSE';
			}
		}

		return false;
	}

	private getStreamableHttpResponseType(toolName: string): ProxyToolResponseType | undefined {
		const config = getProxyToolDefinition(toolName);
		if (config) {
			return config.responseType;
		}

		return undefined;
	}

	protected skipGradioSetup(requestBody: unknown): boolean {
		const body = requestBody as { method?: string; params?: { name?: string } } | undefined;

		const methodName = body?.method || 'unknown';

		// Always skip for initialize requests
		if (methodName === 'initialize' || methodName.startsWith('resources/')) {
			return true;
		}

		// For tools/call, check if it's a Gradio tool using the dedicated method
		if (methodName === 'tools/call') {
			const toolName = body?.params?.name;

			// Special case: gradio_files needs Gradio setup (for registration) but not streaming
			if (toolName === GRADIO_FILES_TOOL_CONFIG.name) {
				return false; // Don't skip Gradio setup
			}

			// Return true (skip) for non-Gradio tools, false (don't skip) for Gradio tools
			return !this.isGradioToolCall(requestBody);
		}

		// For other methods, don't skip Gradio (conservative default)
		return false;
	}

	/**
	 * Track a method call with timing and error status
	 */
	protected trackMethodCall(
		methodName: string | null,
		startTime: number,
		isError: boolean = false,
		clientInfo?: { name: string; version: string }
	): void {
		const duration = Date.now() - startTime;
		this.metrics.trackMethod(methodName, duration, isError, clientInfo);
	}

	/**
	 * Extract client info from initialize request parameters
	 * Used by stateless transports to capture client info directly from request
	 * @param requestBody - The request body containing initialize params
	 * @returns Client info if available in the request
	 */
	protected extractClientInfoFromRequest(requestBody: unknown): { name: string; version: string } | undefined {
		const body = requestBody as { method?: string; params?: { clientInfo?: unknown } } | undefined;

		if (body?.method === 'initialize' && body?.params) {
			const clientInfo = body.params.clientInfo as { name?: string; version?: string } | undefined;
			if (clientInfo?.name && clientInfo?.version) {
				return { name: clientInfo.name, version: clientInfo.version };
			}
		}

		return undefined;
	}

	/**
	 * Validate HF token and track authentication metrics
	 * Returns true if request should continue, false if 401 should be returned
	 */
	protected async validateAuthAndTrackMetrics(
		headers: Record<string, string>
	): Promise<{ shouldContinue: boolean; statusCode?: number; userIdentified: boolean }> {
		const { hfToken } = extractAuthBouquetAndMix(headers);

		if (hfToken) {
			try {
				await whoAmI({ credentials: { accessToken: hfToken } });
				// Track authenticated connection
				this.metrics.trackAuthenticatedConnection();
				return { shouldContinue: true, userIdentified: true };
			} catch (error) {
				// Check for 401 status in multiple possible locations
				const errorObj = error as { statusCode?: number; status?: number };
				const isUnauthorized =
					(error instanceof HubApiError && error.statusCode === 401) ||
					errorObj.statusCode === 401 ||
					errorObj.status === 401 ||
					(error instanceof Error && error.message.includes('401')) ||
					(error instanceof TypeError && error.message.includes('Your access token must start with'));

				if (isUnauthorized) {
					logger.debug('Invalid HF token - returning 401');
					// Track unauthorized connection
					this.metrics.trackUnauthorizedConnection();
					return { shouldContinue: false, statusCode: 401, userIdentified: false };
				}
				// For other errors (network issues, 500s, etc.), continue processing
				// but don't track as authenticated since we couldn't validate
				logger.debug({ error }, 'Non-401 error from whoAmI, continuing without auth tracking');
				// Don't track any auth metrics for this case - token exists but validation failed for non-auth reasons
				return { shouldContinue: true, userIdentified: false };
			}
		} else {
			// Track anonymous connection
			this.metrics.trackAnonymousConnection();
			const shouldContinue: boolean = !headers['x-mcp-force-auth'];
			if (!shouldContinue) logger.trace(`NO TOKEN, FORCE AUTH? ${headers['x-mcp-force-auth']}`);
			return { shouldContinue, userIdentified: false };
		}
	}
}

/**
 * Base class for stateful transport implementations that maintain session state
 * Provides common functionality for session management, stale connection detection, and client info tracking
 */
export abstract class StatefulTransport<TSession extends BaseSession = BaseSession> extends BaseTransport {
	protected sessions: Map<string, TSession> = new Map();
	protected isShuttingDown = false;
	protected staleCheckInterval?: NodeJS.Timeout;
	protected pingInterval?: NodeJS.Timeout;
	protected pingsInFlight = new Set<string>();

	// Configuration from environment variables
	protected readonly STALE_CHECK_INTERVAL = parseInt(process.env.MCP_CLIENT_CONNECTION_CHECK || '90000', 10);
	protected readonly STALE_TIMEOUT = parseInt(process.env.MCP_CLIENT_CONNECTION_TIMEOUT || '600000', 10);
	protected readonly HEARTBEAT_INTERVAL = parseInt(process.env.MCP_CLIENT_HEARTBEAT_INTERVAL || '30000', 10);
	protected readonly PING_ENABLED = process.env.MCP_PING_ENABLED !== 'false';
	protected readonly PING_INTERVAL = parseInt(process.env.MCP_PING_INTERVAL || '30000', 10);
	protected readonly PING_FAILURE_THRESHOLD = parseInt(process.env.MCP_PING_FAILURE_THRESHOLD || '1', 10);

	/**
	 * Update the last activity timestamp for a session
	 */
	protected updateSessionActivity(sessionId: string): void {
		const session = this.sessions.get(sessionId);
		if (session) {
			session.metadata.lastActivity = new Date();
			// Update client activity metrics if client info is available
			this.metrics.updateClientActivity(session.metadata.clientInfo);
		}
	}

	/**
	 * Check if a session is distressed (has excessive ping failures)
	 */
	protected isSessionDistressed(session: BaseSession): boolean {
		return (session.metadata.pingFailures || 0) >= this.PING_FAILURE_THRESHOLD;
	}

	/**
	 * Create a standardized client info capture callback for a session
	 */
	protected createClientInfoCapture(sessionId: string): () => void {
		return () => {
			const session = this.sessions.get(sessionId);
			if (session) {
				const clientInfo = session.server.server.getClientVersion();
				const clientCapabilities = session.server.server.getClientCapabilities();

				if (clientInfo) {
					// Disconnect the old client info if it exists
					if (session.metadata.clientInfo) {
						this.metrics.disconnectClient(session.metadata.clientInfo);
					}
					session.metadata.clientInfo = clientInfo;
					// Associate session with real client for metrics tracking
					this.metrics.associateSessionWithClient(clientInfo);

					// Track IP address for this client if available
					if (session.metadata.ipAddress) {
						this.trackClientIpAddress(session.metadata.ipAddress, clientInfo);
					}

					// Track auth status for this client
					this.trackClientAuth(session.metadata.authToken, clientInfo);
				}

				if (clientCapabilities) {
					session.metadata.capabilities = {
						sampling: !!clientCapabilities.sampling,
						roots: !!clientCapabilities.roots,
					};
				}

				logger.debug(
					{
						sessionId,
						clientInfo: session.metadata.clientInfo,
						capabilities: session.metadata.capabilities,
					},
					'Client Initialization Request'
				);
			}
		};
	}

	/**
	 * Send a fire-and-forget ping to a single session
	 * Success updates lastActivity, failures increment failure count
	 */
	protected pingSingleSession(sessionId: string): void {
		const session = this.sessions.get(sessionId);
		if (!session) return;

		// Skip if ping already in progress for this session
		if (this.pingsInFlight.has(sessionId)) {
			return;
		}

		// Mark ping as in-flight and update last ping attempt
		this.pingsInFlight.add(sessionId);
		session.metadata.lastPingAttempt = new Date();

		// Track ping being sent
		this.metrics.trackPingSent();

		// Fire ping and handle result asynchronously
		session.server.server
			.ping()
			.then(() => {
				// SUCCESS: Update lastActivity timestamp and reset ping failures
				// This prevents the stale checker from removing this session
				this.updateSessionActivity(sessionId);
				session.metadata.pingFailures = 0;
				this.metrics.trackPingSuccess();
				logger.trace({ sessionId }, 'Ping succeeded');
			})
			.catch((error: unknown) => {
				// FAILURE: Increment ping failure count
				session.metadata.pingFailures = (session.metadata.pingFailures || 0) + 1;
				const errorMessage = error instanceof Error ? error.message : String(error);
				this.metrics.trackPingFailed();
				logger.trace({ sessionId, error: errorMessage, failures: session.metadata.pingFailures }, 'Ping failed');
			})
			.finally(() => {
				// Always remove from tracking set
				this.pingsInFlight.delete(sessionId);
			});
	}

	/**
	 * Start the ping keep-alive interval
	 */
	protected startPingKeepAlive(): void {
		if (!this.PING_ENABLED) {
			logger.debug('Ping keep-alive disabled');
			return;
		}

		this.pingInterval = setInterval(() => {
			if (this.isShuttingDown) return;

			// Ping all sessions that don't have an active ping
			for (const sessionId of this.sessions.keys()) {
				this.pingSingleSession(sessionId);
			}
		}, this.PING_INTERVAL);

		logger.debug({ pingInterval: this.PING_INTERVAL }, 'Started ping keep-alive');
	}

	/**
	 * Stop the ping keep-alive interval
	 */
	protected stopPingKeepAlive(): void {
		if (this.pingInterval) {
			clearInterval(this.pingInterval);
			this.pingInterval = undefined;
			// Clear any in-flight pings
			this.pingsInFlight.clear();
			logger.debug('Stopped ping keep-alive');
		}
	}

	/**
	 * Start the stale connection check interval
	 */
	protected startStaleConnectionCheck(): void {
		this.staleCheckInterval = setInterval(() => {
			if (this.isShuttingDown) return;

			const now = Date.now();
			const staleSessionIds: string[] = [];

			// Find stale sessions
			for (const [sessionId, session] of this.sessions) {
				const timeSinceActivity = now - session.metadata.lastActivity.getTime();
				if (timeSinceActivity > this.STALE_TIMEOUT) {
					staleSessionIds.push(sessionId);
				}
			}

			// Remove stale sessions
			for (const sessionId of staleSessionIds) {
				const session = this.sessions.get(sessionId);
				if (session) {
					logger.info(
						{ sessionId, timeSinceActivity: now - session.metadata.lastActivity.getTime() },
						'Removing stale session'
					);
					void this.removeStaleSession(sessionId);
				}
			}
		}, this.STALE_CHECK_INTERVAL);
	}

	/**
	 * Remove a stale session - must be implemented by concrete transport
	 */
	protected abstract removeStaleSession(sessionId: string): Promise<void>;

	/**
	 * Mark transport as shutting down
	 */
	override shutdown(): void {
		this.isShuttingDown = true;
	}

	/**
	 * Get the number of active connections
	 */
	override getActiveConnectionCount(): number {
		// Update metrics active connection count
		this.metrics.updateActiveConnections(this.sessions.size);
		return this.sessions.size;
	}

	/**
	 * Check if server is accepting new connections
	 */
	isAcceptingConnections(): boolean {
		return !this.isShuttingDown;
	}

	/**
	 * Stop the stale connection check interval during cleanup
	 */
	protected stopStaleConnectionCheck(): void {
		if (this.staleCheckInterval) {
			clearInterval(this.staleCheckInterval);
			this.staleCheckInterval = undefined;
		}
		this.stopPingKeepAlive();
	}

	/**
	 * Track a new session created (called when session is added to sessions map)
	 */
	protected trackSessionCreated(sessionId: string): void {
		this.trackNewConnection();
		this.metrics.updateActiveConnections(this.sessions.size);
		this.metrics.trackSessionCreated();
		// Track as unknown client initially - will be updated when client info is available
		const session = this.sessions.get(sessionId);
		if (session) {
			session.metadata.clientInfo = { name: 'unknown', version: 'unknown' };
			this.metrics.associateSessionWithClient(session.metadata.clientInfo);
		}
	}

	/**
	 * Track a session that was cleaned up/removed
	 */
	protected trackSessionCleaned(session?: TSession): void {
		this.metrics.trackSessionCleaned();
		this.metrics.trackSessionDeleted();
		this.metrics.updateActiveConnections(this.sessions.size);

		// Disconnect client if we have client info
		if (session?.metadata.clientInfo) {
			this.metrics.disconnectClient(session.metadata.clientInfo);
		}
	}

	/**
	 * Get all active sessions with their metadata
	 */
	override getSessions(): SessionMetadata[] {
		return Array.from(this.sessions.values()).map((session) => session.metadata);
	}

	/**
	 * Get configuration settings for stateful transports
	 */
	override getConfiguration(): {
		heartbeatInterval: number;
		staleCheckInterval: number;
		staleTimeout: number;
		pingEnabled: boolean;
		pingInterval: number;
		pingFailureThreshold: number;
	} {
		return {
			heartbeatInterval: this.HEARTBEAT_INTERVAL,
			staleCheckInterval: this.STALE_CHECK_INTERVAL,
			staleTimeout: this.STALE_TIMEOUT,
			pingEnabled: this.PING_ENABLED,
			pingInterval: this.PING_INTERVAL,
			pingFailureThreshold: this.PING_FAILURE_THRESHOLD,
		};
	}

	/**
	 * Start heartbeat monitoring for a session with SSE response
	 * Automatically detects stale connections and cleans them up
	 */
	protected startHeartbeat(sessionId: string, response: { destroyed: boolean; writableEnded: boolean }): void {
		const session = this.sessions.get(sessionId);
		if (!session) return;

		// Clear any existing heartbeat
		this.stopHeartbeat(sessionId);

		session.heartbeatInterval = setInterval(() => {
			if (response.destroyed || response.writableEnded) {
				logger.debug({ sessionId }, 'Detected stale connection via heartbeat');
				void this.removeStaleSession(sessionId);
			}
		}, this.HEARTBEAT_INTERVAL);
	}

	/**
	 * Stop heartbeat monitoring for a session
	 */
	protected stopHeartbeat(sessionId: string): void {
		const session = this.sessions.get(sessionId);
		if (session?.heartbeatInterval) {
			clearInterval(session.heartbeatInterval);
			session.heartbeatInterval = undefined;
		}
	}

	/**
	 * Set up standard SSE connection event handlers
	 */
	protected setupSseEventHandlers(
		sessionId: string,
		response: { on: (event: string, handler: (...args: unknown[]) => void) => void }
	): void {
		response.on('close', () => {
			logger.info({ sessionId }, 'SSE connection closed by client');
			void this.removeStaleSession(sessionId);
		});

		response.on('error', (...args: unknown[]) => {
			const error = args[0] as Error;
			logger.error({ error, sessionId }, 'SSE connection error');
			this.trackError(500, error);
			void this.removeStaleSession(sessionId);
		});
	}

	/**
	 * Standard session cleanup implementation
	 * Handles stopping heartbeat, closing transport/server, and tracking cleanup
	 */
	protected async cleanupSession(sessionId: string): Promise<void> {
		try {
			const session = this.sessions.get(sessionId);
			if (!session) return;

			// Prevent recursive cleanup
			if (session.cleaningUp) {
				logger.debug({ sessionId }, 'Session already being cleaned up, skipping');
				return;
			}
			session.cleaningUp = true;

			logger.debug({ sessionId }, 'Cleaning up session');

			// Clear heartbeat interval
			this.stopHeartbeat(sessionId);

			// Close transport
			try {
				await (session.transport as { close(): Promise<void> }).close();
			} catch (error) {
				logger.error({ error, sessionId }, 'Error closing transport');
			}

			// Close server
			try {
				await session.server.close();
			} catch (error) {
				logger.error({ error, sessionId }, 'Error closing server');
			}

			// Remove from map and track cleanup
			this.sessions.delete(sessionId);
			this.trackSessionCleaned(session);

			logger.debug({ sessionId }, 'Session cleaned up');
		} catch (error) {
			logger.error({ error, sessionId }, 'Error during session cleanup');
		}
	}

	/**
	 * Clean up all sessions in parallel
	 */
	protected async cleanupAllSessions(): Promise<void> {
		const sessionIds = Array.from(this.sessions.keys());

		const cleanupPromises = sessionIds.map((sessionId) =>
			this.cleanupSession(sessionId).catch((error: unknown) => {
				logger.error({ error, sessionId }, 'Error during session cleanup');
			})
		);

		await Promise.allSettled(cleanupPromises);
		this.sessions.clear();
	}

	/**
	 * Set up standard server configuration for a session
	 * Configures client info capture and error tracking
	 */
	protected setupServerForSession(server: McpServer, sessionId: string): void {
		// Set up client info capture
		server.server.oninitialized = this.createClientInfoCapture(sessionId);

		// Set up error tracking for server errors
		server.server.onerror = (error) => {
			this.trackError(undefined, error);
			logger.error({ error, sessionId }, 'Server error');
		};
	}

	/**
	 * Validate common request conditions and track method calls
	 * Returns validation result with error response if invalid
	 */
	protected validateSessionRequest(
		sessionId: string | undefined,
		requestBody: unknown,
		allowMissingSession: boolean = false
	): { isValid: boolean; errorResponse?: object; statusCode?: number; trackingName: string | null } {
		const trackingName = this.extractMethodForTracking(requestBody);

		// Check if server is shutting down
		if (this.isShuttingDown) {
			this.trackError(503);
			this.metrics.trackMethod(trackingName, undefined, true, undefined);
			return {
				isValid: false,
				errorResponse: JsonRpcErrors.serverShuttingDown(extractJsonRpcId(requestBody)),
				statusCode: 503,
				trackingName,
			};
		}

		// Check session ID requirements
		if (!sessionId && !allowMissingSession) {
			this.trackError(400);
			this.metrics.trackMethod(trackingName, undefined, true, undefined);
			return {
				isValid: false,
				errorResponse: JsonRpcErrors.invalidParams('sessionId is required', extractJsonRpcId(requestBody)),
				statusCode: 400,
				trackingName,
			};
		}

		// Check session existence
		if (sessionId && !this.sessions.has(sessionId)) {
			this.trackError(404);
			this.metrics.trackMethod(trackingName, undefined, true, undefined);
			return {
				isValid: false,
				errorResponse: JsonRpcErrors.sessionNotFound(sessionId, extractJsonRpcId(requestBody)),
				statusCode: 404,
				trackingName,
			};
		}

		return { isValid: true, trackingName };
	}
}
