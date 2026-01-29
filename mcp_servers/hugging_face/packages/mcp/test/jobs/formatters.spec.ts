import { describe, it, expect } from 'vitest';
import { formatJobsTable, formatScheduledJobsTable, formatJobDetails } from '../../src/jobs/formatters.js';
import type { JobInfo, ScheduledJobInfo, JobSpec } from '../../src/jobs/types.js';

describe('Jobs Formatters', () => {
	describe('formatJobsTable', () => {
		it('should return message for empty job list', () => {
			const result = formatJobsTable([]);
			expect(result).toBe('No jobs found.');
		});

		it('should format a single job as markdown table', () => {
			const jobs: JobInfo[] = [
				{
					id: 'job123',
					createdAt: '2025-01-20T10:00:00Z',
					dockerImage: 'python:3.12',
					command: ['python', 'script.py'],
					flavor: 'cpu-basic',
					status: { stage: 'RUNNING' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
			];

			const result = formatJobsTable(jobs);

			// Should be a markdown table
			expect(result).toContain('| JOB ID');
			expect(result).toContain('| IMAGE/SPACE');
			expect(result).toContain('| COMMAND');
			expect(result).toContain('| CREATED');
			expect(result).toContain('| STATUS');

			// Should contain separator line
			expect(result).toContain('|---');

			// Should contain job data
			expect(result).toContain('job123');
			expect(result).toContain('python:3.12');
			expect(result).toContain('python script.py');
			expect(result).toContain('RUNNING');
		});

		it('should format multiple jobs', () => {
			const jobs: JobInfo[] = [
				{
					id: 'job123',
					createdAt: '2025-01-20T10:00:00Z',
					dockerImage: 'python:3.12',
					command: ['python', 'script.py'],
					flavor: 'cpu-basic',
					status: { stage: 'RUNNING' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
				{
					id: 'job456',
					createdAt: '2025-01-20T11:00:00Z',
					dockerImage: 'ubuntu',
					command: ['bash', 'test.sh'],
					flavor: 'a10g-small',
					status: { stage: 'COMPLETED' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
			];

			const result = formatJobsTable(jobs);

			// Should contain both jobs
			expect(result).toContain('job123');
			expect(result).toContain('job456');
			expect(result).toContain('python:3.12');
			expect(result).toContain('ubuntu');
			expect(result).toContain('RUNNING');
			expect(result).toContain('COMPLETED');
		});

		it('should handle Space IDs instead of Docker images', () => {
			const jobs: JobInfo[] = [
				{
					id: 'job789',
					createdAt: '2025-01-20T12:00:00Z',
					spaceId: 'user/myspace',
					command: ['python', 'app.py'],
					flavor: 'cpu-basic',
					status: { stage: 'RUNNING' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
			];

			const result = formatJobsTable(jobs);
			expect(result).toContain('user/myspace');
		});

		it('should truncate long values with ellipsis', () => {
			const jobs: JobInfo[] = [
				{
					id: 'a'.repeat(50),
					createdAt: '2025-01-20T10:00:00Z',
					dockerImage: 'very-long-image-name-that-exceeds-column-width',
					command: ['python', '-c', 'print(' + 'x'.repeat(100) + ')'],
					flavor: 'cpu-basic',
					status: { stage: 'RUNNING' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
			];

			const result = formatJobsTable(jobs);
			expect(result).toContain('...');
		});
	});

	describe('formatScheduledJobsTable', () => {
		it('should return message for empty scheduled job list', () => {
			const result = formatScheduledJobsTable([]);
			expect(result).toBe('No scheduled jobs found.');
		});

		it('should format a scheduled job as markdown table', () => {
			const jobSpec: JobSpec = {
				dockerImage: 'python:3.12',
				command: ['python', 'backup.py'],
				flavor: 'cpu-basic',
			};

			const jobs: ScheduledJobInfo[] = [
				{
					id: 'sched123',
					schedule: '@hourly',
					suspend: false,
					jobSpec,
					lastRun: '2025-01-20T10:00:00Z',
					nextRun: '2025-01-20T11:00:00Z',
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					createdAt: '2025-01-20T09:00:00Z',
				},
			];

			const result = formatScheduledJobsTable(jobs);

			// Should be a markdown table
			expect(result).toContain('| ID');
			expect(result).toContain('| SCHEDULE');
			expect(result).toContain('| IMAGE/SPACE');
			expect(result).toContain('| COMMAND');
			expect(result).toContain('| LAST RUN');
			expect(result).toContain('| NEXT RUN');
			expect(result).toContain('| SUSPENDED');

			// Should contain job data
			expect(result).toContain('sched123');
			expect(result).toContain('@hourly');
			expect(result).toContain('python:3.12');
			expect(result).toContain('No'); // Not suspended
		});

		it('should show Yes for suspended jobs', () => {
			const jobSpec: JobSpec = {
				dockerImage: 'ubuntu',
				command: ['bash', 'cleanup.sh'],
				flavor: 'cpu-basic',
			};

			const jobs: ScheduledJobInfo[] = [
				{
					id: 'sched456',
					schedule: '@daily',
					suspend: true,
					jobSpec,
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					createdAt: '2025-01-20T09:00:00Z',
				},
			];

			const result = formatScheduledJobsTable(jobs);
			expect(result).toContain('Yes'); // Suspended
		});
	});

	describe('formatJobDetails', () => {
		it('should format a single job as JSON in code block', () => {
			const job: JobInfo = {
				id: 'job123',
				createdAt: '2025-01-20T10:00:00Z',
				dockerImage: 'python:3.12',
				command: ['python', 'script.py'],
				flavor: 'cpu-basic',
				status: { stage: 'RUNNING', message: null },
				owner: { id: 'u123', name: 'testuser', type: 'user' },
				environment: {},
			};

			const result = formatJobDetails(job);

			// Should be wrapped in code block
			expect(result).toMatch(/^```json\n/);
			expect(result).toMatch(/\n```$/);

			// Should contain job data as JSON
			expect(result).toContain('"id": "job123"');
			expect(result).toContain('"dockerImage": "python:3.12"');
			expect(result).toContain('"stage": "RUNNING"');
		});

		it('should format multiple jobs as JSON array', () => {
			const jobs: JobInfo[] = [
				{
					id: 'job123',
					createdAt: '2025-01-20T10:00:00Z',
					dockerImage: 'python:3.12',
					command: ['python', 'script.py'],
					flavor: 'cpu-basic',
					status: { stage: 'RUNNING' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
				{
					id: 'job456',
					createdAt: '2025-01-20T11:00:00Z',
					dockerImage: 'ubuntu',
					command: ['bash', 'test.sh'],
					flavor: 'cpu-basic',
					status: { stage: 'COMPLETED' },
					owner: { id: 'u123', name: 'testuser', type: 'user' },
					environment: {},
				},
			];

			const result = formatJobDetails(jobs);

			// Should be wrapped in code block
			expect(result).toMatch(/^```json\n/);
			expect(result).toMatch(/\n```$/);

			// Should be an array
			expect(result).toContain('[');
			expect(result).toContain(']');

			// Should contain both jobs
			expect(result).toContain('"id": "job123"');
			expect(result).toContain('"id": "job456"');
		});

		it('should format JSON with proper indentation', () => {
			const job: JobInfo = {
				id: 'job123',
				createdAt: '2025-01-20T10:00:00Z',
				dockerImage: 'python:3.12',
				command: ['python', 'script.py'],
				flavor: 'cpu-basic',
				status: { stage: 'RUNNING' },
				owner: { id: 'u123', name: 'testuser', type: 'user' },
				environment: {},
			};

			const result = formatJobDetails(job);

			// Should have proper indentation (2 spaces)
			expect(result).toContain('  "id"');
			expect(result).toContain('  "createdAt"');
		});
	});
});
