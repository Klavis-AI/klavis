/**
 * @fileoverview Implements the IStorageProvider interface for Cloudflare R2.
 *
 * Performance note: TTL filtering in list operations is not applied at the R2 API level.
 * Expired entries are only removed on get operations. For large datasets, consider
 * implementing periodic cleanup jobs to remove expired entries.
 *
 * @module src/storage/providers/cloudflare/r2Provider
 */
import type { R2Bucket } from '@cloudflare/workers-types';

import type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from '@/storage/core/IStorageProvider.js';
import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import { ErrorHandler, logger, type RequestContext } from '@/utils/index.js';

type R2Envelope = {
  __mcp: { v: 1; expiresAt?: number };
  value: unknown;
};

const R2_ENVELOPE_VERSION = 1;
const DEFAULT_LIST_LIMIT = 1000;

export class R2Provider implements IStorageProvider {
  private readonly bucket: R2Bucket;

  constructor(bucket: R2Bucket) {
    if (!bucket) {
      throw new McpError(
        JsonRpcErrorCode.ConfigurationError,
        'R2Provider requires a valid R2Bucket instance.',
      );
    }
    this.bucket = bucket;
  }

  private getR2Key(tenantId: string, key: string): string {
    return `${tenantId}:${key}`;
  }

  private buildEnvelope(value: unknown, options?: StorageOptions): R2Envelope {
    // Fix: Check for undefined instead of truthy to handle ttl=0 correctly
    const expiresAt =
      options?.ttl !== undefined ? Date.now() + options.ttl * 1000 : undefined;
    return {
      __mcp: {
        v: R2_ENVELOPE_VERSION,
        ...(expiresAt !== undefined ? { expiresAt } : {}),
      },
      value,
    };
  }

  private parseAndValidate<T>(
    raw: string,
    tenantId: string,
    key: string,
    context: RequestContext,
  ): T | null {
    try {
      const parsed: unknown = JSON.parse(raw);
      if (parsed && typeof parsed === 'object' && '__mcp' in parsed) {
        const env = parsed as R2Envelope;
        const expiresAt = env.__mcp?.expiresAt;
        if (expiresAt && Date.now() > expiresAt) {
          // expired
          return null;
        }
        return env.value as T;
      }
      // legacy: direct value
      return parsed as T;
    } catch (error) {
      throw new McpError(
        JsonRpcErrorCode.SerializationError,
        `[R2Provider] Failed to parse JSON for key: ${this.getR2Key(
          tenantId,
          key,
        )}`,
        { ...context, error },
      );
    }
  }

  async get<T>(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<T | null> {
    const r2Key = this.getR2Key(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[R2Provider] Getting key: ${r2Key}`, context);
        const object = await this.bucket.get(r2Key);
        if (object === null) {
          return null;
        }
        const text = await object.text();
        const value = this.parseAndValidate<T>(text, tenantId, key, context);
        if (value === null) {
          // best-effort cleanup if expired
          await this.bucket.delete(r2Key).catch(() => {});
          logger.debug(
            `[R2Provider] Key expired and removed: ${r2Key}`,
            context,
          );
        }
        return value;
      },
      {
        operation: 'R2Provider.get',
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
    const r2Key = this.getR2Key(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[R2Provider] Setting key: ${r2Key}`, {
          ...context,
          options,
        });
        const envelope = this.buildEnvelope(value, options);
        const body = JSON.stringify(envelope);
        await this.bucket.put(r2Key, body);
        logger.debug(`[R2Provider] Successfully set key: ${r2Key}`, context);
      },
      {
        operation: 'R2Provider.set',
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
    const r2Key = this.getR2Key(tenantId, key);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[R2Provider] Deleting key: ${r2Key}`, context);
        const head = await this.bucket.head(r2Key);
        if (head === null) {
          logger.debug(
            `[R2Provider] Key to delete not found: ${r2Key}`,
            context,
          );
          return false;
        }
        await this.bucket.delete(r2Key);
        logger.debug(
          `[R2Provider] Successfully deleted key: ${r2Key}`,
          context,
        );
        return true;
      },
      {
        operation: 'R2Provider.delete',
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
    const r2Prefix = this.getR2Key(tenantId, prefix);
    return ErrorHandler.tryCatch(
      async () => {
        logger.debug(`[R2Provider] Listing keys with prefix: ${r2Prefix}`, {
          ...context,
          options,
        });

        const limit = options?.limit ?? DEFAULT_LIST_LIMIT;
        const listOptions: import('@cloudflare/workers-types').R2ListOptions = {
          prefix: r2Prefix,
          limit: limit + 1, // Fetch one extra to determine if there are more
        };
        if (options?.cursor) {
          listOptions.cursor = options.cursor;
        }
        const listed = await this.bucket.list(listOptions);

        const tenantPrefix = `${tenantId}:`;
        const keys = listed.objects.map((obj) =>
          obj.key.startsWith(tenantPrefix)
            ? obj.key.substring(tenantPrefix.length)
            : obj.key,
        );

        const hasMore = keys.length > limit;
        const resultKeys = hasMore ? keys.slice(0, limit) : keys;
        const nextCursor =
          'cursor' in listed && listed.truncated ? listed.cursor : undefined;

        logger.debug(
          `[R2Provider] Found ${resultKeys.length} keys with prefix: ${r2Prefix}`,
          context,
        );

        return {
          keys: resultKeys,
          nextCursor,
        };
      },
      {
        operation: 'R2Provider.list',
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
        operation: 'R2Provider.getMany',
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
        operation: 'R2Provider.setMany',
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
        operation: 'R2Provider.deleteMany',
        context,
        input: { tenantId, keyCount: keys.length },
      },
    );
  }

  async clear(tenantId: string, context: RequestContext): Promise<number> {
    return ErrorHandler.tryCatch(
      async () => {
        const r2Prefix = `${tenantId}:`;
        let deletedCount = 0;
        let cursor: string | undefined;
        let hasMore = true;

        while (hasMore) {
          const listOpts: import('@cloudflare/workers-types').R2ListOptions = {
            prefix: r2Prefix,
            limit: 1000,
          };
          if (cursor) {
            listOpts.cursor = cursor;
          }
          const listed = await this.bucket.list(listOpts);

          const deletePromises = listed.objects.map((obj) =>
            this.bucket.delete(obj.key),
          );
          await Promise.all(deletePromises);
          deletedCount += listed.objects.length;

          hasMore = listed.truncated;
          cursor = 'cursor' in listed ? listed.cursor : undefined;
        }

        logger.info(
          `[R2Provider] Cleared ${deletedCount} keys for tenant: ${tenantId}`,
          context,
        );
        return deletedCount;
      },
      {
        operation: 'R2Provider.clear',
        context,
        input: { tenantId },
      },
    );
  }
}
