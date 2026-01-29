import type { PsArgs } from '../types.js';
import type { JobsApiClient } from '../api-client.js';
import { formatJobsTable } from '../formatters.js';

/**
 * Execute the 'ps' command
 * Lists jobs with optional filtering
 */
export async function psCommand(args: PsArgs, client: JobsApiClient): Promise<string> {
	// Fetch all jobs from API
	const allJobs = await client.listJobs(args.namespace);

	// Filter jobs
	let jobs = allJobs;

	// Default: show only running jobs unless --all is specified
	if (!args.all) {
		jobs = jobs.filter((job) => job.status.stage === 'RUNNING');
	}

	// Apply status filter if specified
	if (args.status) {
		const statusFilter = args.status.toUpperCase();
		jobs = jobs.filter((job) => job.status.stage.toUpperCase().includes(statusFilter));
	}

	// Format as markdown table
	const table = formatJobsTable(jobs);

	if (jobs.length === 0) {
		if (args.all) {
			return 'No jobs found.';
		}
		return 'No running jobs found. Use `{"args": {"all": true}}` to show all jobs.';
	}

	return `**Jobs (${jobs.length} of ${allJobs.length} total):**

${table}`;
}
