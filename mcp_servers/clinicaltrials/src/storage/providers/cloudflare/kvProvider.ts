/**
 * @fileoverview Implements the IStorageProvider interface for Cloudflare KV.
 * @module src/storage/providers/cloudflare/kvProvider
 */
import type { KVNamespace } from '@cloudflare/workers-types';

import type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from '@/storage/core/IStorageProvider.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { ErrorHandler, logger, type RequestContext } from '@/utils/index.js';

const DEFAULT_LIST_LIMIT = 1000;

export class KvProvider implements IStorageProvider {
  private readonly kv: KVNamespace;

  constructor(kv: KVNamespace) {
    if (!kv) {
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'KvProvider requires a valid KVNamespace instance.',
      );
    }
    this.kv = kv;
  }

  private getKvKey(tenantId: string, key: string): string {
    return `${tenantId}:${key}`;
  }

  async get<T>(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<T | null> {
    const kvKey = this.getKvKey(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[KvProvider] Getting key: ${kvKey}`, context);
        try {
          const result = await this.kv.get<T>(kvKey, 'json');
          return result; // null indicates not found
        } catch (error) {
          throw new McpError(
            JsonRpcErrorCode.SerializationError,
            `[KvProvider] Failed to parse JSON for key: ${kvKey}`,
            { ...context, error },
          );
        }
      },
      {
        operation: 'KvProvider.get',
        context,
        input: { tenantId, key },
      },
    );
  }

  async set(
    tenantId: string,
    key: string,
    value: unknown,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    const kvKey = this.getKvKey(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[KvProvider] Setting key: ${kvKey}`, {
          ...context,
          options,
        });
        const valueToStore = JSON.stringify(value);

        const putOptions: import('@cloudflare/workers-types').KVNamespacePutOptions =
          {};
        // Fix: Check for undefined instead of truthy to handle ttl=0 correctly
        if (options?.ttl !== undefined) {
          putOptions.expirationTtl = options.ttl;
        }

        await this.kv.put(kvKey, valueToStore, putOptions);
        logger.debug(`[KvProvider] Successfully set key: ${kvKey}`, context);
      },
      {
        operation: 'KvProvider.set',
        context,
        input: { tenantId, key },
      },
    );
  }

  async delete(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<boolean> {
    const kvKey = this.getKvKey(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[KvProvider] Deleting key: ${kvKey}`, context);

        const value = await this.kv.get(kvKey);
        if (value === null) {
          logger.debug(
            `[KvProvider] Key to delete not found: ${kvKey}`,
            context,
          );
          return false;
        }

        await this.kv.delete(kvKey);
        logger.debug(
          `[KvProvider] Successfully deleted key: ${kvKey}`,
          context,
        );
        return true;
      },
      {
        operation: 'KvProvider.delete',
        context,
        input: { tenantId, key },
      },
    );
  }

  async list(
    tenantId: string,
    prefix: string,
    context: RequestContext,
    options?: ListOptions,
  ): Promise<ListResult> {
    const kvPrefix = this.getKvKey(tenantId, prefix);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[KvProvider] Listing keys with prefix: ${kvPrefix}`, {
          ...context,
          options,
        });

        const limit = options?.limit ?? DEFAULT_LIST_LIMIT;
        const listOptions: import('@cloudflare/workers-types').KVNamespaceListOptions =
          {
            prefix: kvPrefix,
            limit,
          };
        if (options?.cursor) {
          listOptions.cursor = options.cursor;
        }
        const listed = await this.kv.list(listOptions);

        const tenantPrefix = `${tenantId}:`;
        const keys = listed.keys.map((keyInfo) =>
          keyInfo.name.startsWith(tenantPrefix)
            ? keyInfo.name.substring(tenantPrefix.length)
            : keyInfo.name,
        );

        const nextCursor =
          'cursor' in listed && !listed.list_complete
            ? listed.cursor
            : undefined;

        logger.debug(
          `[KvProvider] Found ${keys.length} keys with prefix: ${kvPrefix}`,
          context,
        );

        return {
          keys,
          nextCursor,
        };
      },
      {
        operation: 'KvProvider.list',
        context,
        input: { tenantId, prefix, options },
      },
    );
  }

  async getMany<T>(
    tenantId: string,
    keys: string[],
    context: RequestContext,
  ): Promise<Map<string, T>> {
    return ErrorHandler.tryCatch(
      async () => {
        if (keys.length === 0) {
          return new Map<string, T>();
        }

        const results = new Map<string, T>();
        for (const key of keys) {
          const value = await this.get<T>(tenantId, key, context);
          if (value !== null) {
            results.set(key, value);
          }
        }
        return results;
      },
      {
        operation: 'KvProvider.getMany',
        context,
        input: { tenantId, keyCount: keys.length },
      },
    );
  }

  async setMany(
    tenantId: string,
    entries: Map<string, unknown>,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    return ErrorHandler.tryCatch(
      async () => {
        if (entries.size === 0) {
          return;
        }

        const promises = Array.from(entries.entries()).map(([key, value]) =>
          this.set(tenantId, key, value, context, options),
        );
        await Promise.all(promises);
      },
      {
        operation: 'KvProvider.setMany',
        context,
        input: { tenantId, entryCount: entries.size },
      },
    );
  }

  async deleteMany(
    tenantId: string,
    keys: string[],
    context: RequestContext,
  ): Promise<number> {
    return ErrorHandler.tryCatch(
      async () => {
        if (keys.length === 0) {
          return 0;
        }

        const promises = keys.map((key) => this.delete(tenantId, key, context));
        const results = await Promise.all(promises);
        return results.filter((deleted) => deleted).length;
      },
      {
        operation: 'KvProvider.deleteMany',
        context,
        input: { tenantId, keyCount: keys.length },
      },
    );
  }

  async clear(tenantId: string, context: RequestContext): Promise<number> {
    return ErrorHandler.tryCatch(
      async () => {
        const kvPrefix = `${tenantId}:`;
        let deletedCount = 0;
        let cursor: string | undefined;
        let listComplete = false;

        while (!listComplete) {
          const listOpts: import('@cloudflare/workers-types').KVNamespaceListOptions =
            {
              prefix: kvPrefix,
              limit: 1000,
            };
          if (cursor) {
            listOpts.cursor = cursor;
          }
          const listed = await this.kv.list(listOpts);

          const deletePromises = listed.keys.map((keyInfo) =>
            this.kv.delete(keyInfo.name),
          );
          await Promise.all(deletePromises);
          deletedCount += listed.keys.length;

          listComplete = listed.list_complete;
          cursor = 'cursor' in listed ? listed.cursor : undefined;
        }

        logger.info(
          `[KvProvider] Cleared ${deletedCount} keys for tenant: ${tenantId}`,
          context,
        );
        return deletedCount;
      },
      {
        operation: 'KvProvider.clear',
        context,
        input: { tenantId },
      },
    );
  }
}
