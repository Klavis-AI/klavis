import pino, { type Logger, type LoggerOptions, type Level } from 'pino';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const isDev = process.env.NODE_ENV === 'development';
const activeTransport = process.env.TRANSPORT || '';

const destination = activeTransport.toUpperCase() === 'STDIO' ? 2 : 1; // 2 = stderr, 1 = stdout

const logLevel = (process.env.LOG_LEVEL?.toLowerCase() || 'info') as Level;
const hfLoggingEnabled = !!process.env.LOGGING_DATASET_ID;

// Get the current file's directory in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


function createLogger(): Logger {
	const baseOptions: LoggerOptions = {
		level: logLevel,
		timestamp: pino.stdTimeFunctions.isoTime, // Always use ISO time for better readability
	};

	// Setup HF logging if enabled
	if (hfLoggingEnabled) {
		const datasetId = process.env.LOGGING_DATASET_ID;
		const hfToken = process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN;
		
		if (!hfToken) {
			console.warn('[Logger] HF Dataset logging disabled: No HF token found (set LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN)');
		} else {
			console.log(`[Logger] HF Dataset logging enabled for dataset: ${datasetId}`);
			
			try {
				const transportPath = join(__dirname, 'hf-dataset-transport.js');
				
				const targets = [
					// Console output
					{
						target: 'pino-pretty',
						level: logLevel,
						options: { 
							colorize: isDev, 
							destination 
						},
					},
					// HF dataset output
					{
						target: transportPath,
						level: logLevel,
						options: { sync: false },
					},
				];
				
				return pino({ ...baseOptions, transport: { targets } });
			} catch (error) {
				console.error('[Logger] Failed to setup HF transport, falling back to console only:', error);
			}
		}
	}

	// Console-only logging (default or fallback)
	return pino({
		...baseOptions,
		...(isDev ? {
			transport: {
				target: 'pino-pretty',
				options: { colorize: true, destination },
			},
		} : {}),
	}, !isDev ? pino.destination(destination) : undefined);
}

const logger: Logger = createLogger();

// Function to reconfigure logger for STDIO transport
export function forceLoggerToStderr(): void {
	const stderrOptions: LoggerOptions = {
		level: logLevel,
		timestamp: pino.stdTimeFunctions.isoTime, // Always use ISO time for better readability
	};

	if (isDev) {
		// Development: use pretty printing to stderr
		Object.assign(
			logger,
			pino({
				...stderrOptions,
				transport: {
					target: 'pino-pretty',
					options: {
						colorize: true,
						destination: 2, // stderr
					},
				},
			})
		);
	} else {
		// Production: plain output to stderr
		Object.assign(logger, pino(stderrOptions, pino.destination(2)));
	}
}

export { logger };
