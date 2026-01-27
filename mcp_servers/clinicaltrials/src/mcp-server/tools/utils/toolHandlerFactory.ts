/**
 * @fileoverview A factory for creating standardized MCP tool handlers.
 * This module abstracts away the boilerplate of error handling, context creation,
 * performance measurement, and response formatting for tool handlers.
 * @module mcp-server/tools/utils/toolHandlerFactory
 */
import type { SdkContext } from './toolDefinition.js';
import { McpError } from '@/types-global/errors.js';
import {
  ErrorHandler,
  type RequestContext,
  measureToolExecution,
  requestContextService,
} from '@/utils/index.js';
import type {
  CallToolResult,
  ContentBlock,
} from '@modelcontextprotocol/sdk/types.js';

// Define a type for a context that may have elicitation capabilities.
type ElicitableContext = RequestContext & {
  elicitInput?: (args: {
    message: string;
    schema: unknown;
  }) => Promise<unknown>;
};

// Default formatter for successful responses
const defaultResponseFormatter = (result: unknown): ContentBlock[] => [
  { type: 'text', text: JSON.stringify(result, null, 2) },
];

export type ToolHandlerFactoryOptions<
  TInput,
  TOutput extends Record<string, unknown>,
> = {
  toolName: string;
  logic: (
    input: TInput,
    appContext: RequestContext,
    sdkContext: SdkContext,
  ) => Promise<TOutput>;
  responseFormatter?: (result: TOutput) => ContentBlock[];
};

/**
 * Creates a standardized MCP tool handler.
 * This factory encapsulates context creation, performance measurement,
 * error handling, and response formatting. It separates the app's internal
 * RequestContext from the SDK's `callContext` (which we type as `SdkContext`).
 */
export function createMcpToolHandler<
  TInput,
  TOutput extends Record<string, unknown>,
>({
  toolName,
  logic,
  responseFormatter = defaultResponseFormatter,
}: ToolHandlerFactoryOptions<TInput, TOutput>) {
  return async (
    input: TInput,
    callContext: Record<string, unknown>,
  ): Promise<CallToolResult> => {
    // The `callContext` from the SDK is cast to our specific SdkContext type.
    const sdkContext = callContext as SdkContext;

    const sessionId =
      typeof sdkContext?.sessionId === 'string'
        ? sdkContext.sessionId
        : undefined;

    // Create the application's internal logger/tracing context.
    const appContext: ElicitableContext =
      requestContextService.createRequestContext({
        parentContext: sdkContext,
        operation: 'HandleToolRequest',
        additionalContext: { toolName, sessionId, input },
      });

    // If the SDK context supports elicitation, add it to our app context.
    // This makes it available to the tool's logic function.
    if (
      'elicitInput' in sdkContext &&
      typeof sdkContext.elicitInput === 'function'
    ) {
      appContext.elicitInput = sdkContext.elicitInput as (args: {
        message: string;
        schema: unknown;
      }) => Promise<unknown>;
    }

    try {
      const result = await measureToolExecution(
        // Pass both the app's internal context and the full SDK context to the logic.
        () => logic(input, appContext, sdkContext),
        { ...appContext, toolName },
        input,
      );

      return {
        structuredContent: result,
        content: responseFormatter(result),
      };
    } catch (error) {
      const mcpError = ErrorHandler.handleError(error, {
        operation: `tool:${toolName}`,
        context: appContext,
        input,
      }) as McpError;

      return {
        isError: true,
        content: [{ type: 'text', text: `Error: ${mcpError.message}` }],
        structuredContent: {
          code: mcpError.code,
          message: mcpError.message,
          data: mcpError.data,
        },
      };
    }
  };
}
