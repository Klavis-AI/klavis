export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'silent';

export interface Logger {
	trace: (...args: unknown[]) => void;
	debug: (...args: unknown[]) => void;
	info: (...args: unknown[]) => void;
	warn: (...args: unknown[]) => void;
	error: (...args: unknown[]) => void;
}

const LOG_LEVELS: Record<LogLevel, number> = {
	trace: 0,
	debug: 1,
	info: 2,
	warn: 3,
	error: 4,
	silent: 5,
};

function normalizeLogLevel(value: string | undefined): LogLevel {
	if (!value) return 'info';
	const normalized = value.toLowerCase();
	if (normalized in LOG_LEVELS) {
		return normalized as LogLevel;
	}
	return 'info';
}

const ACTIVE_LEVEL = normalizeLogLevel(process.env.LOG_LEVEL);

function shouldLog(level: LogLevel): boolean {
	return LOG_LEVELS[level] >= LOG_LEVELS[ACTIVE_LEVEL];
}

export const logger: Logger = {
	trace: (...args) => {
		if (shouldLog('trace')) {
			console.debug(...args);
		}
	},
	debug: (...args) => {
		if (shouldLog('debug')) {
			console.debug(...args);
		}
	},
	info: (...args) => {
		if (shouldLog('info')) {
			console.info(...args);
		}
	},
	warn: (...args) => {
		if (shouldLog('warn')) {
			console.warn(...args);
		}
	},
	error: (...args) => {
		if (shouldLog('error')) {
			console.error(...args);
		}
	},
};
