/**
 * @fileoverview A factory for registering standardized MCP resources from definitions.
 * Encapsulates context creation, error handling, and response formatting, keeping
 * resource logic pure and stateless.
 * @module src/mcp-server/resources/utils/resourceHandlerFactory
 */
import {
  McpServer,
  ResourceTemplate,
} from '@modelcontextprotocol/sdk/server/mcp.js';
import type { ReadResourceResult } from '@modelcontextprotocol/sdk/types.js';
import type { ZodObject, ZodRawShape, z } from 'zod';

import type { ResourceDefinition } from '@/mcp-server/resources/utils/resourceDefinition.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import {
  ErrorHandler,
  type RequestContext,
  logger,
  requestContextService,
} from '@/utils/index.js';

/** Default formatter producing a single JSON text content block. */
type ResponseFormatter = (
  result: unknown,
  meta: { uri: URL; mimeType: string },
) => ReadResourceResult['contents'];

function defaultResponseFormatter(
  result: unknown,
  meta: { uri: URL; mimeType: string },
): ReadResourceResult['contents'] {
  return [
    {
      uri: meta.uri.href,
      text: JSON.stringify(result),
      mimeType: meta.mimeType,
    },
  ];
}

function ensureResourceContents(
  contents: unknown,
  handlerContext: RequestContext,
  resourceName: string,
  uri: URL,
): ReadResourceResult['contents'] {
  if (!Array.isArray(contents)) {
    throw new McpError(
      JsonRpcErrorCode.InternalError,
      'Resource formatter must return an array of contents.',
      {
        requestId: handlerContext.requestId,
        resourceName,
        uri: uri.href,
      },
    );
  }

  // We perform a shallow validation here. A full Zod schema validation would be safer
  // but might be too slow for every resource call. This is a pragmatic trade-off.
  for (const item of contents) {
    if (typeof item !== 'object' || item === null || !('uri' in item)) {
      throw new McpError(
        JsonRpcErrorCode.InternalError,
        'Invalid content block found in resource formatter output. Each item must be an object with a `uri` property.',
        {
          requestId: handlerContext.requestId,
          resourceName,
          uri: uri.href,
        },
      );
    }
  }

  return contents as ReadResourceResult['contents'];
}

/**
 * Registers a single resource definition with the provided MCP server.
 */
export async function registerResource<
  TParamsSchema extends ZodObject<ZodRawShape>,
  TOutputSchema extends ZodObject<ZodRawShape> | undefined = undefined,
>(
  server: McpServer,
  def: ResourceDefinition<TParamsSchema, TOutputSchema>,
): Promise<void> {
  const resourceName = def.name;
  const registrationContext: RequestContext =
    requestContextService.createRequestContext({
      operation: 'RegisterResource',
      additionalContext: { resourceName },
    });

  logger.info(`Registering resource: '${resourceName}'`, registrationContext);

  await ErrorHandler.tryCatch(
    () => {
      const template = new ResourceTemplate(def.uriTemplate, {
        list: def.list,
      });

      const mimeType = def.mimeType ?? 'application/json';
      const formatter: ResponseFormatter =
        def.responseFormatter ?? defaultResponseFormatter;
      const title = def.title ?? resourceName;

      server.resource(
        resourceName,
        template,
        {
          name: title,
          description: def.description,
          mimeType,
          ...(def.examples && { examples: def.examples }),
        },
        async (uri, params, callContext): Promise<ReadResourceResult> => {
          const sessionId =
            typeof callContext?.sessionId === 'string'
              ? callContext.sessionId
              : undefined;

          const handlerContext: RequestContext =
            requestContextService.createRequestContext({
              parentContext: callContext,
              operation: 'HandleResourceRead',
              additionalContext: {
                resourceUri: uri.href,
                sessionId,
                inputParams: params,
              },
            });

          try {
            // Validate params via the schema before invoking logic
            type TParams = z.infer<TParamsSchema>;
            type TOutput =
              TOutputSchema extends ZodObject<ZodRawShape>
                ? z.infer<TOutputSchema>
                : unknown;
            const parsedParams = def.paramsSchema.parse(params) as TParams;
            const responseData = (await def.logic(
              uri,
              parsedParams,
              handlerContext,
            )) as TOutput;

            const rawContents: unknown = formatter(responseData, {
              uri,
              mimeType,
            });

            const contents = ensureResourceContents(
              rawContents,
              handlerContext,
              resourceName,
              uri,
            );

            const readResult: ReadResourceResult = { contents };
            return readResult;
          } catch (error) {
            // Centralized handler re-throws the error for the SDK to catch
            throw ErrorHandler.handleError(error, {
              operation: `resource:${resourceName}:readHandler`,
              context: handlerContext,
              input: { uri: uri.href, params },
            });
          }
        },
      );

      logger.notice(
        `Resource '${resourceName}' registered successfully.`,
        registrationContext,
      );
    },
    {
      operation: `RegisteringResource_${resourceName}`,
      context: registrationContext,
      errorCode: JsonRpcErrorCode.InitializationFailed,
      critical: true,
    },
  );
}
