import { z } from 'zod';

/**
 * Hardware flavors available for jobs
 */
export const CPU_FLAVORS = ['cpu-basic', 'cpu-upgrade', 'cpu-performance', 'cpu-xl'] as const;

export const GPU_FLAVORS = [
	'sprx8',
	'zero-a10g',
	't4-small',
	't4-medium',
	'l4x1',
	'l4x4',
	'l40sx1',
	'l40sx4',
	'l40sx8',
	'a10g-small',
	'a10g-large',
	'a10g-largex2',
	'a10g-largex4',
	'a100-large',
	'h100',
	'h100x8',
] as const;

export const SPECIALIZED_FLAVORS = ['inf2x6'] as const;

export const ALL_FLAVORS = [...CPU_FLAVORS, ...GPU_FLAVORS, ...SPECIALIZED_FLAVORS] as const;

export type JobFlavor = (typeof ALL_FLAVORS)[number];

/**
 * Job status stages (from OpenAPI spec)
 */
export type JobStage = 'RUNNING' | 'COMPLETED' | 'CANCELED' | 'ERROR' | 'DELETED';

/**
 * Job status object from API
 */
export interface JobStatus {
	stage: JobStage;
	message?: string | null;
}

/**
 * Job owner information
 */
export interface JobOwner {
	id: string;
	name: string;
	type: 'user' | 'org';
}

/**
 * Job information from API
 * Based on OpenAPI schema
 */
export interface JobInfo {
	id: string;
	createdAt: string;
	dockerImage?: string;
	spaceId?: string;
	command?: string[];
	arguments?: string[];
	environment: Record<string, string>;
	secrets?: Record<string, string | null>;
	flavor: string;
	status: JobStatus;
	owner: JobOwner;
	createdBy?: JobOwner;
	tags?: string[];
	timeout?: number;
	// Additional fields not in OpenAPI but present in responses
	url?: string;
	endpoint?: string;
	finishedAt?: string;
}

/**
 * Job specification for creating jobs
 */
export interface JobSpec {
	dockerImage?: string;
	spaceId?: string;
	command: string[];
	arguments?: string[];
	environment?: Record<string, string>;
	secrets?: Record<string, string>;
	flavor: string;
	timeoutSeconds?: number;
}

/**
 * Scheduled job specification
 */
export interface ScheduledJobSpec {
	schedule: string;
	suspend?: boolean;
	jobSpec: JobSpec;
}

/**
 * Scheduled job information from API
 */
export interface ScheduledJobInfo {
	id: string;
	schedule: string;
	suspend: boolean;
	jobSpec: JobSpec;
	lastRun?: string;
	nextRun?: string;
	owner: JobOwner;
	createdAt: string;
}

/**
 * Log event from SSE stream
 */
export interface LogEvent {
	timestamp: string;
	data: string;
}

/**
 * Zod schemas for command arguments
 */

// Common args shared across commands
const commonArgsSchema = z.object({
	namespace: z.string().optional().describe('Target namespace (username or organization). Defaults to current user.'),
});

// Run command args
export const runArgsSchema = commonArgsSchema.extend({
	image: z
		.string()
		.describe('Docker image or HF Space URL (e.g., "python:3.12" or "hf.co/spaces/user/space")')
		.optional()
		.default('python:3.12'), // NOTE -- this is a deviation from the hf jobs command (which has no default)
	command: z
		.union([z.string(), z.array(z.string())])
		.describe(
			'Command to execute. Array format recommended (e.g., ["python", "script.py"]). ' +
				'String format is parsed with POSIX shell semantics (quotes, escaping). ' +
				'For multiline scripts, use array with newlines in arguments.'
		),
	flavor: z
		.enum(ALL_FLAVORS)
		.optional()
		.default('cpu-basic')
		.describe(`Hardware flavor. Options: ${ALL_FLAVORS.join(', ')}`),
	env: z.record(z.string()).optional().describe('Environment variables as key-value pairs'),
	secrets: z
		.record(z.string())
		.optional()
		.describe('Secrets as key-value pairs. Use HF_TOKEN=$HF_TOKEN to include your token'),
	timeout: z.string().optional().describe('Max duration (e.g., "5m", "2h", "30s"). Default: 30m').default('30m'),
	detach: z
		.boolean()
		.optional()
		.default(false)
		.describe('If true, return immediately with job ID. If false (default), tail logs for up to 10 seconds.'),
});

// UV command args
export const uvArgsSchema = commonArgsSchema.extend({
	script: z
		.string()
		.describe('Python script: local file path, URL, or inline code. UV will handle dependencies automatically.'),
	//	repo: z.string().optional().describe('Persistent repository name for script storage'), // consider reinstating if we decide to cache scripts
	with_deps: z.array(z.string()).optional().describe('Additional package dependencies'),
	script_args: z.array(z.string()).optional().describe('Arguments to pass to the script'),
	python: z.string().optional().describe('Python interpreter version (e.g., "3.12")'),
	flavor: z.enum(ALL_FLAVORS).optional().default('cpu-basic').describe('Hardware flavor'),
	env: z.record(z.string()).optional().describe('Environment variables as key-value pairs'),
	secrets: z
		.record(z.string())
		.optional()
		.describe('Secrets as key-value pairs. Use HF_TOKEN=$HF_TOKEN to include your token'),
	timeout: z.string().optional().default('30m').describe('Max duration'),
	detach: z.boolean().optional().default(false).describe('If true, return immediately with job ID. If false (default), tail logs for up to 10 seconds.'),
});

// PS command args
export const psArgsSchema = commonArgsSchema.extend({
	all: z.boolean().optional().default(false).describe('Show all jobs (default: only running)'),
	status: z.string().optional().describe('Filter by status ("RUNNING", "COMPLETED", "CANCELED", "ERROR", "DELETED")'),
});

// Logs command args
export const logsArgsSchema = commonArgsSchema.extend({
	job_id: z.string().describe('Job ID to fetch logs from'),
	tail: z.number().optional().default(20).describe('Number of lines to return (default: 20)'),
});

// Inspect command args
export const inspectArgsSchema = commonArgsSchema.extend({
	job_id: z.union([z.string(), z.array(z.string())]).describe('Job ID(s) to inspect'),
});

// Cancel command args
export const cancelArgsSchema = commonArgsSchema.extend({
	job_id: z.string().describe('Job ID to cancel'),
});

// Scheduled run args
export const scheduledRunArgsSchema = runArgsSchema.extend({
	schedule: z.string().describe('Schedule: cron expression or shorthand (@hourly, @daily, @weekly, @monthly, @yearly)'),
	suspend: z.boolean().optional().default(false).describe('Create in suspended state'),
});

// Scheduled UV args
export const scheduledUvArgsSchema = uvArgsSchema.extend({
	schedule: z.string().describe('Schedule: cron expression or shorthand'),
	suspend: z.boolean().optional().default(false).describe('Create in suspended state'),
});

// Scheduled PS args
export const scheduledPsArgsSchema = commonArgsSchema.extend({
	all: z.boolean().optional().default(false).describe('Show all scheduled jobs (default: hide suspended)'),
});

// Scheduled inspect/delete/suspend/resume args
export const scheduledJobArgsSchema = commonArgsSchema.extend({
	scheduled_job_id: z.string().describe('Scheduled job ID'),
});

/**
 * Export type aliases for use in commands
 */
export type RunArgs = z.infer<typeof runArgsSchema>;
export type UvArgs = z.infer<typeof uvArgsSchema>;
export type PsArgs = z.infer<typeof psArgsSchema>;
export type LogsArgs = z.infer<typeof logsArgsSchema>;
export type InspectArgs = z.infer<typeof inspectArgsSchema>;
export type CancelArgs = z.infer<typeof cancelArgsSchema>;
export type ScheduledRunArgs = z.infer<typeof scheduledRunArgsSchema>;
export type ScheduledUvArgs = z.infer<typeof scheduledUvArgsSchema>;
export type ScheduledPsArgs = z.infer<typeof scheduledPsArgsSchema>;
export type ScheduledJobArgs = z.infer<typeof scheduledJobArgsSchema>;
