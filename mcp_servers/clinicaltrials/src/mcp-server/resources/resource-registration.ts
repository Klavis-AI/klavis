/**
 * @fileoverview Encapsulates the registration of all resource definitions for the application's
 * dependency injection (DI) container and provides a registry service to apply them to an
 * McpServer instance.
 * @module src/mcp-server/resources/resource-registration
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { type DependencyContainer, injectable, injectAll } from 'tsyringe';
import { ZodObject, type ZodRawShape } from 'zod';

import { ResourceDefinitions } from '@/container/index.js';
import { allResourceDefinitions } from '@/mcp-server/resources/definitions/index.js';
import type { ResourceDefinition } from '@/mcp-server/resources/utils/resourceDefinition.js';
import { registerResource } from '@/mcp-server/resources/utils/resourceHandlerFactory.js';
import { logger, requestContextService } from '@/utils/index.js';

@injectable()
export class ResourceRegistry {
  constructor(
    @injectAll(ResourceDefinitions, { isOptional: true })
    private resourceDefs: ResourceDefinition<
      ZodObject<ZodRawShape>,
      ZodObject<ZodRawShape> | undefined
    >[],
  ) {}

  /**
   * Registers all resolved resource definitions with the provided McpServer instance.
   * @param {McpServer} server - The server instance to register resources with.
   */
  public async registerAll(server: McpServer): Promise<void> {
    const context = requestContextService.createRequestContext({
      operation: 'ResourceRegistry.registerAll',
    });
    logger.info(
      `Registering ${this.resourceDefs.length} resource(s)...`,
      context,
    );
    for (const resourceDef of this.resourceDefs) {
      await registerResource(server, resourceDef);
    }
  }
}

/**
 * Registers all resource definitions with the provided dependency container.
 * This function uses multi-injection to register each resource under the `ResourceDefinitions` token.
 *
 * @param {DependencyContainer} container - The tsyringe container instance to register resources with.
 */
export const registerResources = (container: DependencyContainer): void => {
  for (const resource of allResourceDefinitions) {
    container.register(ResourceDefinitions, { useValue: resource });
  }
};
