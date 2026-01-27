/**
 * @fileoverview Provides a singleton service for interacting with the application's storage layer.
 * This service acts as a proxy to the configured storage provider, ensuring a consistent
 * interface for all storage operations throughout the application. It receives its concrete
 * provider via dependency injection.
 * @module src/storage/core/StorageService
 */
import { injectable, inject } from 'tsyringe';

import { StorageProvider } from '@/container/tokens.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { logger, type RequestContext } from '@/utils/index.js';
import type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from '@/storage/core/IStorageProvider.js';
import {
  validateTenantId,
  validateKey,
  validatePrefix,
  validateStorageOptions,
  validateListOptions,
} from '@/storage/core/storageValidation.js';

/**
 * Validates and returns the tenant ID from the request context.
 *
 * This helper ensures the tenant ID is present in the context and passes
 * validation rules defined in {@link validateTenantId}. All StorageService
 * operations require a valid tenant ID for multi-tenancy isolation.
 *
 * @param context - The request context containing the tenant ID
 * @returns The validated tenant ID (trimmed of whitespace)
 * @throws {McpError} JsonRpcErrorCode.InternalError - If tenant ID is missing (undefined or null)
 * @throws {McpError} JsonRpcErrorCode.InvalidParams - If tenant ID fails validation (from validateTenantId)
 * @internal
 */
function requireTenantId(context: RequestContext): string {
  const tenantId = context.tenantId;

  // Check if tenant ID is missing (undefined or null)
  if (tenantId === undefined || tenantId === null) {
    throw new McpError(
      JsonRpcErrorCode.InternalError,
      'Tenant ID is required for storage operations but was not found in the request context.',
      {
        operation: context.operation || 'StorageService.requireTenantId',
        requestId: context.requestId,
        // Include call stack hint for debugging
        calledFrom: 'StorageService',
      },
    );
  }

  // Delegate validation to shared utility
  validateTenantId(tenantId, context);

  return tenantId.trim();
}

@injectable()
export class StorageService {
  constructor(@inject(StorageProvider) private provider: IStorageProvider) {
    // Note: Cannot use structured logging in constructor as we don't have RequestContext yet
    // This is logged when the service is first instantiated by the DI container
  }

  get<T>(key: string, context: RequestContext): Promise<T | null> {
    const tenantId = requireTenantId(context);
    validateKey(key, context);

    logger.debug('[StorageService] get operation', {
      ...context,
      operation: 'StorageService.get',
      tenantId,
      key,
    });

    return this.provider.get(tenantId, key, context);
  }

  set(
    key: string,
    value: unknown,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    const tenantId = requireTenantId(context);
    validateKey(key, context);
    validateStorageOptions(options, context);

    logger.debug('[StorageService] set operation', {
      ...context,
      operation: 'StorageService.set',
      tenantId,
      key,
      hasTTL: options?.ttl !== undefined,
      ttl: options?.ttl,
    });

    return this.provider.set(tenantId, key, value, context, options);
  }

  delete(key: string, context: RequestContext): Promise<boolean> {
    const tenantId = requireTenantId(context);
    validateKey(key, context);

    logger.debug('[StorageService] delete operation', {
      ...context,
      operation: 'StorageService.delete',
      tenantId,
      key,
    });

    return this.provider.delete(tenantId, key, context);
  }

  list(
    prefix: string,
    context: RequestContext,
    options?: ListOptions,
  ): Promise<ListResult> {
    const tenantId = requireTenantId(context);
    validatePrefix(prefix, context);
    validateListOptions(options, context);

    logger.debug('[StorageService] list operation', {
      ...context,
      operation: 'StorageService.list',
      tenantId,
      prefix,
      limit: options?.limit,
      hasCursor: !!options?.cursor,
    });

    return this.provider.list(tenantId, prefix, context, options);
  }

  getMany<T>(keys: string[], context: RequestContext): Promise<Map<string, T>> {
    const tenantId = requireTenantId(context);
    // Validate all keys
    for (const key of keys) {
      validateKey(key, context);
    }

    logger.debug('[StorageService] getMany operation', {
      ...context,
      operation: 'StorageService.getMany',
      tenantId,
      keyCount: keys.length,
    });

    return this.provider.getMany(tenantId, keys, context);
  }

  setMany(
    entries: Map<string, unknown>,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    const tenantId = requireTenantId(context);
    validateStorageOptions(options, context);
    // Validate all keys
    for (const key of entries.keys()) {
      validateKey(key, context);
    }

    logger.debug('[StorageService] setMany operation', {
      ...context,
      operation: 'StorageService.setMany',
      tenantId,
      entryCount: entries.size,
      hasTTL: options?.ttl !== undefined,
      ttl: options?.ttl,
    });

    return this.provider.setMany(tenantId, entries, context, options);
  }

  deleteMany(keys: string[], context: RequestContext): Promise<number> {
    const tenantId = requireTenantId(context);
    // Validate all keys
    for (const key of keys) {
      validateKey(key, context);
    }

    logger.debug('[StorageService] deleteMany operation', {
      ...context,
      operation: 'StorageService.deleteMany',
      tenantId,
      keyCount: keys.length,
    });

    return this.provider.deleteMany(tenantId, keys, context);
  }

  clear(context: RequestContext): Promise<number> {
    const tenantId = requireTenantId(context);

    logger.info('[StorageService] clear operation', {
      ...context,
      operation: 'StorageService.clear',
      tenantId,
    });

    return this.provider.clear(tenantId, context);
  }
}
