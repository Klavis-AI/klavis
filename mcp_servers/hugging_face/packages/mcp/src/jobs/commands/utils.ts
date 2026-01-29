import type { JobSpec } from '../types.js';
import { parse as parseShellArgs } from 'shell-quote';

interface EnvToken {
	type: 'env';
	key: string;
}

const SPECIAL_PARAMS = new Set(['*', '@', '#', '?', '!', '-', '_']);

function isEnvToken(entry: unknown): entry is EnvToken {
	return Boolean(entry && typeof entry === 'object' && (entry as EnvToken).type === 'env');
}

function formatEnvReference(key: string): string {
	if (key === '') {
		return '$';
	}

	if (key === '$') {
		return '$$';
	}

	if (/^[A-Za-z0-9_]+$/.test(key)) {
		return `$${key}`;
	}

	if (SPECIAL_PARAMS.has(key)) {
		return `$${key}`;
	}

	return `\${${key}}`;
}

/**
 * Parse timeout string (e.g., "5m", "2h", "30s") to seconds
 */
export function parseTimeout(timeout: string): number {
	const timeUnits: Record<'s' | 'm' | 'h' | 'd', number> = {
		s: 1,
		m: 60,
		h: 3600,
		d: 86400,
	};

	const match = timeout.match(/^(\d+(?:\.\d+)?)(s|m|h|d)$/);
	if (!match || !match[1] || !match[2]) {
		// Try to parse as plain number (seconds)
		const seconds = parseInt(timeout, 10);
		if (!isNaN(seconds)) {
			return seconds;
		}
		throw new Error(
			`Invalid timeout format: "${timeout}". Use format like "5m", "2h", "30s", or plain seconds.`
		);
	}

	const value = parseFloat(match[1]);
	const unit = match[2] as 's' | 'm' | 'h' | 'd';
	return Math.floor(value * timeUnits[unit]);
}

/**
 * Detect if image is a Space URL and extract spaceId
 * Returns { dockerImage } or { spaceId }
 */
export function parseImageSource(image: string): { dockerImage?: string; spaceId?: string } {
	const spacePrefixes = [
		'https://huggingface.co/spaces/',
		'https://hf.co/spaces/',
		'huggingface.co/spaces/',
		'hf.co/spaces/',
	];

	for (const prefix of spacePrefixes) {
		if (image.startsWith(prefix)) {
			return { spaceId: image.substring(prefix.length) };
		}
	}

	// Not a space, treat as docker image
	return { dockerImage: image };
}

/**
 * Parse command string or array into command array
 * Uses shell-quote library for proper POSIX-compliant parsing
 */
export function parseCommand(command: string | string[]): { command: string[]; arguments?: string[] } {
	// If already an array, return as-is
	if (Array.isArray(command)) {
		return { command, arguments: [] };
	}

	// Parse the command string using shell-quote for POSIX-compliant parsing
	const parsed = parseShellArgs<EnvToken>(command, key => ({ type: 'env', key }));

	// Convert parsed result to string array
	// shell-quote can return various types (strings, objects for operators, etc.)
	// We filter to only keep string arguments
	const stringArgs: string[] = [];
	for (const arg of parsed) {
		if (typeof arg === 'string') {
			stringArgs.push(arg);
		} else if (isEnvToken(arg)) {
			stringArgs.push(formatEnvReference(arg.key));
		} else {
			// If we encounter a non-string (like operators), throw an error
			throw new Error(
				`Unsupported shell syntax in command: "${command}". ` +
					`Please use an array format for commands with complex shell operators, ` +
					`or use simple quoted strings.`
			);
		}
	}

	if (stringArgs.length === 0) {
		throw new Error(`Invalid command: "${command}". Command cannot be empty.`);
	}

	return { command: stringArgs, arguments: [] };
}

/**
 * Replace HF token placeholder with actual token if available
 */
function replaceTokenPlaceholder(value: string, hfToken?: string): string {
	if (!hfToken) {
		return value;
	}

	if (value === '$HF_TOKEN' || value === '${HF_TOKEN}') {
		return hfToken;
	}

	return value;
}

function transformEnvMap(
	map: Record<string, string> | undefined,
	hfToken?: string
): Record<string, string> | undefined {
	if (!map) {
		return undefined;
	}

	const transformedEntries = Object.entries(map).map<[string, string]>(([key, value]) => [
		key,
		replaceTokenPlaceholder(value, hfToken),
	]);
	return Object.fromEntries(transformedEntries) as Record<string, string>;
}

/**
 * Create a JobSpec from run command arguments
 */
export function createJobSpec(args: {
	image: string;
	command: string | string[];
	flavor?: string;
	env?: Record<string, string>;
	secrets?: Record<string, string>;
	timeout?: string;
	hfToken?: string;
}): JobSpec {
	// Validate required fields
	if (!args.image) {
		throw new Error('image parameter is required. Provide a Docker image (e.g., "python:3.12") or Space URL.');
	}
	if (!args.command) {
		throw new Error('command parameter is required. Provide a command as string or array.');
	}

	const imageSource = parseImageSource(args.image);
	const { command, arguments: cmdArgs } = parseCommand(args.command);
	const timeoutSeconds = args.timeout ? parseTimeout(args.timeout) : undefined;
	const environment = transformEnvMap(args.env, args.hfToken) || {};
	const secrets = transformEnvMap(args.secrets, args.hfToken) || {};

	const spec: JobSpec = {
		...imageSource,
		command,
		arguments: cmdArgs,
		flavor: args.flavor || 'cpu-basic',
		environment,
		secrets,
		timeoutSeconds,
	};

	return spec;
}
