import { describe, expect, it, vi } from 'vitest';
import { uvCommand } from '../../src/jobs/commands/run.js';
import type { JobsApiClient } from '../../src/jobs/api-client.js';
import type { JobInfo, JobSpec } from '../../src/jobs/types.js';

function setupMockClient() {
	let capturedSpec: JobSpec | undefined;

	const runJob = vi.fn(async (spec: JobSpec) => {
		capturedSpec = spec;
		const job: JobInfo = {
			id: 'job-123',
			createdAt: new Date().toISOString(),
			command: spec.command,
			arguments: spec.arguments,
			environment: spec.environment ?? {},
			secrets: {},
			flavor: spec.flavor,
			status: { stage: 'RUNNING' },
			owner: { id: 'owner-1', name: 'tester', type: 'user' },
		};
		return job;
	});

	const getLogsUrl = vi.fn(() => 'https://example.test/logs');

	const client = {
		runJob,
		getLogsUrl,
	} as unknown as JobsApiClient;

	return {
		client,
		runJob,
		getLogsUrl,
		get lastSpec() {
			return capturedSpec;
		},
	};
}

describe('uvCommand', () => {
	it('wraps inline scripts in a shell pipeline executed via /bin/sh', async () => {
		const harness = setupMockClient();
		const script = 'print("hello")\nprint("world")';

		await uvCommand({ script, detach: true }, harness.client);

		expect(harness.runJob).toHaveBeenCalledTimes(1);
		expect(harness.lastSpec).toBeDefined();
		expect(harness.lastSpec?.command).toEqual([
			'/bin/sh',
			'-lc',
			expect.stringContaining('uv run'),
		]);

		const encoded = Buffer.from(script).toString('base64');
		expect(harness.lastSpec?.command?.[2]).toContain(`echo "${encoded}" | base64 -d | uv run`);
		expect(harness.lastSpec?.command?.[2]).toContain(' -');
	});

	it('includes dependency and python flags when provided', async () => {
		const harness = setupMockClient();
		const script = 'print("deps")\nprint("python")';

		await uvCommand(
			{
				script,
				with_deps: ['numpy', 'pandas'],
				python: '3.12',
				detach: true,
			},
			harness.client
		);

		const shellCommand = harness.lastSpec?.command?.[2];
		expect(shellCommand).toContain('--with numpy');
		expect(shellCommand).toContain('--with pandas');
		expect(shellCommand).toContain('-p 3.12');
	});
});
