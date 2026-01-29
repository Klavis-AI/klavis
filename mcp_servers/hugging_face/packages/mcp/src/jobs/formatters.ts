import type { JobInfo, ScheduledJobInfo } from './types.js';

/**
 * Truncate a string to a maximum length with ellipsis
 */
function truncate(str: string, maxLength: number): string {
	if (str.length <= maxLength) {
		return str;
	}
	return str.substring(0, maxLength - 3) + '...';
}

/**
 * Format a date string to a readable format
 */
function formatDate(dateStr: string | undefined): string {
	if (!dateStr) {
		return 'N/A';
	}
	try {
		const date = new Date(dateStr);
		return date.toISOString().replace('T', ' ').substring(0, 19);
	} catch {
		return dateStr;
	}
}

/**
 * Format command array as a single string
 */
function formatCommand(command?: string[]): string {
	if (!command || command.length === 0) {
		return 'N/A';
	}
	return command.join(' ');
}

/**
 * Get image/space identifier from job
 */
function getImageOrSpace(job: JobInfo | { dockerImage?: string; spaceId?: string }): string {
	if (job.spaceId) {
		return job.spaceId;
	}
	if (job.dockerImage) {
		return job.dockerImage;
	}
	return 'N/A';
}

/**
 * Format jobs as a markdown table
 */
export function formatJobsTable(jobs: JobInfo[]): string {
	if (jobs.length === 0) {
		return 'No jobs found.';
	}

	// Calculate dynamic ID column width - never truncate IDs!
	const longestIdLength = Math.max(...jobs.map((job) => job.id.length));
	const idColumnWidth = Math.max(longestIdLength, 'JOB ID'.length);

	// Define column widths
	const colWidths = {
		id: idColumnWidth,
		image: 20,
		command: 30,
		created: 19,
		status: 12,
	};

	// Build header
	const header = `| ${'JOB ID'.padEnd(colWidths.id)} | ${'IMAGE/SPACE'.padEnd(colWidths.image)} | ${'COMMAND'.padEnd(colWidths.command)} | ${'CREATED'.padEnd(colWidths.created)} | ${'STATUS'.padEnd(colWidths.status)} |`;
	const separator = `|${'-'.repeat(colWidths.id + 2)}|${'-'.repeat(colWidths.image + 2)}|${'-'.repeat(colWidths.command + 2)}|${'-'.repeat(colWidths.created + 2)}|${'-'.repeat(colWidths.status + 2)}|`;

	// Build rows
	const rows = jobs.map((job) => {
		const id = job.id; // Never truncate IDs!
		const image = truncate(getImageOrSpace(job), colWidths.image);
		const command = truncate(formatCommand(job.command), colWidths.command);
		const created = truncate(formatDate(job.createdAt), colWidths.created);
		const status = truncate(job.status.stage, colWidths.status);

		return `| ${id.padEnd(colWidths.id)} | ${image.padEnd(colWidths.image)} | ${command.padEnd(colWidths.command)} | ${created.padEnd(colWidths.created)} | ${status.padEnd(colWidths.status)} |`;
	});

	return [header, separator, ...rows].join('\n');
}

/**
 * Format scheduled jobs as a markdown table
 */
export function formatScheduledJobsTable(jobs: ScheduledJobInfo[]): string {
	if (jobs.length === 0) {
		return 'No scheduled jobs found.';
	}

	// Calculate dynamic ID column width - never truncate IDs!
	const longestIdLength = Math.max(...jobs.map((job) => job.id.length));
	const idColumnWidth = Math.max(longestIdLength, 'ID'.length);

	// Define column widths
	const colWidths = {
		id: idColumnWidth,
		schedule: 12,
		image: 18,
		command: 25,
		lastRun: 19,
		nextRun: 19,
		suspend: 9,
	};

	// Build header
	const header = `| ${'ID'.padEnd(colWidths.id)} | ${'SCHEDULE'.padEnd(colWidths.schedule)} | ${'IMAGE/SPACE'.padEnd(colWidths.image)} | ${'COMMAND'.padEnd(colWidths.command)} | ${'LAST RUN'.padEnd(colWidths.lastRun)} | ${'NEXT RUN'.padEnd(colWidths.nextRun)} | ${'SUSPENDED'.padEnd(colWidths.suspend)} |`;
	const separator = `|${'-'.repeat(colWidths.id + 2)}|${'-'.repeat(colWidths.schedule + 2)}|${'-'.repeat(colWidths.image + 2)}|${'-'.repeat(colWidths.command + 2)}|${'-'.repeat(colWidths.lastRun + 2)}|${'-'.repeat(colWidths.nextRun + 2)}|${'-'.repeat(colWidths.suspend + 2)}|`;

	// Build rows
	const rows = jobs.map((job) => {
		const id = job.id; // Never truncate IDs!
		const schedule = truncate(job.schedule, colWidths.schedule);
		const image = truncate(getImageOrSpace(job.jobSpec), colWidths.image);
		const command = truncate(formatCommand(job.jobSpec.command), colWidths.command);
		const lastRun = truncate(formatDate(job.lastRun), colWidths.lastRun);
		const nextRun = truncate(formatDate(job.nextRun), colWidths.nextRun);
		const suspend = job.suspend ? 'Yes' : 'No';

		return `| ${id.padEnd(colWidths.id)} | ${schedule.padEnd(colWidths.schedule)} | ${image.padEnd(colWidths.image)} | ${command.padEnd(colWidths.command)} | ${lastRun.padEnd(colWidths.lastRun)} | ${nextRun.padEnd(colWidths.nextRun)} | ${suspend.padEnd(colWidths.suspend)} |`;
	});

	return [header, separator, ...rows].join('\n');
}

/**
 * Format job details as JSON in a markdown code block
 */
export function formatJobDetails(jobs: JobInfo | JobInfo[]): string {
	const jobArray = Array.isArray(jobs) ? jobs : [jobs];
	const json = JSON.stringify(jobArray, null, 2);
	return `\`\`\`json\n${json}\n\`\`\``;
}

/**
 * Format scheduled job details as JSON in a markdown code block
 */
export function formatScheduledJobDetails(jobs: ScheduledJobInfo | ScheduledJobInfo[]): string {
	const jobArray = Array.isArray(jobs) ? jobs : [jobs];
	const json = JSON.stringify(jobArray, null, 2);
	return `\`\`\`json\n${json}\n\`\`\``;
}
