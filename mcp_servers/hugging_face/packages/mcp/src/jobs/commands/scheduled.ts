import type {
	ScheduledRunArgs,
	ScheduledUvArgs,
	ScheduledPsArgs,
	ScheduledJobArgs,
	ScheduledJobSpec,
} from '../types.js';
import type { JobsApiClient } from '../api-client.js';
import { formatScheduledJobsTable, formatScheduledJobDetails } from '../formatters.js';
import { createJobSpec } from './utils.js';
import { resolveUvCommand, UV_DEFAULT_IMAGE } from './uv-utils.js';

/**
 * Execute 'scheduled run' command
 * Creates a scheduled job
 */
export async function scheduledRunCommand(
	args: ScheduledRunArgs,
	client: JobsApiClient,
	token?: string
): Promise<string> {
	// Create job spec
	const jobSpec = createJobSpec({
		image: args.image,
		command: args.command,
		flavor: args.flavor,
		env: args.env,
		secrets: args.secrets,
		timeout: args.timeout,
		hfToken: token,
	});

	// Create scheduled job spec
	const scheduledSpec: ScheduledJobSpec = {
		schedule: args.schedule,
		suspend: args.suspend,
		jobSpec,
	};

	// Submit scheduled job
	const scheduledJob = await client.createScheduledJob(scheduledSpec, args.namespace);

	return `✓ Scheduled job created successfully!

**Scheduled Job ID:** ${scheduledJob.id}
**Schedule:** ${scheduledJob.schedule}
**Suspended:** ${scheduledJob.suspend ? 'Yes' : 'No'}
**Next Run:** ${scheduledJob.nextRun || 'N/A'}

	To inspect, call this tool with \`{"operation": "scheduled inspect", "args": {"scheduled_job_id": "${scheduledJob.id}"}}\`
	To list all, call this tool with \`{"operation": "scheduled ps"}\``;
}

/**
 * Execute 'scheduled uv' command
 * Creates a scheduled UV job
 */
export async function scheduledUvCommand(
	args: ScheduledUvArgs,
	client: JobsApiClient,
	token?: string
): Promise<string> {
	// For UV, use standard UV image
	const image = UV_DEFAULT_IMAGE;

	// Build UV command (similar to regular uv command)
	const command = resolveUvCommand(args);

	// Convert to scheduled run args
	const scheduledRunArgs: ScheduledRunArgs = {
		schedule: args.schedule,
		suspend: args.suspend,
		image,
		command,
		flavor: args.flavor,
		env: args.env,
		secrets: args.secrets,
		timeout: args.timeout,
		detach: args.detach,
		namespace: args.namespace,
	};

	return scheduledRunCommand(scheduledRunArgs, client, token);
}

/**
 * Execute 'scheduled ps' command
 * Lists scheduled jobs
 */
export async function scheduledPsCommand(args: ScheduledPsArgs, client: JobsApiClient): Promise<string> {
	// Fetch all scheduled jobs
	const allJobs = await client.listScheduledJobs(args.namespace);

	// Filter jobs
	let jobs = allJobs;

	// Default: hide suspended jobs unless --all is specified
	if (!args.all) {
		jobs = jobs.filter((job) => !job.suspend);
	}

	// Format as markdown table
	const table = formatScheduledJobsTable(jobs);

	if (jobs.length === 0) {
		if (args.all) {
			return 'No scheduled jobs found.';
		}
		return 'No active scheduled jobs found. Use `{"args": {"all": true}}` to show suspended jobs.';
	}

	return `**Scheduled Jobs (${jobs.length} of ${allJobs.length} total):**

${table}`;
}

/**
 * Execute 'scheduled inspect' command
 * Gets details of a scheduled job
 */
export async function scheduledInspectCommand(args: ScheduledJobArgs, client: JobsApiClient): Promise<string> {
	const job = await client.getScheduledJob(args.scheduled_job_id, args.namespace);
	const formattedDetails = formatScheduledJobDetails(job);
	return `**Scheduled Job Details:**\n\n${formattedDetails}`;
}

/**
 * Execute 'scheduled delete' command
 * Deletes a scheduled job
 */
export async function scheduledDeleteCommand(args: ScheduledJobArgs, client: JobsApiClient): Promise<string> {
	await client.deleteScheduledJob(args.scheduled_job_id, args.namespace);

	return `✓ Scheduled job ${args.scheduled_job_id} has been deleted.`;
}

/**
 * Execute 'scheduled suspend' command
 * Suspends a scheduled job
 */
export async function scheduledSuspendCommand(args: ScheduledJobArgs, client: JobsApiClient): Promise<string> {
	await client.suspendScheduledJob(args.scheduled_job_id, args.namespace);

	return `✓ Scheduled job ${args.scheduled_job_id} has been suspended.

To resume, call this tool with \`{"operation": "scheduled resume", "args": {"scheduled_job_id": "${args.scheduled_job_id}"}}\``;
}

/**
 * Execute 'scheduled resume' command
 * Resumes a suspended scheduled job
 */
export async function scheduledResumeCommand(args: ScheduledJobArgs, client: JobsApiClient): Promise<string> {
	await client.resumeScheduledJob(args.scheduled_job_id, args.namespace);

	return `✓ Scheduled job ${args.scheduled_job_id} has been resumed.

To inspect, call this tool with \`{"operation": "scheduled inspect", "args": {"scheduled_job_id": "${args.scheduled_job_id}"}}\``;
}
