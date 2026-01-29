import type { InspectArgs, CancelArgs } from '../types.js';
import type { JobsApiClient } from '../api-client.js';
import { formatJobDetails } from '../formatters.js';

/**
 * Execute the 'inspect' command
 * Gets detailed information about one or more jobs
 */
export async function inspectCommand(args: InspectArgs, client: JobsApiClient): Promise<string> {
	const jobIds = Array.isArray(args.job_id) ? args.job_id : [args.job_id];

	// Fetch all jobs
	const jobs = await Promise.all(
		jobIds.map(async (id) => {
			try {
				return await client.getJob(id, args.namespace);
			} catch (error) {
				throw new Error(`Failed to fetch job ${id}: ${(error as Error).message}`);
			}
		})
	);

	const formattedDetails = formatJobDetails(jobs);

	return `**Job Details** (${jobs.length} job${jobs.length > 1 ? 's' : ''}):\n\n${formattedDetails}`;
}

/**
 * Execute the 'cancel' command
 * Cancels a running job
 */
export async function cancelCommand(args: CancelArgs, client: JobsApiClient): Promise<string> {
	await client.cancelJob(args.job_id, args.namespace);

	return `✓ Job ${args.job_id} has been cancelled.

To verify, call this tool with \`{"operation": "inspect", "args": {"job_id": "${args.job_id}"}}\``;
}
