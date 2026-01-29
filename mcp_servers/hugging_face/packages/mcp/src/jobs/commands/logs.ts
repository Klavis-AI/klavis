import type { LogsArgs } from '../types.js';
import type { JobsApiClient } from '../api-client.js';
import { fetchJobLogs, DEFAULT_LOG_WAIT_MS, DEFAULT_LOG_WAIT_SECONDS } from '../sse-handler.js';

/**
 * Execute the 'logs' command
 * Fetches logs from a job via SSE
 */
export async function logsCommand(args: LogsArgs, client: JobsApiClient, token?: string): Promise<string> {
	// Get namespace for the logs URL
	const namespace = await client.getNamespace(args.namespace);
	const logsUrl = client.getLogsUrl(args.job_id, namespace);

	// Fetch logs with timeout and line limit
	const result = await fetchJobLogs(logsUrl, {
		token,
		maxDuration: DEFAULT_LOG_WAIT_MS,
		maxLines: args.tail,
	});

	if (result.logs.length === 0) {
		return `No logs available for job ${args.job_id}`;
	}

	let response = `**Logs for job ${args.job_id}** (last ${args.tail} lines):\n\n${'```'}\n`;
	response += result.logs.join('\n');
	response += `\n${'```'}`;

	if (result.finished) {
		response += '\n\n✓ Job finished.';
	} else if (result.truncated) {
		response += `\n\n⚠ Log collection stopped after ${DEFAULT_LOG_WAIT_SECONDS} seconds. Job may still be running.`;
	}

	return response;
}
