import express, { type Express } from 'express';
import cors from 'cors';
import type { CorsOptions, CorsRequest, CorsOptionsDelegate } from 'cors';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import type { Server } from 'node:http';
import type { TransportInfo } from '../shared/transport-info.js';
import { settingsService, type SpaceTool } from '../shared/settings.js';
import { logger } from './utils/logger.js';
import type { BaseTransport } from './transport/base-transport.js';
import type { McpApiClient } from './utils/mcp-api-client.js';
import { formatMetricsForAPI } from '../shared/transport-metrics.js';
import { ALL_BUILTIN_TOOL_IDS } from '@llmindset/hf-mcp';
import { CORS_ALLOWED_ORIGINS, CORS_EXPOSED_HEADERS } from '../shared/constants.js';
import { apiMetrics } from './utils/api-metrics.js';
import { gradioMetrics } from './utils/gradio-metrics.js';
import { formatCacheMetricsForAPI } from './utils/gradio-cache.js';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class WebServer {
	private app: Express;
	private server: Server | null = null;
	private transportInfo: TransportInfo = {
		transport: 'unknown',
		defaultHfTokenSet: false,
		externalApiMode: false,
		stdioClient: null,
	};
	private localSharedToolStates: Map<string, boolean> = new Map();
	private transport?: BaseTransport;
	private apiClient?: McpApiClient;

	constructor() {
		this.app = express() as Express;
		this.setupMiddleware();
	}

	private setupMiddleware(): void {
		this.app.disable('x-powered-by');
		this.app.set('trust proxy', true);
		// Inbound body size limit to prevent abuse
		this.app.use(express.json({ limit: '1mb' }));

		// Basic security headers (complementary to CORS)
		this.app.use((_, res, next) => {
			res.setHeader('X-Content-Type-Options', 'nosniff');
			res.setHeader('Referrer-Policy', 'no-referrer');
			if (process.env.HSTS === 'true') {
				res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
			}
			next();
		});



		// Global CORS for all routes (API + MCP endpoints)
		// Simple exact-match allowlist with optional env override
		const envOrigins = (process.env.CORS_ALLOWED_ORIGINS || '')
			.split(',')
			.map((s) => s.trim())
			.filter(Boolean);
		const normalize = (s: string) => s.replace(/\/+$/, '');
		const envOriginsNorm = envOrigins.map(normalize);
		const allowedOrigins = (envOriginsNorm.length > 0 ? envOriginsNorm : CORS_ALLOWED_ORIGINS).map(normalize);

		// Support wildcard "*" to allow all origins explicitly
		let originSetting: CorsOptions['origin'];
		if (allowedOrigins.length === 1 && allowedOrigins[0] === '*') {
			originSetting = '*';
		} else if (allowedOrigins.some((o) => o.includes('*'))) {
			// Support basic subdomain wildcards like "https://*.use-mcp.dev" or "*.use-mcp.dev"
			const exact = new Set(allowedOrigins.filter((o) => !o.includes('*')));
			const patterns = allowedOrigins.filter((o) => o.includes('*'));

			originSetting = (requestOrigin: string | undefined, cb: (err: Error | null, allow?: boolean) => void) => {
				if (!requestOrigin) return cb(null, true);
				const reqOrigin = normalize(requestOrigin);
				if (exact.has(reqOrigin)) return cb(null, true);
				try {
					const u = new URL(requestOrigin);
					for (const p of patterns) {
						let scheme: string | undefined;
						let hostPattern = p;
						if (p.startsWith('http://') || p.startsWith('https://')) {
							scheme = p.split('://', 1)[0];
							hostPattern = p.slice((scheme + '://').length);
						}
						// Only support leading wildcard: *.domain.tld
						if (!hostPattern.startsWith('*.')) continue;
						const suffix = hostPattern.slice(2); // domain.tld
						const host = u.hostname;
						if (scheme && u.protocol !== scheme + ':') continue;
						if (host.endsWith('.' + suffix) && host !== suffix) {
							return cb(null, true);
						}
					}
					return cb(null, false);
				} catch {
					return cb(null, false);
				}
			};
		} else {
			originSetting = allowedOrigins;
		}

		const corsOptions: CorsOptions | CorsOptionsDelegate<CorsRequest> = {
			origin: originSetting,
			exposedHeaders: CORS_EXPOSED_HEADERS,
		};

		this.app.use(cors(corsOptions));
		// Ensure preflight requests succeed for any path
		this.app.options('*', cors(corsOptions));
	}

	public getApp(): Express {
		return this.app;
	}

	public setTransportInfo(info: TransportInfo): void {
		this.transportInfo = info;
	}

	public setClientInfo(clientInfo: { name: string; version: string } | null): void {
		this.transportInfo.stdioClient = clientInfo;
	}

	public initializeToolStates(): void {
		// Initialize local shared tool states based on current settings to prevent initial event burst
		const currentSettings = settingsService.getSettings();
		for (const toolId of ALL_BUILTIN_TOOL_IDS) {
			const isEnabled = currentSettings.builtInTools.includes(toolId);
			this.localSharedToolStates.set(toolId, isEnabled);
		}
	}

	public setTransport(transport: BaseTransport): void {
		this.transport = transport;
	}

	public setApiClient(apiClient: McpApiClient): void {
		this.apiClient = apiClient;
	}

	public getTransportInfo(): TransportInfo {
		return this.transportInfo;
	}

	public async start(port: number): Promise<void> {
		if (this.server) {
			throw new Error('Server is already running');
		}

		return new Promise((resolve, reject) => {
			this.server = this.app
				.listen(port, () => {
					this.transportInfo.port = port;
					resolve();
				})
				.on('error', reject);
		});
	}

	public async stop(): Promise<void> {
		if (!this.server) {
			return;
		}

		return new Promise((resolve, reject) => {
			this.server?.close((err) => {
				if (err) {
					reject(err);
				} else {
					this.server = null;
					resolve();
				}
			});
		});
	}

	public async setupStaticFiles(isDevelopment: boolean): Promise<void> {
		if (isDevelopment) {
			// In development mode, use Vite's dev server middleware
			try {
				const { createServer: createViteServer } = await import('vite');
				const rootDir = path.resolve(__dirname, '..', '..', '..', 'app', 'src', 'web');

				// Create Vite server with proper HMR configuration
				const vite = await createViteServer({
					configFile: path.resolve(__dirname, '..', '..', '..', 'app', 'vite.config.ts'),
					server: {
						middlewareMode: true,
						hmr: true, // Explicitly enable HMR
					},
					appType: 'spa',
					root: rootDir,
				});

				// Use Vite's middleware for dev server with HMR
				this.app.use(vite.middlewares);

				logger.info('Using Vite middleware in development mode with HMR enabled');
				logger.info({ rootDir }, 'Vite root directory');
			} catch (err) {
				logger.error({ err }, 'Error setting up Vite middleware');
				throw err;
			}
		} else {
			// In production, serve static files
			const staticPath = path.join(__dirname, '..', 'web');
			this.app.use(express.static(staticPath));

			// Fallback to index.html for SPA routing
			this.app.get('*', (req, res) => {
				if (!req.path.startsWith('/api/')) {
					res.sendFile(path.join(staticPath, 'index.html'));
				}
			});
		}
	}

	public setupApiRoutes(): void {

		// Transport info endpoint
		this.app.get('/api/transport', (_req, res) => {
			res.json(this.transportInfo);
		});

		// Sessions endpoint
		this.app.get('/api/sessions', (_req, res) => {
			if (!this.transport) {
				res.json([]);
				return;
			}

			const sessions = this.transport.getSessions();

			// For STDIO transport, also update the stdioClient info if we have a session
			if (this.transportInfo.transport === 'stdio' && sessions.length > 0) {
				const stdioSession = sessions[0];
				if (stdioSession?.clientInfo && !this.transportInfo.stdioClient) {
					this.transportInfo.stdioClient = {
						name: stdioSession.clientInfo.name,
						version: stdioSession.clientInfo.version,
					};
				}
			}

			res.json(sessions);
		});

		// Transport metrics endpoint
		this.app.get('/api/transport-metrics', (req, res) => {
			if (!this.transport) {
				res.status(503).json({ error: 'Transport not initialized' });
				return;
			}

			try {
				// Check for templog query parameter
				const tempLogParam = req.query.templog;
				let tempLogStatus: { activated: boolean; remaining: number; maxAllowed: number } | undefined = undefined;

				if (tempLogParam && this.transportInfo.transport === 'streamableHttpJson') {
					// Only activate for stateless transport with analytics mode
					// We need to import StatelessHttpTransport type or use method check
					const statelessTransport = this.transport as {
						activateTempLogging?: (count: number) => number;
						getTempLogStatus?: () => { enabled: boolean; remaining: number; maxAllowed: number };
					};
					if (statelessTransport.activateTempLogging && statelessTransport.getTempLogStatus) {
						const requestedCount = parseInt(tempLogParam as string, 10);
						if (!isNaN(requestedCount) && requestedCount > 0) {
							const activated = statelessTransport.activateTempLogging(requestedCount);
							tempLogStatus = {
								activated: true,
								remaining: activated,
								maxAllowed: statelessTransport.getTempLogStatus().maxAllowed,
							};
						}
					}
				}

				// Get raw metrics from transport
				const metrics = this.transport.getMetrics();

				// Determine if transport is stateless
				const isStateless = this.transportInfo.transport === 'streamableHttpJson';

				// Get configuration for stateful transports
				const config = this.transport.getConfiguration();

				// Get sessions (empty for stateless transports)
				const sessions = this.transport.getSessions().map((session) => {
					// Determine connection status: Connected, Distressed, or Disconnected
					const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
					const hasRecentActivity = session.lastActivity > fiveMinutesAgo;
					const hasPingFailures = (session.pingFailures || 0) >= 1;

					// Note that from the WebUI this is provided as a courtesy. If a Client connects and
					// disconnects before the Client refresh it will not be shown in the Client list.
					let connectionStatus: 'Connected' | 'Distressed' | 'Disconnected';
					if (!hasRecentActivity) {
						connectionStatus = 'Disconnected';
					} else if (hasPingFailures) {
						connectionStatus = 'Distressed';
					} else {
						connectionStatus = 'Connected';
					}

					return {
						id: session.id,
						connectedAt: session.connectedAt.toISOString(),
						lastActivity: session.lastActivity.toISOString(),
						requestCount: session.requestCount,
						clientInfo: session.clientInfo,
						isConnected: hasRecentActivity,
						connectionStatus,
						pingFailures: session.pingFailures || 0,
						lastPingAttempt: session.lastPingAttempt?.toISOString(),
						ipAddress: session.ipAddress,
					};
				});

				// Format for API response
				const formattedMetrics = formatMetricsForAPI(metrics, this.transportInfo.transport, isStateless, sessions);

				// Add configuration if available
				if (!isStateless && config.staleCheckInterval && config.staleTimeout) {
					formattedMetrics.configuration = {
						heartbeatInterval: config.heartbeatInterval || 30000,
						staleCheckInterval: config.staleCheckInterval,
						staleTimeout: config.staleTimeout,
						pingEnabled: config.pingEnabled,
						pingInterval: config.pingInterval,
						pingFailureThreshold: config.pingFailureThreshold || 1,
					};
				}

				// Add API metrics if in external API mode
				if (this.transportInfo.externalApiMode) {
					formattedMetrics.apiMetrics = apiMetrics.getMetrics();
				}

				// Add Gradio metrics
				formattedMetrics.gradioMetrics = gradioMetrics.getMetrics();

				// Add Gradio cache metrics
				formattedMetrics.gradioCacheMetrics = formatCacheMetricsForAPI();

				// Add temp log status if it was activated or if we need to check current status
				const extendedMetrics = formattedMetrics as typeof formattedMetrics & { tempLogStatus?: unknown };
				if (tempLogStatus) {
					extendedMetrics.tempLogStatus = tempLogStatus;
				} else if (this.transportInfo.transport === 'streamableHttpJson') {
					// Include current status even if not activating
					const statelessTransport = this.transport as {
						getTempLogStatus?: () => { enabled: boolean; remaining: number; maxAllowed: number };
					};
					if (statelessTransport.getTempLogStatus) {
						const status = statelessTransport.getTempLogStatus();
						if (status.enabled) {
							extendedMetrics.tempLogStatus = status;
						}
					}
				}

				res.json(formattedMetrics);
			} catch (error) {
				logger.error({ error }, 'Error retrieving transport metrics');
				res.status(500).json({ error: 'Failed to retrieve transport metrics' });
			}
		});

		// Settings endpoint
		this.app.get('/api/settings', (_req, res) => {
			res.json(settingsService.getSettings());
		});

		// Update tool settings endpoint
		this.app.post('/api/settings', express.json(), (req, res) => {
			const { builtInTools, spaceTools } = req.body as { builtInTools?: string[]; spaceTools?: SpaceTool[] };

			let updatedSettings = settingsService.getSettings();

			if (builtInTools !== undefined) {
				updatedSettings = settingsService.updateBuiltInTools(builtInTools);
			}

			if (spaceTools !== undefined) {
				updatedSettings = settingsService.updateSpaceTools(spaceTools);
			}

			// Enable or disable only the tools that actually changed state
			if (builtInTools !== undefined) {
				for (const toolId of ALL_BUILTIN_TOOL_IDS) {
					const shouldBeEnabled = builtInTools.includes(toolId);
					const currentlyEnabled = this.localSharedToolStates.get(toolId) ?? false;

					// Only update state and emit events if state actually changed
					if (currentlyEnabled !== shouldBeEnabled) {
						this.localSharedToolStates.set(toolId, shouldBeEnabled);
						// Emit event for MCP server instances
						if (this.apiClient) {
							this.apiClient.emit('toolStateChange', toolId, shouldBeEnabled);
						}
						logger.info(`Tool ${toolId} has been ${shouldBeEnabled ? 'enabled' : 'disabled'} via API`);
					}
				}
			}

			res.json(updatedSettings);
		});

		// Gradio endpoints endpoint
		this.app.get('/api/gradio-endpoints', (_req, res) => {
			if (!this.apiClient) {
				res.json([]);
				return;
			}
			res.json(this.apiClient.getGradioEndpoints());
		});

		// Update Gradio endpoint status
		this.app.post('/api/gradio-endpoints/:index', express.json(), (req, res) => {
			const index = parseInt(req.params.index);
			const { enabled } = req.body as { enabled: boolean };

			if (!this.apiClient) {
				res.status(500).json({ error: 'API client not initialized' });
				return;
			}

			const endpoints = this.apiClient.getGradioEndpoints();
			if (index < 0 || index >= endpoints.length) {
				res.status(404).json({ error: 'Endpoint not found' });
				return;
			}

			// Update the state in the API client
			this.apiClient.updateGradioEndpointState(index, enabled);

			// Emit tool state change event for Gradio endpoint
			const endpoint = endpoints[index];
			if (endpoint) {
				const toolId = `gradio_${endpoint.subdomain}`;
				this.apiClient.emit('toolStateChange', toolId, enabled);
			}

			// Get the updated endpoint
			const updatedEndpoint = endpoints[index];

			res.json(updatedEndpoint);
		});

		// Update Gradio endpoint
		this.app.put('/api/gradio-endpoints/:index', express.json(), (req, res) => {
			const index = parseInt(req.params.index);
			const { name, subdomain, id, emoji } = req.body as {
				name: string;
				subdomain: string;
				id?: string;
				emoji?: string;
			};

			if (!this.apiClient) {
				res.status(500).json({ error: 'API client not initialized' });
				return;
			}

			const endpoints = this.apiClient.getGradioEndpoints();
			if (index < 0 || index >= endpoints.length) {
				res.status(404).json({ error: 'Endpoint not found' });
				return;
			}

			// Validate required fields
			if (!name || !subdomain) {
				res.status(400).json({ error: 'Name and subdomain are required' });
				return;
			}

			// Update the endpoint in the API client
			const updatedEndpoint = { name, subdomain, id, emoji };
			this.apiClient.updateGradioEndpoint(index, updatedEndpoint);

			res.json(updatedEndpoint);
		});
	}
}
