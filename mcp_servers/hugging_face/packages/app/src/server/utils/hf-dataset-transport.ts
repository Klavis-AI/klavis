import build from 'pino-abstract-transport';
import { uploadFile } from '@huggingface/hub';
import type { uploadFile as UploadFileFunction } from '@huggingface/hub';
import { randomUUID } from 'node:crypto';
import type { Transform } from 'node:stream';
import safeStringify from 'fast-safe-stringify';

const HF_TOKEN_REGEX = /hf_[A-Za-z0-9]{7,}[A-Za-z0-9-]*/g;
const REDACTED_TOKEN = 'REDACTED_TOKEN';

export interface HfDatasetTransportOptions {
	loggingToken: string;
	datasetId: string;
	batchSize?: number;
	flushInterval?: number; // in milliseconds
	uploadFunction?: typeof UploadFileFunction;
	logType?: string; // For console output labeling
}

export interface HfTransportOptions {
	batchSize?: number;
	flushInterval?: number;
	logType?: string; // 'Query' or 'Logs'
}

export interface LogEntry {
	level: number;
	time: number;
	msg: string;
	[key: string]: unknown;
}

export class HfDatasetLogger {
	private loggingToken: string;
	private datasetId: string;
	private logBuffer: LogEntry[] = [];
	private batchSize: number;
	private flushInterval: number;
	private flushTimer?: NodeJS.Timeout;
	private isShuttingDown = false;
	private uploadInProgress = false;
	private sessionId: string;
	private uploadFunction: typeof UploadFileFunction;
	private readonly maxBufferSize: number = 10000;
	private logType: string;

	constructor(options: HfDatasetTransportOptions) {
		this.loggingToken = options.loggingToken;
		this.datasetId = options.datasetId;
		this.batchSize = options.batchSize || 100;
		this.flushInterval = calculateFlushInterval(options.flushInterval);
		this.sessionId = randomUUID();
		this.uploadFunction = options.uploadFunction || uploadFile;
		this.logType = options.logType || 'Logs';

		// Start the flush timer
		this.startFlushTimer();

		// Register shutdown handlers
		this.registerShutdownHandlers();

		// Log initialization with flush interval
		console.log(
			`[HF Dataset ${this.logType}] Initialized - Dataset: ${this.datasetId}, Session: ${this.sessionId}, FlushInterval: ${this.flushInterval}ms, BatchSize: ${this.batchSize}`
		);
	}

	processLog(logEntry: LogEntry): void {
		try {
			if (this.logBuffer.length >= this.maxBufferSize) {
				this.logBuffer.shift();
			}

			this.logBuffer.push(logEntry);

			if (this.logBuffer.length >= this.batchSize) {
				//		console.log(`[HF Dataset ${this.logType}] Triggering flush due to batch size (${this.batchSize})`);
				void this.flush();
			}
		} catch (error) {
			console.error(`[HF Dataset ${this.logType}] Error processing log:`, error);
		}
	}

	private startFlushTimer(): void {
		this.flushTimer = setInterval(() => {
			if (this.logBuffer.length > 0) {
				console.log(`[HF Dataset ${this.logType}] Timer flush triggered - Buffer: ${this.logBuffer.length} logs`);
				void this.flush();
			}
		}, this.flushInterval);
	}

	private async flush(): Promise<void> {
		//		console.log(
		//			`[HF Dataset ${this.logType}] Flush called - Buffer: ${this.logBuffer.length}, InProgress: ${this.uploadInProgress}`
		//		);

		if (this.uploadInProgress || this.logBuffer.length === 0) {
			return;
		}

		const logsToUpload = [...this.logBuffer];
		this.uploadInProgress = true;

		console.log(`[HF Dataset ${this.logType}] Starting upload of ${logsToUpload.length} logs`);

		try {
			await this.uploadLogs(logsToUpload);
			// Only clear buffer after successful upload
			this.logBuffer = [];
			console.log(`[HF Dataset ${this.logType}] ✅ Uploaded ${logsToUpload.length} logs to ${this.datasetId}`);
		} catch (error) {
			// Keep logs in buffer for retry on next flush cycle
			console.error(`[HF Dataset ${this.logType}] ❌ Upload failed, will retry on next flush:`, error);
		} finally {
			this.uploadInProgress = false;
		}
	}

	private async uploadLogs(logs: LogEntry[]): Promise<void> {
		const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
		const filename = `logs-${timestamp}-${this.sessionId}.jsonl`;

		const dateFolder = new Date().toISOString().split('T')[0];
		const folder = this.logType === 'Query' ? 'queries' 
			: this.logType === 'System' ? 'sessions' 
			: this.logType === 'Gradio' ? 'gradio'
			: 'logs';
		const pathInRepo = `${folder}/${dateFolder}/${filename}`;

		console.log(`[HF Dataset ${this.logType}] Uploading to path: ${pathInRepo}`);

		// Create JSONL content directly in memory
		const logData = logs
			.map((log) => safeStringifyLog(log, this.sessionId, this.logType))
			.filter(Boolean) // Remove empty strings from null/undefined logs
			.join('\n');

		// Upload directly from memory with timeout
		const uploadTimeout = 30000; // 30 seconds
		await Promise.race([
			this.uploadFunction({
				repo: { type: 'dataset', name: this.datasetId },
				file: {
					path: pathInRepo,
					content: new Blob([logData], { type: 'application/x-ndjson' }),
				},
				accessToken: this.loggingToken,
				commitTitle: `Add ${logs.length} log entries`,
				commitDescription: `Session: ${this.sessionId}, Time: ${new Date().toISOString()}`,
			}),
			new Promise((_, reject) => setTimeout(() => reject(new Error('Upload timeout')), uploadTimeout)),
		]);
	}

	private registerShutdownHandlers(): void {
		const shutdownHandler = async () => {
			await this.destroy();
		};

		// Register handlers for various shutdown signals (skip in tests to avoid MaxListeners warning)
		const isTest = process.env.NODE_ENV === 'test' || process.env.VITEST === 'true';
		if (!isTest) {
			process.once('beforeExit', shutdownHandler);
			process.once('SIGINT', shutdownHandler);
			process.once('SIGTERM', shutdownHandler);
			process.once('exit', () => {
				// Synchronous cleanup if needed
				if (this.flushTimer) {
					clearInterval(this.flushTimer);
				}
			});
		}
	}

	async destroy(): Promise<void> {
		if (this.isShuttingDown) return;
		this.isShuttingDown = true;

		console.log(`[HF Dataset ${this.logType}] Shutting down...`);

		// Clear the flush timer
		if (this.flushTimer) {
			clearInterval(this.flushTimer);
		}

		// Final flush attempt
		try {
			await this.flush();
		} catch (error) {
			console.error(`[HF Dataset ${this.logType}] Error during final log flush:`, error);
		}
	}

	// Simple health check method
	getStatus(): {
		bufferSize: number;
		uploadInProgress: boolean;
		sessionId: string;
	} {
		return {
			bufferSize: this.logBuffer.length,
			uploadInProgress: this.uploadInProgress,
			sessionId: this.sessionId,
		};
	}
}

// Helper function to calculate flush interval with environment awareness
function calculateFlushInterval(optionsInterval?: number): number {
	const envInterval = parseInt(process.env.LOGGING_FLUSH_INTERVAL || '300000', 10);
	const interval = optionsInterval || envInterval;
	const isTest = process.env.NODE_ENV === 'test' || process.env.VITEST === 'true';
	const isDev = process.env.NODE_ENV === 'development';
	const isAnalytics = process.env.ANALYTICS_MODE === 'true';

	if (isTest) return interval || 1000;
	if (isDev) return interval;
	if (isAnalytics) return interval; // Allow custom intervals in analytics mode
	return Math.max(interval, 300000); // Enforce minimum in production only
}

// Helper function to create a no-op transport
function createNoOpTransport(reason: string, logType = 'Logs'): Transform {
	console.warn(`[HF Dataset ${logType}] Dataset logging disabled: ${reason}`);
	return build(function (source) {
		source.on('data', function (_obj: unknown) {
			// No-op
		});
	});
}

// Replace any string that looks like a Hugging Face token to keep uploads clean
export function redactHfTokens(value: string): string {
	if (!value) return value;
	return value.replace(HF_TOKEN_REGEX, REDACTED_TOKEN);
}

// Helper function to safely stringify log entries with consistent structure
function safeStringifyLog(log: LogEntry, sessionId: string, logType: string): string {
	if (!log) return ''; // Skip null/undefined logs

	if (logType === 'Query' || logType === 'System' || logType === 'Gradio') {
		// For query, system, and gradio logs, preserve pino's time field but strip other pino metadata
		// Pino adds level, time, pid, hostname, msg - we want to keep time but strip the rest
		const { level: _level, pid: _pid, hostname: _hostname, msg: _msg, ...logEntry } = log;

		// Return the log entry with pino's time field preserved
		return redactHfTokens(safeStringify.default(logEntry));
	}

	// For standard logs, preserve pino defaults while creating structured format
	const standardizedLog = {
		message: log.msg || 'No message',
		level: log.level,
		time: log.time, // Preserve pino's time field
		pid: log.pid, // Preserve process ID
		hostname: log.hostname, // Preserve hostname
		sessionId,
		data: (() => {
			// Extract all fields except the standard ones and stringify them
			const { msg: _msg, level: _level, time: _time, pid: _pid, hostname: _hostname, ...extraData } = log;
			return Object.keys(extraData).length > 0 ? JSON.stringify(extraData) : undefined;
		})(),
	};

	// Remove undefined fields for cleaner output
	Object.keys(standardizedLog).forEach((key) => {
		if (standardizedLog[key as keyof typeof standardizedLog] === undefined) {
			delete standardizedLog[key as keyof typeof standardizedLog];
		}
	});

	return redactHfTokens(safeStringify.default(standardizedLog));
}

// Factory function for Pino transport using pino-abstract-transport
export default async function (opts: HfTransportOptions = {}): Promise<Transform> {
	const logType = opts.logType || 'Logs';

	// Early returns for no-op cases
	if (process.env.NODE_ENV === 'test' || process.env.VITEST === 'true') {
		return createNoOpTransport('disabled during tests', logType);
	}

	// All logs go to a single dataset; use LOGGING_DATASET_ID
	const datasetId = process.env.LOGGING_DATASET_ID;
	if (!datasetId) {
		return createNoOpTransport('no dataset ID configured', logType);
	}

	const loggingToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;
	if (!loggingToken) {
		console.warn(
			`[HF Dataset ${logType}] No HF token available (LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN). Dataset logging disabled.`
		);
		return createNoOpTransport('no HF token available', logType);
	}

	// Log that we're using HF dataset logging
	console.log(`[HF Dataset ${logType}] Logging to dataset: ${datasetId}`);

	try {
		// Create the HF dataset logger instance
		const hfLogger = new HfDatasetLogger({
			loggingToken,
			datasetId,
			batchSize: opts.batchSize || parseInt(process.env.LOGGING_BATCH_SIZE || '100', 10),
			flushInterval: calculateFlushInterval(opts.flushInterval),
			logType,
		});
		// Return a proper Pino transport using async iterator pattern (recommended)
		return build(
			async function (source) {
				for await (const obj of source) {
					// Process each log entry with error isolation
					try {
						hfLogger.processLog(obj);
					} catch (error) {
						// Never let transport errors affect the main logger
						console.error(`[HF Dataset ${logType}] Transport error (ignoring):`, error);
					}
				}
			},
			{
				async close(_err: Error) {
					// Ensure all logs are flushed on close
					try {
						await hfLogger.destroy();
					} catch (error) {
						console.error(`[HF Dataset ${logType}] Error during close (ignoring):`, error);
					}
				},
			}
		);
	} catch (error) {
		console.error(`[HF Dataset ${logType}] Failed to initialize, falling back to no-op:`, error);
		return createNoOpTransport('initialization failed', logType);
	}
}
