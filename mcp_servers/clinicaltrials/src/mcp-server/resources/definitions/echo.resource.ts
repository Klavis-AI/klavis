/**
 * @fileoverview Echo resource definition using the new declarative pattern.
 * Provides a pure logic function and schema-driven params, registered via the
 * generic resource registrar.
 * @module src/mcp-server/resources/definitions/echo.resource
 */
import { z } from 'zod';

import { type RequestContext, logger } from '@/utils/index.js';
import { withResourceAuth } from '@/mcp-server/transports/auth/lib/withAuth.js';
import { type ResourceDefinition } from '@/mcp-server/resources/utils/resourceDefinition.js';

const ParamsSchema = z
  .object({
    message: z
      .string()
      .optional()
      .describe(
        'Optional message to echo back. If omitted, it may be derived from the URI path/host.',
      ),
  })
  .describe('Echo resource parameters.');

const OutputSchema = z
  .object({
    message: z.string().describe('The echoed message.'),
    timestamp: z
      .string()
      .datetime()
      .describe('ISO 8601 timestamp when the response was generated.'),
    requestUri: z
      .string()
      .url()
      .describe('The request URI used to fetch this resource.'),
  })
  .describe('Echo resource response payload.');

type EchoParams = z.infer<typeof ParamsSchema>;
type EchoOutput = z.infer<typeof OutputSchema>;

function echoLogic(
  uri: URL,
  params: EchoParams,
  context: RequestContext,
): EchoOutput {
  const messageFromPath = uri.hostname || uri.pathname.replace(/^\/+/, '');
  const messageToEcho =
    params.message || messageFromPath || 'Default echo message';

  logger.debug('Processing echo resource logic.', {
    ...context,
    resourceUri: uri.href,
    extractedMessage: messageToEcho,
  });

  const responsePayload: EchoOutput = {
    message: messageToEcho,
    timestamp: new Date().toISOString(),
    requestUri: uri.href,
  };

  logger.debug('Echo resource processed successfully.', {
    ...context,
    responsePayloadSummary: {
      messageLength: responsePayload.message.length,
    },
  });

  return responsePayload;
}

export const echoResourceDefinition: ResourceDefinition<
  typeof ParamsSchema,
  typeof OutputSchema
> = {
  name: 'echo-resource',
  title: 'Echo Message Resource',
  description: 'A simple echo resource that returns a message.',
  uriTemplate: 'echo://{message}',
  paramsSchema: ParamsSchema,
  outputSchema: OutputSchema,
  mimeType: 'application/json',
  examples: [{ name: 'Basic echo', uri: 'echo://hello' }],
  annotations: { readOnlyHint: true },
  list: () => ({
    resources: [
      {
        uri: 'echo://hello',
        name: 'Default Echo Message',
        description: 'A simple echo resource example.',
      },
    ],
  }),
  logic: withResourceAuth(['resource:echo:read'], echoLogic),
};
