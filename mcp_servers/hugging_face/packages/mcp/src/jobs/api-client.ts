import { HfApiCall } from '../hf-api-call.js';
import type { JobInfo, JobSpec, ScheduledJobInfo, ScheduledJobSpec } from './types.js';

/**
 * Interface for whoami API response
 */
interface WhoAmIResponse {
	name: string;
	id: string;
	type: 'user' | 'org';
	[key: string]: unknown;
}

/**
 * API client for HuggingFace Jobs API
 * Handles all HTTP interactions with the Jobs API endpoints
 */
export class JobsApiClient extends HfApiCall {
	private namespaceCache: string | null = null;

	constructor(hfToken?: string, namespace?: string) {
		// Base URL is the main HF API, we'll construct specific endpoints
		super('https://huggingface.co/api', hfToken);
		// Initialize cache with provided namespace to avoid redundant whoami calls
		this.namespaceCache = namespace || null;
	}

	/**
	 * Get the namespace (username or org) for the current user
	 * Uses cached value from constructor or /api/whoami-v2 endpoint as fallback
	 */
	async getNamespace(namespace?: string): Promise<string> {
		if (namespace) {
			return namespace;
		}

		if (this.namespaceCache) {
			return this.namespaceCache;
		}

		// Fetch from whoami endpoint only if not cached
		const whoami = await this.fetchFromApi<WhoAmIResponse>('https://huggingface.co/api/whoami-v2');
		this.namespaceCache = whoami.name;
		return this.namespaceCache;
	}

	/**
	 * Run a job
	 * POST /api/jobs/{namespace}
	 */
	async runJob(jobSpec: JobSpec, namespace?: string): Promise<JobInfo> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/jobs/${ns}`;

		const result = await this.fetchFromApi<JobInfo>(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(jobSpec),
		});
		return result;
	}

	/**
	 * List all jobs for a namespace
	 * GET /api/jobs/{namespace}
	 */
	async listJobs(namespace?: string): Promise<JobInfo[]> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/jobs/${ns}`;

		return this.fetchFromApi<JobInfo[]>(url);
	}

	/**
	 * Get detailed information about a specific job
	 * GET /api/jobs/{namespace}/{jobId}
	 */
	async getJob(jobId: string, namespace?: string): Promise<JobInfo> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/jobs/${ns}/${jobId}`;

		return this.fetchFromApi<JobInfo>(url);
	}

	/**
	 * Cancel a running job
	 * POST /api/jobs/{namespace}/{jobId}/cancel
	 */
	async cancelJob(jobId: string, namespace?: string): Promise<void> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/jobs/${ns}/${jobId}/cancel`;

		await this.fetchFromApi<void>(url, {
			method: 'POST',
		});
	}

	/**
	 * Get logs URL for a job
	 * Returns the URL for SSE streaming - caller handles the actual streaming
	 */
	getLogsUrl(jobId: string, namespace: string): string {
		return `https://huggingface.co/api/jobs/${namespace}/${jobId}/logs`;
	}

	/**
	 * Create a scheduled job
	 * POST /api/scheduled-jobs/{namespace}
	 */
	async createScheduledJob(spec: ScheduledJobSpec, namespace?: string): Promise<ScheduledJobInfo> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}`;

		return this.fetchFromApi<ScheduledJobInfo>(url, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(spec),
		});
	}

	/**
	 * List all scheduled jobs
	 * GET /api/scheduled-jobs/{namespace}
	 */
	async listScheduledJobs(namespace?: string): Promise<ScheduledJobInfo[]> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}`;

		return this.fetchFromApi<ScheduledJobInfo[]>(url);
	}

	/**
	 * Get details of a scheduled job
	 * GET /api/scheduled-jobs/{namespace}/{scheduledJobId}
	 */
	async getScheduledJob(scheduledJobId: string, namespace?: string): Promise<ScheduledJobInfo> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}/${scheduledJobId}`;
		console.error(url);
		return this.fetchFromApi<ScheduledJobInfo>(url);
	}

	/**
	 * Delete a scheduled job
	 * DELETE /api/scheduled-jobs/{namespace}/{scheduledJobId}
	 */
	async deleteScheduledJob(scheduledJobId: string, namespace?: string): Promise<void> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}/${scheduledJobId}`;

		await this.fetchFromApi<void>(url, {
			method: 'DELETE',
		});
	}

	/**
	 * Suspend a scheduled job
	 * POST /api/scheduled-jobs/{namespace}/{scheduledJobId}/suspend
	 */
	async suspendScheduledJob(scheduledJobId: string, namespace?: string): Promise<void> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}/${scheduledJobId}/suspend`;

		await this.fetchFromApi<void>(url, {
			method: 'POST',
		});
	}

	/**
	 * Resume a suspended scheduled job
	 * POST /api/scheduled-jobs/{namespace}/{scheduledJobId}/resume
	 */
	async resumeScheduledJob(scheduledJobId: string, namespace?: string): Promise<void> {
		const ns = await this.getNamespace(namespace);
		const url = `https://huggingface.co/api/scheduled-jobs/${ns}/${scheduledJobId}/resume`;

		await this.fetchFromApi<void>(url, {
			method: 'POST',
		});
	}
}
