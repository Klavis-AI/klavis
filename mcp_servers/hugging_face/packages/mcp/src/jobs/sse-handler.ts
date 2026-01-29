import type { LogEvent } from './types.js';

/**
 * Default duration to wait for logs when not detached (in milliseconds)
 */
export const DEFAULT_LOG_WAIT_MS = 10000; // 10 seconds

/**
 * Default duration to wait for logs when not detached (in seconds, for display)
 */
export const DEFAULT_LOG_WAIT_SECONDS = DEFAULT_LOG_WAIT_MS / 1000;

/**
 * Default maximum number of log lines to return
 */
export const DEFAULT_MAX_LOG_LINES = 20;

/**
 * Options for fetching logs via SSE
 */
export interface SseLogOptions {
	/** Maximum time to collect logs in milliseconds (default: 10000 = 10s) */
	maxDuration?: number;
	/** Maximum number of lines to return (default: 20) */
	maxLines?: number;
	/** HF API token for authentication */
	token?: string;
}

/**
 * Result from fetching logs
 */
export interface SseLogResult {
	/** Log lines collected */
	logs: string[];
	/** Whether the job finished during collection */
	finished: boolean;
	/** Whether collection was truncated due to timeout */
	truncated: boolean;
}

/**
 * Fetch logs from a job via Server-Sent Events (SSE)
 * Collects logs for a maximum duration and returns the last N lines
 *
 * @param url - The SSE endpoint URL for job logs
 * @param options - Options for log collection
 * @returns Log result with collected lines and status
 */
export async function fetchJobLogs(url: string, options: SseLogOptions = {}): Promise<SseLogResult> {
	const { maxDuration = DEFAULT_LOG_WAIT_MS, maxLines = DEFAULT_MAX_LOG_LINES, token } = options;

	const logLines: string[] = [];
	let finished = false;
	let truncated = false;

	// Create abort controller for timeout
	const controller = new AbortController();
	const timeoutId = setTimeout(() => {
		controller.abort();
		truncated = true;
	}, maxDuration);

	try {
		const headers: Record<string, string> = {
			Accept: 'text/event-stream',
		};
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		const response = await fetch(url, {
			headers,
			signal: controller.signal,
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch logs: ${response.status} ${response.statusText}`);
		}

		if (!response.body) {
			throw new Error('Response body is null');
		}

		// Process the SSE stream
		const reader = response.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

		while (true) {
			const { done, value } = await reader.read();

			if (done) {
				break;
			}

			// Decode chunk and add to buffer
			buffer += decoder.decode(value, { stream: true });

			// Process complete lines
			const lines = buffer.split('\n');
			buffer = lines.pop() || ''; // Keep incomplete line in buffer

			for (const line of lines) {
				// SSE format: "data: {json}"
				if (line.startsWith('data: ')) {
					try {
						const jsonStr = line.substring(6); // Remove "data: " prefix
						const event = JSON.parse(jsonStr) as LogEvent;

						// Filter out system messages
						if (event.data.startsWith('===== Job started')) {
							continue;
						}

						// Check for job finished message
						if (event.data.startsWith('===== Job finished')) {
							finished = true;
							// Extract status from message if present
							// e.g., "===== Job finished: status=COMPLETED ====="
							logLines.push(event.data);
							break;
						}

						// Add log line
						logLines.push(event.data);
					} catch {
						// Ignore malformed JSON
						continue;
					}
				}
			}

			// Break if job finished
			if (finished) {
				break;
			}
		}

		// Close the reader
		await reader.cancel();
	} catch (error) {
		// If aborted due to timeout, that's expected
		if ((error as Error).name !== 'AbortError') {
			throw error;
		}
	} finally {
		clearTimeout(timeoutId);
	}

	// Return last N lines
	const lastLines = logLines.slice(-maxLines);

	return {
		logs: lastLines,
		finished,
		truncated: truncated && !finished,
	};
}
