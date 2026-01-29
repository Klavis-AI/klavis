import { createHash } from 'node:crypto';
import type { TransportType } from './constants.js';

/**
 * Core metrics data tracked by each transport
 */
export interface TransportMetrics {
	startupTime: Date;

	// Connection metrics
	connections: {
		active: number | 'stateless';
		total: number;
		authenticated: number;
		denied: number;
		anonymous: number;
		unauthorized?: number; // 401 errors
		cleaned?: number; // Only for stateful transports
		uniqueIps?: number; // Unique IP addresses that have connected
	};

	// Session lifecycle metrics (only for stateful transports)
	sessions?: {
		created: number;
		resumedFailed: number;
		deleted: number;
	};

	// Request metrics
	requests: {
		total: number;
		averagePerMinute: number;
		lastMinute: number;
		lastHour: number;
		last3Hours: number;
	};

	// Ping metrics (for stateful transports)
	pings?: {
		sent: number;
		successful: number;
		failed: number;
		lastPingTime?: Date;
	};

	// Error metrics
	errors: {
		expected: number; // 4xx errors
		unexpected: number; // 5xx errors
		lastError?: {
			type: string;
			message: string;
			timestamp: Date;
		};
	};

	// Client identity aggregation (name version)
	clients: Map<string, ClientMetrics>;

	// Method metrics
	methods: Map<string, MethodMetrics>;

	// Static page hits (for stateless transport)
	staticPageHits200?: number;
	staticPageHits405?: number;
}

/**
 * Metrics per client identity (name@version)
 */
export interface ClientMetrics {
	name: string;
	version: string;
	requestCount: number;
	firstSeen: Date;
	lastSeen: Date;
	isConnected: boolean;
	activeConnections: number;
	totalConnections: number;
	toolCallCount: number;
	newIpCount: number;
	anonCount: number;
	uniqueAuthCount: number;
}

/**
 * Metrics per client for a specific method
 */
export interface ClientMethodMetrics {
	clientName: string;
	count: number;
}

/**
 * Metrics per MCP method
 */
export interface MethodMetrics {
	method: string;
	count: number;
	firstCalled: Date;
	lastCalled: Date;
	averageResponseTime?: number;
	errors: number;
	byClient: Map<string, ClientMethodMetrics>;
}

/**
 * API call metrics for external HuggingFace API calls
 */
export interface ApiCallMetrics {
	anonymous: number;
	authenticated: number;
	unauthorized: number; // 401
	forbidden: number; // 403
}

/**
 * Gradio tool call metrics
 */
export interface GradioToolMetrics {
	success: number;
	failure: number;
	byTool: Record<string, { success: number; failure: number }>;
}

/**
 * Gradio cache metrics for space metadata and schemas
 */
export interface GradioCacheMetrics {
	spaceMetadata: {
		hits: number;
		misses: number;
		hitRate: number; // percentage
		etagRevalidations: number;
		cacheSize: number;
	};
	schemas: {
		hits: number;
		misses: number;
		hitRate: number; // percentage
		cacheSize: number;
	};
	totalHits: number;
	totalMisses: number;
	overallHitRate: number; // percentage
}

/**
 * API response format for transport metrics
 */
export interface SessionData {
	id: string;
	connectedAt: string; // ISO date string
	lastActivity: string; // ISO date string
	clientInfo?: {
		name: string;
		version: string;
	};
	isConnected: boolean;
	connectionStatus?: 'Connected' | 'Distressed' | 'Disconnected';
	pingFailures?: number;
	lastPingAttempt?: string; // ISO date string
	ipAddress?: string;
}

export interface TransportMetricsResponse {
	transport: TransportType;
	isStateless: boolean;
	startupTime: string; // ISO date string
	currentTime: string; // ISO date string
	uptimeSeconds: number;

	// Configuration settings (only for stateful transports)
	configuration?: {
		heartbeatInterval: number; // milliseconds
		staleCheckInterval: number; // milliseconds
		staleTimeout: number; // milliseconds
		pingEnabled?: boolean;
		pingInterval?: number; // milliseconds
		pingFailureThreshold?: number; // number of failed pings before distressed
	};

	connections: {
		active: number | 'stateless';
		total: number;
		cleaned?: number;
	};

	// Session lifecycle metrics (only for stateful transports)
	sessionLifecycle?: {
		created: number;
		resumedFailed: number;
		deleted: number;
	};

	requests: {
		total: number;
		averagePerMinute: number;
		lastMinute: number;
		lastHour: number;
		last3Hours: number;
	};

	// Static page hits (stateless transport only)
	staticPageHits200?: number;
	staticPageHits405?: number;

	pings?: {
		sent: number;
		successful: number;
		failed: number;
		lastPingTime?: string; // ISO date string
	};

	errors: {
		expected: number;
		unexpected: number;
		lastError?: {
			type: string;
			message: string;
			timestamp: string; // ISO date string
		};
	};

	clients: Array<{
		name: string;
		version: string;
		requestCount: number;
		firstSeen: string; // ISO date string
		lastSeen: string; // ISO date string
		isConnected: boolean;
		activeConnections: number;
		totalConnections: number;
		toolCallCount: number;
		newIpCount: number;
		anonCount: number;
		uniqueAuthCount: number;
	}>;

	sessions: SessionData[];

	methods: Array<{
		method: string;
		count: number;
		firstCalled: string; // ISO date string
		lastCalled: string; // ISO date string
		averageResponseTime?: number; // milliseconds
		errors: number;
		errorRate: number; // percentage
		byClient: Array<{
			clientName: string;
			count: number;
		}>;
	}>;

	// API call metrics (only shown in external API mode)
	apiMetrics?: ApiCallMetrics;

	// Gradio tool call metrics
	gradioMetrics?: GradioToolMetrics;

	// Gradio cache metrics (discovery optimization)
	gradioCacheMetrics?: GradioCacheMetrics;
}

/**
 * Convert internal metrics to API response format
 */
export function formatMetricsForAPI(
	metrics: TransportMetrics,
	transport: TransportType,
	isStateless: boolean,
	sessions: SessionData[] = []
): TransportMetricsResponse {
	const currentTime = new Date();
	const uptimeSeconds = Math.floor((currentTime.getTime() - metrics.startupTime.getTime()) / 1000);

	return {
		transport,
		isStateless,
		startupTime: metrics.startupTime.toISOString(),
		currentTime: currentTime.toISOString(),
		uptimeSeconds,
		connections: metrics.connections,
		sessionLifecycle: metrics.sessions,
		requests: metrics.requests,
		pings: metrics.pings
			? {
					...metrics.pings,
					lastPingTime: metrics.pings.lastPingTime?.toISOString(),
				}
			: undefined,
		errors: {
			...metrics.errors,
			lastError: metrics.errors.lastError
				? {
						...metrics.errors.lastError,
						timestamp: metrics.errors.lastError.timestamp.toISOString(),
					}
				: undefined,
		},
		clients: Array.from(metrics.clients.values()).map((client) => ({
			...client,
			firstSeen: client.firstSeen.toISOString(),
			lastSeen: client.lastSeen.toISOString(),
		})),
		sessions,
		staticPageHits200: metrics.staticPageHits200,
		staticPageHits405: metrics.staticPageHits405,
		methods: Array.from(metrics.methods.values()).map((method) => ({
			...method,
			firstCalled: method.firstCalled.toISOString(),
			lastCalled: method.lastCalled.toISOString(),
			errorRate: method.count > 0 ? (method.errors / method.count) * 100 : 0,
			byClient: Array.from(method.byClient.values()).map((client) => ({
				clientName: client.clientName,
				count: client.count,
			})),
		})),
	};
}

/**
 * Check if a method name is an initialization request
 */
export function isInitializeRequest(method: string): boolean {
	return method === 'initialize';
}

/**
 * Create a new empty metrics object
 */
export function createEmptyMetrics(): TransportMetrics {
	return {
		startupTime: new Date(),
		connections: {
			active: 0,
			total: 0,
			authenticated: 0,
			denied: 0,
			anonymous: 0,
		},
		sessions: {
			created: 0,
			resumedFailed: 0,
			deleted: 0,
		},
		requests: {
			total: 0,
			averagePerMinute: 0,
			lastMinute: 0,
			lastHour: 0,
			last3Hours: 0,
		},
		errors: {
			expected: 0,
			unexpected: 0,
		},
		clients: new Map(),
		methods: new Map(),
		staticPageHits200: 0,
		staticPageHits405: 0,
	};
}

/**
 * Get client identity key from name and version
 */
export function getClientKey(name: string, version: string): string {
	return `${name} ${version}`;
}

/**
 * Rolling window counter for tracking metrics over time periods
 */
class RollingWindowCounter {
	private readonly buckets: number[];
	private currentBucket: number = 0;
	private lastRotation: number = Date.now();
	
	constructor(windowMinutes: number) {
		this.buckets = new Array(windowMinutes).fill(0);
	}
	
	increment(): void {
		this.rotateBucketsIfNeeded();
		const current = this.buckets[this.currentBucket] ?? 0;
		this.buckets[this.currentBucket] = current + 1;
	}
	
	getCount(): number {
		this.rotateBucketsIfNeeded();
		return this.buckets.reduce((sum, count) => sum + count, 0);
	}
	
	private rotateBucketsIfNeeded(): void {
		const now = Date.now();
		const minutesPassed = Math.floor((now - this.lastRotation) / 60000);
		
		// Rotate and clear buckets for each minute that has passed
		for (let i = 0; i < minutesPassed && i < this.buckets.length; i++) {
			this.currentBucket = (this.currentBucket + 1) % this.buckets.length;
			this.buckets[this.currentBucket] = 0;
		}
		
		// If all buckets need to be cleared (time gap > window size)
		if (minutesPassed >= this.buckets.length) {
			this.buckets.fill(0);
			this.currentBucket = 0;
		}
		
		if (minutesPassed > 0) {
			// Update to the last minute boundary that was processed
			this.lastRotation = this.lastRotation + (minutesPassed * 60000);
		}
	}
}

/**
 * Hash auth tokens before counting them to avoid storing raw secrets.
 */
function hashToken(token: string): string {
	return createHash('sha256').update(token).digest('hex');
}

/**
 * Centralized metrics counter for transport operations
 */
export class MetricsCounter {
	private metrics: TransportMetrics;
	private rollingMinute: RollingWindowCounter;
	private rollingHour: RollingWindowCounter;
	private rolling3Hours: RollingWindowCounter;
	private uniqueIps: Set<string>;
	private clientIps: Map<string, Set<string>>; // Map of clientKey -> Set of IPs
	private clientAuthHashes: Map<string, Set<string>>; // Map of clientKey -> Set of auth token hashes

	constructor() {
		this.metrics = createEmptyMetrics();
		this.rollingMinute = new RollingWindowCounter(1);
		this.rollingHour = new RollingWindowCounter(60);
		this.rolling3Hours = new RollingWindowCounter(180);
		this.uniqueIps = new Set();
		this.clientIps = new Map();
		this.clientAuthHashes = new Map();
	}

	/**
	 * Get the underlying metrics data
	 */
	getMetrics(): TransportMetrics {
		// Calculate rates (requests per minute) for each window
		// Note: All values represent "requests per minute" calculated over their respective windows
		this.metrics.requests.lastMinute = this.rollingMinute.getCount(); // Requests in last 1 minute (already per minute)

		// For longer windows, divide total count by window size to get per-minute rate
		const hourCount = this.rollingHour.getCount();
		const threeHourCount = this.rolling3Hours.getCount();

		// Calculate per-minute rates for the longer windows
		this.metrics.requests.lastHour = Math.round((hourCount / 60) * 100) / 100; // Requests per minute over last hour
		this.metrics.requests.last3Hours = Math.round((threeHourCount / 180) * 100) / 100; // Requests per minute over last 3 hours

		// Update unique IPs count
		this.metrics.connections.uniqueIps = this.uniqueIps.size;

		return this.metrics;
	}

	/**
	 * Track a new request received by the transport
	 */
	trackRequest(): void {
		this.metrics.requests.total++;
		this.updateRequestsPerMinute();
		
		// Update rolling window counters
		this.rollingMinute.increment();
		this.rollingHour.increment();
		this.rolling3Hours.increment();
		
		// Calculate rates (requests per minute) for each window
		// Note: All values represent "requests per minute" calculated over their respective windows
		this.metrics.requests.lastMinute = this.rollingMinute.getCount(); // Requests in last 1 minute (already per minute)
		
		// For longer windows, divide total count by window size to get per-minute rate
		const hourCount = this.rollingHour.getCount();
		const threeHourCount = this.rolling3Hours.getCount();
		
		// Calculate per-minute rates for the longer windows
		this.metrics.requests.lastHour = Math.round((hourCount / 60) * 100) / 100; // Requests per minute over last hour
		this.metrics.requests.last3Hours = Math.round((threeHourCount / 180) * 100) / 100; // Requests per minute over last 3 hours
	}

	/**
	 * Track an error in the transport
	 */
	trackError(statusCode?: number, error?: Error): void {
		if (statusCode && statusCode >= 400 && statusCode < 500) {
			this.metrics.errors.expected++;
		} else {
			this.metrics.errors.unexpected++;
		}

		if (error) {
			this.metrics.errors.lastError = {
				type: error.constructor.name,
				message: error.message,
				timestamp: new Date(),
			};
		}
	}

	/**
	 * Track a new connection established (global counter)
	 */
	trackNewConnection(): void {
		this.metrics.connections.total++;
	}

	/**
	 * Track an IP address
	 */
	trackIpAddress(ipAddress: string | undefined): void {
		if (ipAddress) {
			this.uniqueIps.add(ipAddress);
		}
	}

	/**
	 * Track an IP address for a specific client
	 */
	trackClientIpAddress(ipAddress: string | undefined, clientInfo?: { name: string; version: string }): void {
		// Always track globally
		this.trackIpAddress(ipAddress);

		// Track per-client if client info is available
		if (ipAddress && clientInfo) {
			const clientKey = getClientKey(clientInfo.name, clientInfo.version);
			const clientMetrics = this.metrics.clients.get(clientKey);

			if (clientMetrics) {
				// Get or create the IP set for this client
				let clientIpSet = this.clientIps.get(clientKey);
				if (!clientIpSet) {
					clientIpSet = new Set();
					this.clientIps.set(clientKey, clientIpSet);
				}

				// Check if this is a new IP for this client
				const isNewIp = !clientIpSet.has(ipAddress);
				if (isNewIp) {
					clientIpSet.add(ipAddress);
					clientMetrics.newIpCount++;
				}
			}
		}
	}

	/**
	 * Track auth status for a specific client
	 */
	trackClientAuth(authToken: string | undefined, clientInfo?: { name: string; version: string }): void {
		if (!clientInfo) return;

		const clientKey = getClientKey(clientInfo.name, clientInfo.version);
		const clientMetrics = this.metrics.clients.get(clientKey);

		if (clientMetrics) {
			if (!authToken) {
				// Anonymous request
				clientMetrics.anonCount++;
			} else {
				// Authenticated request - hash the token for privacy
				const tokenHash = hashToken(authToken);

				// Get or create the auth hash set for this client
				let clientAuthSet = this.clientAuthHashes.get(clientKey);
				if (!clientAuthSet) {
					clientAuthSet = new Set();
					this.clientAuthHashes.set(clientKey, clientAuthSet);
				}

				// Check if this is a new auth token for this client
				const isNewAuth = !clientAuthSet.has(tokenHash);
				if (isNewAuth) {
					clientAuthSet.add(tokenHash);
					clientMetrics.uniqueAuthCount++;
				}
			}
		}
	}

	/**
	 * Update active connection count
	 */
	updateActiveConnections(count: number): void {
		this.metrics.connections.active = count;
	}

	/**
	 * Track a session that was cleaned up/removed
	 */
	trackSessionCleaned(): void {
		if (!this.metrics.connections.cleaned) {
			this.metrics.connections.cleaned = 0;
		}
		this.metrics.connections.cleaned++;
	}

	/**
	 * Associate a session with a client identity when client info becomes available
	 */
	associateSessionWithClient(clientInfo: { name: string; version: string }): void {
		const clientKey = getClientKey(clientInfo.name, clientInfo.version);
		let clientMetrics = this.metrics.clients.get(clientKey);

		if (!clientMetrics) {
			clientMetrics = {
				name: clientInfo.name,
				version: clientInfo.version,
				requestCount: 0,
				firstSeen: new Date(),
				lastSeen: new Date(),
				isConnected: true,
				activeConnections: 1,
				totalConnections: 1,
				toolCallCount: 0,
				newIpCount: 0,
				anonCount: 0,
				uniqueAuthCount: 0,
			};
			this.metrics.clients.set(clientKey, clientMetrics);
		} else {
			clientMetrics.lastSeen = new Date();
			clientMetrics.isConnected = true;
			clientMetrics.activeConnections++;
			clientMetrics.totalConnections++;
		}
	}

	/**
	 * Update client activity when a request is made
	 */
	updateClientActivity(clientInfo?: { name: string; version: string }): void {
		if (!clientInfo) return;

		const clientKey = getClientKey(clientInfo.name, clientInfo.version);
		const clientMetrics = this.metrics.clients.get(clientKey);

		if (clientMetrics) {
			clientMetrics.requestCount++;
			clientMetrics.lastSeen = new Date();
		}
	}

	/**
	 * Mark a client connection as disconnected
	 */
	disconnectClient(clientInfo?: { name: string; version: string }): void {
		if (!clientInfo) return;

		const clientKey = getClientKey(clientInfo.name, clientInfo.version);
		const clientMetrics = this.metrics.clients.get(clientKey);

		if (clientMetrics && clientMetrics.activeConnections > 0) {
			clientMetrics.activeConnections--;
			if (clientMetrics.activeConnections === 0) {
				clientMetrics.isConnected = false;
			}
		}
	}

	/**
	 * Track a method call
	 */
	trackMethod(
		method: string | null,
		responseTime?: number,
		isError: boolean = false,
		clientInfo?: { name: string; version: string }
	): void {
		if (!method) return;
		let methodMetrics = this.metrics.methods.get(method);

		if (!methodMetrics) {
			methodMetrics = {
				method,
				count: 0,
				firstCalled: new Date(),
				lastCalled: new Date(),
				errors: 0,
				byClient: new Map(),
			};
			this.metrics.methods.set(method, methodMetrics);
		}

		methodMetrics.count++;
		methodMetrics.lastCalled = new Date();

		// Track per-client breakdown
		if (clientInfo) {
			const clientName = clientInfo.name;
			let clientMethodMetrics = methodMetrics.byClient.get(clientName);

			if (!clientMethodMetrics) {
				clientMethodMetrics = {
					clientName,
					count: 0,
				};
				methodMetrics.byClient.set(clientName, clientMethodMetrics);
			}

			clientMethodMetrics.count++;

			// If this is a tool call, increment the client's tool call count
			if (method.startsWith('tools/call:')) {
				const clientKey = getClientKey(clientInfo.name, clientInfo.version);
				const clientMetrics = this.metrics.clients.get(clientKey);
				if (clientMetrics) {
					clientMetrics.toolCallCount++;
				}
			}
		}

		if (isError) {
			methodMetrics.errors++;
		}

		// Update average response time if provided
		if (responseTime !== undefined && !isError) {
			const successfulCalls = methodMetrics.count - methodMetrics.errors;
			if (successfulCalls === 1) {
				methodMetrics.averageResponseTime = responseTime;
			} else {
				const currentAvg = methodMetrics.averageResponseTime || 0;
				const totalTime = currentAvg * (successfulCalls - 1) + responseTime;
				methodMetrics.averageResponseTime = totalTime / successfulCalls;
			}
		}
	}

	/**
	 * Track a ping being sent
	 */
	trackPingSent(): void {
		if (!this.metrics.pings) {
			this.metrics.pings = {
				sent: 0,
				successful: 0,
				failed: 0,
			};
		}
		this.metrics.pings.sent++;
	}

	/**
	 * Track a successful ping response
	 */
	trackPingSuccess(): void {
		if (!this.metrics.pings) {
			this.metrics.pings = {
				sent: 0,
				successful: 0,
				failed: 0,
			};
		}
		this.metrics.pings.successful++;
		this.metrics.pings.lastPingTime = new Date();
	}

	/**
	 * Track a failed ping
	 */
	trackPingFailed(): void {
		if (!this.metrics.pings) {
			this.metrics.pings = {
				sent: 0,
				successful: 0,
				failed: 0,
			};
		}
		this.metrics.pings.failed++;
	}

	/**
	 * Track a static page hit with status code
	 */
	trackStaticPageHit(statusCode: number): void {
		if (statusCode === 200) {
			this.metrics.staticPageHits200 = (this.metrics.staticPageHits200 || 0) + 1;
		} else if (statusCode === 405) {
			this.metrics.staticPageHits405 = (this.metrics.staticPageHits405 || 0) + 1;
		}
	}

	/**
	 * Track authenticated connection
	 */
	trackAuthenticatedConnection(): void {
		this.metrics.connections.authenticated++;
	}

	/**
	 * Track anonymous connection
	 */
	trackAnonymousConnection(): void {
		this.metrics.connections.anonymous++;
	}

	/**
	 * Track unauthorized connection (401)
	 */
	trackUnauthorizedConnection(): void {
		if (!this.metrics.connections.unauthorized) {
			this.metrics.connections.unauthorized = 0;
		}
		this.metrics.connections.unauthorized++;
	}

	/**
	 * Track a new session being created
	 */
	trackSessionCreated(): void {
		if (this.metrics.sessions) {
			this.metrics.sessions.created++;
		}
	}


	/**
	 * Track a failed session resumption attempt
	 */
	trackSessionResumeFailed(): void {
		if (this.metrics.sessions) {
			this.metrics.sessions.resumedFailed++;
		}
	}

	/**
	 * Track a session being deleted/cleaned up
	 */
	trackSessionDeleted(): void {
		if (this.metrics.sessions) {
			this.metrics.sessions.deleted++;
		}
	}

	/**
	 * Update requests per minute calculation
	 */
	private updateRequestsPerMinute(): void {
		const now = Date.now();
		const startupTime = this.metrics.startupTime.getTime();
		const uptimeMinutes = (now - startupTime) / (1000 * 60);

		this.metrics.requests.averagePerMinute =
			uptimeMinutes > 0 ? Math.round((this.metrics.requests.total / uptimeMinutes) * 100) / 100 : 0;
	}
}
