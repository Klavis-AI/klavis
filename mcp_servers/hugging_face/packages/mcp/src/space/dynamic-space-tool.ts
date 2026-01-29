import type { ToolResult } from '../types/tool-result.js';
import type { ServerNotification, ServerRequest } from '@modelcontextprotocol/sdk/types.js';
import type { RequestHandlerExtra } from '@modelcontextprotocol/sdk/shared/protocol.js';
import type { z } from 'zod';
import {
	spaceArgsSchema,
	type SpaceArgs,
	type InvokeResult,
	isDynamicSpaceMode,
	getOperationNames,
	getSpaceArgsSchema,
	VIEW_PARAMETERS,
	FILE_HANDLING_TEXT,
} from './types.js';
import { findSpaces } from './commands/dynamic-find.js';
import { discoverSpaces } from './commands/discover.js';
import { viewParameters } from './commands/view-parameters.js';
import { invokeSpace } from './commands/invoke.js';

// Re-export types (including InvokeResult for external use)
export * from './types.js';

/**
 * Usage instructions when tool is called with no operation
 */
const USAGE_INSTRUCTIONS = `# Gradio Space Interaction

Dynamically interact with any Gradio MCP Space. Find spaces, view space parameter schemas, and invoke spaces.
- Enums (predefined value sets)
- Arrays of primitives
- Shallow objects (one level deep)
- FileData (as URL strings)

To use spaces with complex schemas, add them from huggingface.co/settings/mcp.

## Available Operations

### Find
Find MCP-enabled Spaces for available for invocation based on task-focused or semantic searches.

**Example:**
\`\`\`json
{
  "operation": "find",
  "search_query": "image generation",
  "limit": 10
}
\`\`\`

### ${VIEW_PARAMETERS}
Display the parameter schema for a space's first tool.

**Example:**
\`\`\`json
{
  "operation": "${VIEW_PARAMETERS}",
  "space_name": "evalstate/FLUX1_schnell"
}
\`\`\`

### invoke
Execute a space's first tool with provided parameters.

**Example:**
\`\`\`json
{
  "operation": "invoke",
  "space_name": "evalstate/FLUX1_schnell",
  "parameters": "{\\"prompt\\": \\"a cute cat\\", \\"num_steps\\": 4}"
}
\`\`\`

## Workflow

1. **Find Spaces** - Use \`find\` to find MCP-enabled spaces for your task
2. **Inspect Parameters** - Use \`${VIEW_PARAMETERS}\` to see what a space accepts
3. **Invoke the Space** - Use \`invoke\` with the required parameters
For parameters that accept files (FileData types):
- Provide a publicly accessible URL (http:// or https://)
- Example: \`{"image": "https://example.com/photo.jpg"}\`
- The tool automatically applies default values for optional parameters
- Unknown parameters generate warnings but are still passed through (permissive inputs)
- Enum parameters show all allowed values in ${VIEW_PARAMETERS} output
- Required parameters are clearly marked and validated
`;

/**
 * Usage instructions for dynamic mode (when DYNAMIC_SPACE_DATA is set)
 */
const DYNAMIC_USAGE_INSTRUCTIONS = `# Hugging Face Space Dynamic Use

Perform Tasks using Hugging Face Spaces. 

## Workflow

1. **Discover Taks and Spaces** - Use \`discover\` operation to see available spaces
2. **View Parameters** - Use \`${VIEW_PARAMETERS}\` operation to inspect parameter schema
3. **Invoke the Space** - Use \`invoke\` operation with the necessary parameters

${FILE_HANDLING_TEXT}

## Available Operations

### discover
List recommended spaces and their categories.

**Example:**
\`\`\`json
{
  "operation": "discover"
}
\`\`\`

### ${VIEW_PARAMETERS}
Display the parameter schema for the Space.

**Example:**
\`\`\`json
{
  "operation": "${VIEW_PARAMETERS}",
  "space_name": "evalstate/FLUX1_schnell"
}
\`\`\`

### invoke
Execute a Task on a Space.

**Example:**
\`\`\`json
{
  "operation": "invoke",
  "space_name": "evalstate/FLUX1_schnell",
  "parameters": "{\\"prompt\\": \\"a cute cat\\", \\"num_steps\\": 4}"
}
\`\`\`


`;

/**
 * Get the appropriate usage instructions based on mode
 */
function getUsageInstructions(): string {
	return isDynamicSpaceMode() ? DYNAMIC_USAGE_INSTRUCTIONS : USAGE_INSTRUCTIONS;
}

/**
 * Space tool configuration
 * Returns dynamic config based on environment
 */
export function getDynamicSpaceToolConfig(): {
	name: string;
	description: string;
	schema: z.ZodObject<z.ZodRawShape>;
	annotations: { title: string; readOnlyHint: boolean; openWorldHint: boolean };
} {
	const dynamicMode = isDynamicSpaceMode();
	return {
		name: 'dynamic_space',
		description: dynamicMode
			? 'Perform Tasks with Hugging Face Spaces. Use "discover" to view available Tasks. Examples are Image Generation/Editing, Background Removal, Text to Speech, OCR and many more. ' +
				'Call with no arguments for full usage instructions.'
			: 'Find (semantic/task search), inspect (view parameter schema) and dynamically invoke Hugging Face Spaces. ' +
				'Call with no arguments for full usage instructions.',
		schema: getSpaceArgsSchema(),
		annotations: {
			title: 'Dynamically use Hugging Face Spaces',
			readOnlyHint: false,
			openWorldHint: true,
		},
	};
}

/**
 * Space tool configuration (static, for backward compatibility)
 */
export const DYNAMIC_SPACE_TOOL_CONFIG = {
	name: 'dynamic_space',
	description:
		'Find (semantic/task search), inspect (view parameter schema) and dynamically invoke Hugging Face Spaces. ' +
		'Call with no operation for full usage instructions.',
	schema: spaceArgsSchema,
	annotations: {
		title: 'Dynamically use Hugging Face Spaces',
		readOnlyHint: false,
		openWorldHint: true,
	},
} as const;

/**
 * Space tool implementation
 */
export class SpaceTool {
	private hfToken?: string;

	constructor(hfToken?: string) {
		this.hfToken = hfToken;
	}

	/**
	 * Execute a space operation
	 * Returns InvokeResult (with raw MCP content) for invoke operation,
	 * or ToolResult (with formatted text) for other operations
	 */
	async execute(
		params: SpaceArgs,
		extra?: RequestHandlerExtra<ServerRequest, ServerNotification>
	): Promise<InvokeResult | ToolResult> {
		const requestedOperation = params.operation;

		// If no operation provided, return usage instructions
		if (!requestedOperation) {
			return {
				formatted: getUsageInstructions(),
				totalResults: 1,
				resultsShared: 1,
			};
		}

		// Validate operation
		const normalizedOperation = requestedOperation.toLowerCase();
		const validOperations = getOperationNames();
		if (!validOperations.includes(normalizedOperation)) {
			return {
				formatted: `Unknown operation: "${requestedOperation}"
Available operations: ${validOperations.join(', ')}

Call this tool with no operation for full usage instructions.`,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		// Execute operation
		try {
			switch (normalizedOperation) {
				case 'find':
					return await this.handleFind(params);

				case 'discover':
					return await this.handleDiscover();

				case 'view_parameters':
					return await this.handleViewParameters(params);

				case 'invoke':
					return await this.handleInvoke(params, extra);

				default:
					return {
						formatted: `Unknown operation: "${requestedOperation}"`,
						totalResults: 0,
						resultsShared: 0,
						isError: true,
					};
			}
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);
			return {
				formatted: `Error executing ${requestedOperation}: ${errorMessage}`,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}
	}

	/**
	 * Handle find operation
	 */
	private async handleFind(params: SpaceArgs): Promise<ToolResult> {
		return await findSpaces(params.search_query, params.limit, this.hfToken);
	}

	/**
	 * Handle discover operation (for dynamic space mode)
	 */
	private async handleDiscover(): Promise<ToolResult> {
		return await discoverSpaces();
	}

	/**
	 * Handle view_parameters operation
	 */
	private async handleViewParameters(params: SpaceArgs): Promise<ToolResult> {
		if (!params.space_name) {
			return {
				formatted: `Error: Missing required parameter: "space_name"

Example:
\`\`\`json
{
  "operation": "${VIEW_PARAMETERS}",
  "space_name": "username/space-name"
}
\`\`\``,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		return await viewParameters(params.space_name, this.hfToken);
	}

	/**
	 * Handle invoke operation
	 * Returns either InvokeResult (with raw MCP content) or ToolResult (error messages)
	 */
	private async handleInvoke(
		params: SpaceArgs,
		extra?: RequestHandlerExtra<ServerRequest, ServerNotification>
	): Promise<InvokeResult | ToolResult> {
		// Validate required parameters
		if (!params.space_name) {
			return {
				formatted: `Error: Missing required parameter: "space_name"

Example:
\`\`\`json
{
  "operation": "invoke",
  "space_name": "username/space-name",
  "parameters": "{\\"param1\\": \\"value1\\"}"
}
\`\`\``,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		if (!params.parameters) {
			return {
				formatted: `Error: Missing required parameter: "parameters"

The "parameters" field must be a JSON object string containing the space parameters.

Example:
\`\`\`json
{
  "operation": "invoke",
  "space_name": "${params.space_name}",
  "parameters": "{\\"param1\\": \\"value1\\", \\"param2\\": 42}"
}
\`\`\`

Use "${VIEW_PARAMETERS}" to see what parameters this space accepts.`,
				totalResults: 0,
				resultsShared: 0,
				isError: true,
			};
		}

		return await invokeSpace(params.space_name, params.parameters, this.hfToken, extra);
	}
}
