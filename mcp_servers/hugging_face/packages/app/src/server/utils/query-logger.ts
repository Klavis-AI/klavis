import pino, { type Logger, type LoggerOptions } from 'pino';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Feature flags: enable/disable per-log-type; defaults to true
const QUERY_LOGS_ENABLED = (process.env.LOG_QUERY_EVENTS ?? 'true').toLowerCase() === 'true';
const SYSTEM_LOGS_ENABLED = (process.env.LOG_SYSTEM_EVENTS ?? 'true').toLowerCase() === 'true';
const DATASET_CONFIGURED = !!process.env.LOGGING_DATASET_ID;

// Get the current file's directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Structure for query logs - consistent fields for HF dataset viewer
 */
export interface QueryLogEntry {
	mcpServerSessionId: string; // MCP Server to Dataset connection
	clientSessionId?: string | null; // Client to MCP Server connection
	name?: string | null; // ClientInfo.name
	version?: string | null; // ClientInfo.version
	methodName: string;
	query: string;
	parameters: string; // JSON string of parameters for consistent format
	// SessionMetadata fields
	isAuthenticated?: boolean;
	// Response information
	totalResults?: number;
	resultsShared?: number;
	responseCharCount?: number;
	requestJson?: string; // Full JSON of the request
	durationMs?: number;
	success?: boolean;
	errorMessage?: string | null;
}

export interface QueryLoggerOptions {
	clientSessionId?: string;
	isAuthenticated?: boolean;
	clientName?: string;
	clientVersion?: string;
	totalResults?: number;
	resultsShared?: number;
	responseCharCount?: number;
	durationMs?: number;
	success?: boolean;
	error?: unknown;
}

function createQueryLogger(): Logger | null {
	// Disable during tests
	if (process.env.NODE_ENV === 'test' || process.env.VITEST === 'true') {
		return null;
	}

	if (!QUERY_LOGS_ENABLED || !DATASET_CONFIGURED) {
		return null;
	}

	const datasetId = process.env.LOGGING_DATASET_ID;
	const hfToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;

	if (!hfToken) {
		console.warn('[Query Logger] Query logging disabled: No HF token found (set LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN)');
		return null;
	}

	console.log(`[Query Logger] Query logging enabled for dataset: ${datasetId}`);

	try {
		const transportPath = join(__dirname, 'hf-dataset-transport.js');

		const baseOptions: LoggerOptions = {
			level: 'info', // Always log queries when enabled
			timestamp: pino.stdTimeFunctions.isoTime,
		};

		// Only log to HF dataset, no console output for queries
		return pino({
			...baseOptions,
			transport: {
				target: transportPath,
				options: { sync: false, logType: 'Query' },
			},
		});
	} catch (error) {
		console.error('[Query Logger] Failed to setup query logging transport:', error);
		return null;
	}
}

const queryLogger: Logger | null = createQueryLogger();

function createSystemLogger(): Logger | null {
	// Disable during tests
	if (process.env.NODE_ENV === 'test' || process.env.VITEST === 'true') {
		return null;
	}

	// Require a dataset
	if (!DATASET_CONFIGURED) {
		return null;
	}

	if (!SYSTEM_LOGS_ENABLED) {
		return null;
	}

	const hfToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;
	if (!hfToken) {
		console.warn(
			'[System Logger] System logging disabled: No HF token found (set LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN)'
		);
		return null;
	}

	try {
		const transportPath = join(__dirname, 'hf-dataset-transport.js');
		const baseOptions: LoggerOptions = {
			level: 'info',
			timestamp: pino.stdTimeFunctions.isoTime,
		};
		return pino({
			...baseOptions,
			transport: {
				target: transportPath,
				options: { sync: false, logType: 'System' },
			},
		});
	} catch (error) {
		console.error('[System Logger] Failed to setup system logging transport:', error);
		return null;
	}
}

const systemLogger: Logger | null = createSystemLogger();

function createGradioLogger(): Logger | null {
	// Disable during tests
	if (process.env.NODE_ENV === 'test' || process.env.VITEST === 'true') {
		return null;
	}

	// Require a dataset
	if (!DATASET_CONFIGURED) {
		return null;
	}

	if (!SYSTEM_LOGS_ENABLED) {
		return null;
	}

	const hfToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;
	if (!hfToken) {
		console.warn(
			'[Gradio Logger] Gradio logging disabled: No HF token found (set LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN)'
		);
		return null;
	}

	try {
		const transportPath = join(__dirname, 'hf-dataset-transport.js');
		const baseOptions: LoggerOptions = {
			level: 'info',
			timestamp: pino.stdTimeFunctions.isoTime,
		};
		return pino({
			...baseOptions,
			transport: {
				target: transportPath,
				options: { sync: false, logType: 'Gradio' },
			},
		});
	} catch (error) {
		console.error('[Gradio Logger] Failed to setup Gradio logging transport:', error);
		return null;
	}
}

const gradioLogger: Logger | null = createGradioLogger();

// Stable session ID for this MCP server instance (process lifetime)
const mcpServerSessionId = crypto.randomUUID();

function getMcpServerSessionId(): string {
	return mcpServerSessionId;
}

/**
 * Log a search query with consistent structure
 */
export function logQuery(entry: QueryLogEntry): void {
	if (!queryLogger) {
		return;
	}

	queryLogger.info(entry);
}

/**
 * Simple helper to log successful search queries
 */
export function logSearchQuery(
	methodName: string,
	query: string,
	data: Record<string, unknown>,
	options?: QueryLoggerOptions
): void {
	// Use a stable mcpServerSessionId per process/transport instance
	const mcpServerSessionId = getMcpServerSessionId();
	const normalizedDurationMs =
		options?.durationMs !== undefined ? Math.round(options.durationMs) : undefined;
	const serializedParameters = JSON.stringify(data);
	const requestPayload = {
		methodName,
		query,
		parameters: data,
	};
	const normalizedError =
		options?.error !== undefined && options?.error !== null ? normalizeError(options.error) : null;

	logQuery({
		query,
		methodName,
		parameters: serializedParameters,
		requestJson: JSON.stringify(requestPayload),
		mcpServerSessionId,
		clientSessionId: options?.clientSessionId || null,
		isAuthenticated: options?.isAuthenticated ?? false,
		name: options?.clientName || null,
		version: options?.clientVersion || null,
		totalResults: options?.totalResults,
		resultsShared: options?.resultsShared,
		responseCharCount: options?.responseCharCount,
		durationMs: normalizedDurationMs,
		success: options?.success ?? true,
		errorMessage: normalizedError,
	});
}

/**
 * Simple helper to log prompts (model details, dataset details, user/paper summaries)
 */
export function logPromptQuery(
	methodName: string,
	query: string,
	data: Record<string, unknown>,
	options?: QueryLoggerOptions
): void {
	// Use a stable mcpServerSessionId per process/transport instance
	const mcpServerSessionId = getMcpServerSessionId();
	const normalizedDurationMs =
		options?.durationMs !== undefined ? Math.round(options.durationMs) : undefined;
	const serializedParameters = JSON.stringify(data);
	const requestPayload = {
		methodName,
		query,
		parameters: data,
	};
	const normalizedError =
		options?.error !== undefined && options?.error !== null ? normalizeError(options.error) : null;

	logQuery({
		query,
		methodName,
		parameters: serializedParameters,
		requestJson: JSON.stringify(requestPayload),
		mcpServerSessionId,
		clientSessionId: options?.clientSessionId || null,
		isAuthenticated: options?.isAuthenticated ?? false,
		name: options?.clientName || null,
		version: options?.clientVersion || null,
		totalResults: options?.totalResults,
		resultsShared: options?.resultsShared,
		responseCharCount: options?.responseCharCount,
		durationMs: normalizedDurationMs,
		success: options?.success ?? true,
		errorMessage: normalizedError,
	});
}

/**
 * Simple helper to log system events (initialize, session_delete)
 */
export function logSystemEvent(
	methodName: string,
	sessionId: string,
	options?: {
		clientSessionId?: string;
		isAuthenticated?: boolean;
		clientName?: string;
		clientVersion?: string;
		requestJson?: unknown;
		capabilities?: unknown;
		ipAddress?: string;
	}
): void {
	if (!systemLogger) {
		return;
	}

	const mcpServerSessionId = getMcpServerSessionId();

	// Extract name and version from capabilities if available
	let capabilitiesName = null;
	let capabilitiesVersion = null;
	if (options?.capabilities && typeof options.capabilities === 'object' && options.capabilities !== null) {
		const caps = options.capabilities as Record<string, unknown>;
		if (caps.clientInfo && typeof caps.clientInfo === 'object' && caps.clientInfo !== null) {
			const clientInfo = caps.clientInfo as Record<string, unknown>;
			capabilitiesName = typeof clientInfo.name === 'string' ? clientInfo.name : null;
			capabilitiesVersion = typeof clientInfo.version === 'string' ? clientInfo.version : null;
		}
	}

	systemLogger.info(
		{
			// Core session tracking fields (no level/message - they are redundant)
			sessionId, // Direct session ID field instead of using "query"
			methodName, // Direct method name field

			// Authorization status

			// Client info fields as separate columns
			name: options?.clientName || capabilitiesName || null,
			version: options?.clientVersion || capabilitiesVersion || null,
			authorized: options?.isAuthenticated ?? false, // renamed from isAuthenticated

			// IP address for session tracking
			ipAddress: options?.ipAddress || null,

			// Full request data for context
			capabilities: options?.capabilities ? JSON.stringify(options.capabilities) : null,
			clientSessionId: options?.clientSessionId || null,
			requestJson: options?.requestJson
				? JSON.stringify(options.requestJson)
				: JSON.stringify({ methodName, sessionId }),
			mcpServerSessionId,
		},
		'System event logged'
	);
}

/**
 * Log Gradio API calls with timing, success/error status, and response size
 */
export function logGradioEvent(
	endpointName: string,
	sessionId: string,
	options: {
		durationMs: number;
		isAuthenticated?: boolean;
		clientName?: string;
		clientVersion?: string;
		success: boolean;
		error?: unknown;
		responseSizeBytes?: number;
		notificationCount?: number;
		isDynamic?: boolean;
	}
): void {
	if (!gradioLogger) {
		return;
	}

	const mcpServerSessionId = getMcpServerSessionId();

	// Normalize error to a readable string
	let errorString: string | null = null;
	if (options.error !== undefined && options.error !== null) {
		if (typeof options.error === 'string') {
			errorString = options.error;
		} else if (options.error instanceof Error) {
			errorString = options.error.message;
		} else {
			try {
				errorString = JSON.stringify(options.error);
			} catch {
				errorString = String(options.error);
			}
		}
	}

	gradioLogger.info(
		{
			sessionId,
			endpointName, // e.g., "user/repo"
			name: options.clientName || null,
			version: options.clientVersion || null,
			authorized: options.isAuthenticated ?? false,
			durationMs: options.durationMs,
			success: options.success,
			error: errorString,
			responseSizeBytes: options.responseSizeBytes || null,
			notificationCount: options.notificationCount || 0,
			isDynamic: options.isDynamic ?? false,
			mcpServerSessionId,
		},
		'Gradio event logged'
	);
}

export { queryLogger };

function normalizeError(error: unknown): string {
	if (error instanceof Error) {
		return `${error.name}: ${error.message}`;
	}
	if (typeof error === 'string') {
		return error;
	}
	try {
		return JSON.stringify(error);
	} catch {
		return String(error);
	}
}
