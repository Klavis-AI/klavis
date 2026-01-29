import { z } from 'zod';
import { JobsApiClient } from './api-client.js';
import { HfApiError } from '../hf-api-call.js';
import { runCommand, uvCommand } from './commands/run.js';
import { psCommand } from './commands/ps.js';
import { logsCommand } from './commands/logs.js';
import { inspectCommand, cancelCommand } from './commands/inspect.js';
import {
	scheduledRunCommand,
	scheduledUvCommand,
	scheduledPsCommand,
	scheduledInspectCommand,
	scheduledDeleteCommand,
	scheduledSuspendCommand,
	scheduledResumeCommand,
} from './commands/scheduled.js';
import { formatCommandHelp, extractFieldDetails, type AnyZodType } from './schema-help.js';
import type { ToolResult } from '../types/tool-result.js';
import { CPU_FLAVORS, GPU_FLAVORS, SPECIALIZED_FLAVORS } from './types.js';
import { DEFAULT_LOG_WAIT_SECONDS } from './sse-handler.js';
import type {
	RunArgs,
	UvArgs,
	PsArgs,
	LogsArgs,
	InspectArgs,
	CancelArgs,
	ScheduledRunArgs,
	ScheduledUvArgs,
	ScheduledPsArgs,
	ScheduledJobArgs,
} from './types.js';

// Re-export types
export * from './types.js';
export { JobsApiClient } from './api-client.js';

// Import Zod schemas for validation
import {
	runArgsSchema,
	uvArgsSchema,
	psArgsSchema,
	logsArgsSchema,
	inspectArgsSchema,
	cancelArgsSchema,
	scheduledRunArgsSchema,
	scheduledUvArgsSchema,
	scheduledPsArgsSchema,
	scheduledJobArgsSchema,
} from './types.js';

const OPERATION_NAMES = [
	'run',
	'uv',
	'ps',
	'logs',
	'inspect',
	'cancel',
	'scheduled run',
	'scheduled uv',
	'scheduled ps',
	'scheduled inspect',
	'scheduled delete',
	'scheduled suspend',
	'scheduled resume',
] as const;

type OperationName = (typeof OPERATION_NAMES)[number];

const OPERATION_EXAMPLES: Partial<Record<OperationName, string>> = {
	run: `{
  "operation": "run",
  "args": {
    "image": "python:3.12",
    "command": ["python", "-c", "print('Hello from HF Jobs!')"],
    "flavor": "cpu-basic"
  }
}`,
	uv: `{
  "operation": "uv",
  "args": {
    "script": "import random\\nprint(42 + random.randint(1, 5))"
  }
}`,
	ps: `{"operation": "ps"}`,
	logs: `{
  "operation": "logs",
  "args": {"job_id": "your-job-id"}
}`,
	inspect: `{
  "operation": "inspect",
  "args": {"job_id": "your-job-id"}
}`,
	cancel: `{
  "operation": "cancel",
  "args": {"job_id": "your-job-id"}
}`,
	'scheduled run': `{
  "operation": "scheduled run",
  "args": {
    "schedule": "@hourly",
    "image": "python:3.12",
    "command": ["python", "backup.py"]
  }
}`,
	'scheduled uv': `{
  "operation": "scheduled uv",
  "args": {
    "schedule": "0 9 * * 1-5",
    "script": "import datetime\\nprint('daily check', datetime.datetime.utcnow())"
  }
}`,
	'scheduled ps': `{"operation": "scheduled ps"}`,
	'scheduled inspect': `{
  "operation": "scheduled inspect",
  "args": {"scheduled_job_id": "your-scheduled-job-id"}
}`,
	'scheduled delete': `{
  "operation": "scheduled delete",
  "args": {"scheduled_job_id": "your-scheduled-job-id"}
}`,
	'scheduled suspend': `{
  "operation": "scheduled suspend",
  "args": {"scheduled_job_id": "your-scheduled-job-id"}
}`,
	'scheduled resume': `{
  "operation": "scheduled resume",
  "args": {"scheduled_job_id": "your-scheduled-job-id"}
}`,
};

/**
 * Map of operation names to their validation schemas
 */
const OPERATION_SCHEMAS: Record<OperationName, z.ZodSchema> = {
	run: runArgsSchema,
	uv: uvArgsSchema,
	ps: psArgsSchema,
	logs: logsArgsSchema,
	inspect: inspectArgsSchema,
	cancel: cancelArgsSchema,
	'scheduled run': scheduledRunArgsSchema,
	'scheduled uv': scheduledUvArgsSchema,
	'scheduled ps': scheduledPsArgsSchema,
	'scheduled inspect': scheduledJobArgsSchema,
	'scheduled delete': scheduledJobArgsSchema,
	'scheduled suspend': scheduledJobArgsSchema,
	'scheduled resume': scheduledJobArgsSchema,
};

const HELP_FLAG = 'help';
const operationRequiresArgsCache = new Map<OperationName, boolean>();

const CPU_FLAVOR_LIST = CPU_FLAVORS.join(', ');
const GPU_FLAVOR_LIST = GPU_FLAVORS.join(', ');
const SPECIALIZED_FLAVOR_LIST = SPECIALIZED_FLAVORS.join(', ');
const HARDWARE_FLAVORS_SECTION = [
	`**CPU:** ${CPU_FLAVOR_LIST}`,
	GPU_FLAVORS.length ? `**GPU:** ${GPU_FLAVOR_LIST}` : undefined,
	SPECIALIZED_FLAVORS.length ? `**Specialized:** ${SPECIALIZED_FLAVOR_LIST}` : undefined,
]
	.filter((line): line is string => Boolean(line))
	.join('\n');

function isHelpRequested(args: Record<string, unknown> | undefined): boolean {
	if (!args) {
		return false;
	}

	const helpValue = args[HELP_FLAG];
	return helpValue === true || helpValue === 'true';
}

function removeHelpFlag(args: Record<string, unknown> | undefined): Record<string, unknown> {
	if (!args || !(HELP_FLAG in args)) {
		return args ?? {};
	}

	const { [HELP_FLAG]: _ignored, ...rest } = args;
	return rest;
}

function isOperationName(value: string): value is OperationName {
	return (OPERATION_NAMES as readonly string[]).includes(value);
}

function formatExampleSnippet(operation: OperationName): string | undefined {
	const example = OPERATION_EXAMPLES[operation];
	if (!example) {
		return undefined;
	}

	return `Call this tool with:\n\`\`\`json\n${example}\n\`\`\``;
}

function renderExampleSection(title: string, operation: OperationName): string {
	const snippet = formatExampleSnippet(operation);
	if (!snippet) {
		return '';
	}

	return `### ${title}
${snippet}
`;
}

function operationRequiresArgs(operation: OperationName): boolean {
	const cached = operationRequiresArgsCache.get(operation);
	if (cached !== undefined) {
		return cached;
	}

	const schema = OPERATION_SCHEMAS[operation];
	if (!schema) {
		operationRequiresArgsCache.set(operation, false);
		return false;
	}

	const fields = extractFieldDetails(schema as AnyZodType);
	const requiresArgs = fields.some((field) => !field.isOptional);
	operationRequiresArgsCache.set(operation, requiresArgs);
	return requiresArgs;
}

function formatCommandHelpWithExample(operation: OperationName, schema: z.ZodSchema): string {
	let help = formatCommandHelp(operation, schema);
	const exampleSnippet = formatExampleSnippet(operation);

	if (exampleSnippet) {
		help += `\n\n### Example\n${exampleSnippet}`;
	}

	return help;
}

function extractTopLevelArgs(params: { [key: string]: unknown }): Record<string, unknown> {
	const legacyArgs: Record<string, unknown> = {};
	for (const [key, value] of Object.entries(params)) {
		if (key === 'operation' || key === 'args') {
			continue;
		}
		legacyArgs[key] = value;
	}
	return legacyArgs;
}

/**
 * Validate operation arguments against a Zod schema
 * Returns a ToolResult with detailed error message if validation fails
 */
function validateArgs<T extends z.ZodTypeAny>(
	schema: T,
	args: unknown,
	operationName: string
): { success: true; data: z.infer<T> } | { success: false; errorResult: ToolResult } {
	const result = schema.safeParse(args);

	if (result.success) {
		return { success: true, data: result.data as z.infer<T> };
	}

	// Format Zod errors into a helpful message
	const errors = result.error.errors;
	const missingFields: string[] = [];
	const invalidFields: string[] = [];

	for (const err of errors) {
		const field = err.path.join('.');
		if (err.code === 'invalid_type' && err.received === 'undefined') {
			missingFields.push(`  • ${field}: ${err.message}`);
		} else {
			invalidFields.push(`  • ${field}: ${err.message}`);
		}
	}

	let errorMessage = `Error: Invalid parameters for '${operationName}'\n\n`;

	if (missingFields.length > 0) {
		errorMessage += `Missing required parameters:\n${missingFields.join('\n')}\n\n`;
	}

	if (invalidFields.length > 0) {
		errorMessage += `Invalid parameters:\n${invalidFields.join('\n')}\n\n`;
	}

	errorMessage += `Call this tool with {"operation": "${operationName}", "args": {"help": true}} to see valid arguments.`;

	return {
		success: false,
		errorResult: {
			formatted: errorMessage,
			totalResults: 0,
			resultsShared: 0,
			isError: true,
		},
	};
}

/**
 * Usage instructions when tool is called with no arguments
 */
const USAGE_INSTRUCTIONS = `# HuggingFace Jobs API

Manage compute jobs on Hugging Face infrastructure.

## Available Commands

### Job Management
- **run** - Run a job with a Docker image
- **uv** - Run a Python script with UV (inline dependencies)
- **ps** - List jobs
- **logs** - Fetch job logs
- **inspect** - Get detailed job information
- **cancel** - Cancel a running job

### Scheduled Jobs
- **scheduled run** - Create a scheduled job
- **scheduled uv** - Create a scheduled UV job
- **scheduled ps** - List scheduled jobs
- **scheduled inspect** - Get scheduled job details
- **scheduled delete** - Delete a scheduled job
- **scheduled suspend** - Pause a scheduled job
- **scheduled resume** - Resume a suspended job

## Examples

${renderExampleSection('Run a simple job', 'run')}${renderExampleSection('Run a Python script with UV', 'uv')}

## Hardware Flavors

${HARDWARE_FLAVORS_SECTION}

## Command Format Guidelines

**Array format (default):**
- Recommended for every command—JSON keeps arguments intact (URLs with \`&\`, spaces, etc.)
- Use \`["/bin/sh", "-lc", "..."]\` when you need shell operators like \`&&\`, \`|\`, or redirections
- Works with any language: Python, bash, node, npm, uv, etc.

**String format (simple cases only):**
- Still accepted for backwards compatibility, parsed with POSIX shell semantics
- Rejects shell operators and can mis-handle characters such as \`&\`; switch to arrays when things turn complex
- \`$HF_TOKEN\` stays literal—forward it via \`secrets: { "HF_TOKEN": "$HF_TOKEN" }\`

**Multiline inline scripts:**
- Include newline characters directly in the argument (e.g., \`"first line\\nsecond line"\`)
- UV inline scripts are automatically base64-decoded inside the container; just send the raw script text

### Show command-specific help
Call this tool with:
\`\`\`json
{"operation": "<operation>", "args": {"help": true}}
\`\`\`

## Tips

- The uv-scripts organisation contains examples for common tasks. dataset_search {'author':'uv-scripts'}
- Jobs default to non-detached mode (tail logs for up to ${DEFAULT_LOG_WAIT_SECONDS}s or until completion). Set \`detach: true\` to return immediately.
- Prefer array commands to avoid shell parsing surprises
- To access private Hub assets, include \`secrets: { "HF_TOKEN": "$HF_TOKEN" }\` (or \`${'${HF_TOKEN}'}\`) to inject your auth token.
- When not detached, logs are time-limited (${DEFAULT_LOG_WAIT_SECONDS}s max or until job completes) - check job page for full logs
`;

/**
 * Jobs tool configuration
 */
export const HF_JOBS_TOOL_CONFIG = {
	name: 'hf_jobs',
	description:
		'Manage Hugging Face CPU/GPU compute jobs. Run commands in Docker containers, ' +
		'execute Python scripts with UV. List, schedule and monitor jobs/logs. ' +
		'Call this tool with no operation for full usage instructions and examples. ',
	schema: z.object({
		operation: z
			.enum(OPERATION_NAMES)
			.optional()
			.describe(`Operation to execute. Valid values: ${OPERATION_NAMES.map((cmd) => `"${cmd}"`).join(', ')}`),
		args: z.record(z.any()).optional().describe('Operation-specific arguments as a JSON object'),
	}),
	annotations: {
		title: 'Hugging Face Jobs', // omit destructive hint.
		readOnlyHint: false,
		openWorldHint: true,
	},
} as const;

/**
 * Jobs tool implementation
 */
export class HfJobsTool {
	private client: JobsApiClient;
	private hfToken?: string;
	private isAuthenticated: boolean;

	constructor(hfToken?: string, isAuthenticated?: boolean, namespace?: string) {
		this.hfToken = hfToken;
		this.isAuthenticated = isAuthenticated ?? !!hfToken;
		this.client = new JobsApiClient(hfToken, namespace);
	}

	/**
	 * Execute a jobs operation
	 */
	async execute(params: { operation?: string; args?: Record<string, unknown> }): Promise<ToolResult> {
		// If not authenticated, show upgrade message
		if (!this.isAuthenticated) {
			return {
				formatted:
					'Jobs are available for Pro, Team and Enterprise users. Go to https://huggingface.co/pricing to get started.',
				totalResults: 0,
				resultsShared: 0,
			};
		}

		const requestedOperation = params.operation;

		// If no operation provided, return usage instructions
		if (!requestedOperation) {
			return {
				formatted: USAGE_INSTRUCTIONS,
				totalResults: 1,
				resultsShared: 1,
			};
		}

		const normalizedOperation = requestedOperation.toLowerCase();
		if (!isOperationName(normalizedOperation)) {
			return {
				formatted: `Unknown operation: "${requestedOperation}"
Available operations:
- run, uv, ps, logs, inspect, cancel
- scheduled run, scheduled uv, scheduled ps, scheduled inspect, scheduled delete, scheduled suspend, scheduled resume

Call this tool with no operation for full usage instructions.`,
				totalResults: 0,
				resultsShared: 0,
			};
		}

		const operation = normalizedOperation;
		const legacyArgs = extractTopLevelArgs(params as Record<string, unknown>);
		const rawArgs = params.args ? params.args : Object.keys(legacyArgs).length > 0 ? legacyArgs : {};
		const schema = OPERATION_SCHEMAS[operation];
		const noArgsProvided = !params.args || Object.keys(params.args).length === 0;

		if (schema && noArgsProvided && operationRequiresArgs(operation)) {
			const helpText = formatCommandHelpWithExample(operation, schema);
			return {
				formatted: `No arguments provided for "${operation}".\n\n${helpText}`,
				totalResults: 1,
				resultsShared: 1,
			};
		}
		const helpRequested = isHelpRequested(rawArgs);

		if (helpRequested) {
			if (!schema) {
				return {
					formatted: `No help available for '${requestedOperation}'.`,
					totalResults: 0,
					resultsShared: 0,
				};
			}

			const helpText = formatCommandHelpWithExample(operation, schema);
			return {
				formatted: helpText,
				totalResults: 1,
				resultsShared: 1,
			};
		}

		const cleanedArgs = removeHelpFlag(rawArgs);
		let parsedArgs: Record<string, unknown> = cleanedArgs;

		// Validate operation arguments if schema exists
		if (schema) {
			const validation = validateArgs(schema, cleanedArgs, operation);
			if (!validation.success) {
				return validation.errorResult;
			}
			parsedArgs = validation.data as Record<string, unknown>;
		}

		try {
			let result: string;

			switch (operation) {
				case 'run':
					result = await runCommand(parsedArgs as RunArgs, this.client, this.hfToken);
					break;

				case 'uv':
					result = await uvCommand(parsedArgs as UvArgs, this.client, this.hfToken);
					break;

				case 'ps':
					result = await psCommand(parsedArgs as PsArgs, this.client);
					break;

				case 'logs':
					result = await logsCommand(parsedArgs as LogsArgs, this.client, this.hfToken);
					break;

				case 'inspect':
					result = await inspectCommand(parsedArgs as InspectArgs, this.client);
					break;

				case 'cancel':
					result = await cancelCommand(parsedArgs as CancelArgs, this.client);
					break;

				case 'scheduled run':
					result = await scheduledRunCommand(parsedArgs as ScheduledRunArgs, this.client, this.hfToken);
					break;

				case 'scheduled uv':
					result = await scheduledUvCommand(parsedArgs as ScheduledUvArgs, this.client, this.hfToken);
					break;

				case 'scheduled ps':
					result = await scheduledPsCommand(parsedArgs as ScheduledPsArgs, this.client);
					break;

				case 'scheduled inspect':
					result = await scheduledInspectCommand(parsedArgs as ScheduledJobArgs, this.client);
					break;

				case 'scheduled delete':
					result = await scheduledDeleteCommand(parsedArgs as ScheduledJobArgs, this.client);
					break;

				case 'scheduled suspend':
					result = await scheduledSuspendCommand(parsedArgs as ScheduledJobArgs, this.client);
					break;

				case 'scheduled resume':
					result = await scheduledResumeCommand(parsedArgs as ScheduledJobArgs, this.client);
					break;

				default:
					return {
						formatted: `Unknown operation: "${requestedOperation ?? 'unknown'}"
Available operations:
- run, uv, ps, logs, inspect, cancel
- scheduled run, scheduled uv, scheduled ps, scheduled inspect, scheduled delete, scheduled suspend, scheduled resume

Call this tool with no operation for full usage instructions.`,
						totalResults: 0,
						resultsShared: 0,
					};
			}

			return {
				formatted: result,
				totalResults: 1,
				resultsShared: 1,
			};
		} catch (error) {
			let errorMessage = error instanceof Error ? error.message : String(error);

			// If this is an HfApiError with a response body, include it
			if (error instanceof HfApiError && error.responseBody) {
				try {
					// Try to parse and format the response body
					const parsed: unknown = JSON.parse(error.responseBody);
					const formattedBody = JSON.stringify(parsed, null, 2);
					errorMessage += `\n\nServer response:\n${formattedBody}`;
				} catch {
					// If not valid JSON, include raw response (if not too long)
					if (error.responseBody.length < 500) {
						errorMessage += `\n\nServer response: ${error.responseBody}`;
					}
				}
			}

			return {
				formatted: `Error executing ${requestedOperation ?? 'operation'}: ${errorMessage}`,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}
	}
}
