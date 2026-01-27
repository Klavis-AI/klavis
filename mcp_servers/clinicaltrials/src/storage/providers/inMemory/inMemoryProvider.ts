/**
 * @fileoverview An in-memory storage provider implementation.
 * Ideal for development, testing, or scenarios where persistence is not required.
 * Supports TTL (Time-To-Live) for entries.
 * @module src/storage/providers/inMemory/inMemoryProvider
 */
import type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from '@/storage/core/IStorageProvider.js';
import {
  encodeCursor,
  decodeCursor,
} from '@/storage/core/storageValidation.js';
import { type RequestContext, logger } from '@/utils/index.js';

const DEFAULT_LIST_LIMIT = 1000;

interface InMemoryStoreEntry {
  value: unknown;
  expiresAt?: number;
}

export class InMemoryProvider implements IStorageProvider {
  private readonly store = new Map<string, Map<string, InMemoryStoreEntry>>();

  private getTenantStore(tenantId: string): Map<string, InMemoryStoreEntry> {
    let tenantStore = this.store.get(tenantId);
    if (!tenantStore) {
      tenantStore = new Map<string, InMemoryStoreEntry>();
      this.store.set(tenantId, tenantStore);
    }
    return tenantStore;
  }

  get<T>(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<T | null> {
    logger.debug(
      `[InMemoryProvider] Getting key: ${key} for tenant: ${tenantId}`,
      context,
    );
    const tenantStore = this.getTenantStore(tenantId);
    const entry = tenantStore.get(key);

    if (!entry) {
      return Promise.resolve(null);
    }

    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      tenantStore.delete(key);
      logger.debug(
        `[InMemoryProvider] Key expired and removed: ${key} for tenant: ${tenantId}`,
        context,
      );
      return Promise.resolve(null);
    }

    return Promise.resolve(entry.value as T);
  }

  set(
    tenantId: string,
    key: string,
    value: unknown,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    logger.debug(
      `[InMemoryProvider] Setting key: ${key} for tenant: ${tenantId}`,
      context,
    );
    const tenantStore = this.getTenantStore(tenantId);
    // Fix: Check for undefined instead of truthy to handle ttl=0 correctly
    const expiresAt =
      options?.ttl !== undefined ? Date.now() + options.ttl * 1000 : undefined;
    tenantStore.set(key, {
      value,
      ...(expiresAt !== undefined && { expiresAt }),
    });
    return Promise.resolve();
  }

  delete(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<boolean> {
    logger.debug(
      `[InMemoryProvider] Deleting key: ${key} for tenant: ${tenantId}`,
      context,
    );
    const tenantStore = this.getTenantStore(tenantId);
    return Promise.resolve(tenantStore.delete(key));
  }

  list(
    tenantId: string,
    prefix: string,
    context: RequestContext,
    options?: ListOptions,
  ): Promise<ListResult> {
    logger.debug(
      `[InMemoryProvider] Listing keys with prefix: ${prefix} for tenant: ${tenantId}`,
      { ...context, options },
    );
    const tenantStore = this.getTenantStore(tenantId);
    const now = Date.now();
    const allKeys: string[] = [];

    // Collect all matching non-expired keys
    for (const [key, entry] of tenantStore.entries()) {
      if (key.startsWith(prefix)) {
        if (entry.expiresAt && now > entry.expiresAt) {
          tenantStore.delete(key); // Lazy cleanup
        } else {
          allKeys.push(key);
        }
      }
    }

    // Sort for consistent pagination
    allKeys.sort();

    // Apply pagination with opaque cursors
    const limit = options?.limit ?? DEFAULT_LIST_LIMIT;
    let startIndex = 0;

    if (options?.cursor) {
      // Decode and validate cursor
      const lastKey = decodeCursor(options.cursor, tenantId, context);
      const cursorIndex = allKeys.indexOf(lastKey);
      if (cursorIndex !== -1) {
        startIndex = cursorIndex + 1;
      }
    }

    const paginatedKeys = allKeys.slice(startIndex, startIndex + limit);
    const nextCursor =
      startIndex + limit < allKeys.length && paginatedKeys.length > 0
        ? encodeCursor(paginatedKeys[paginatedKeys.length - 1]!, tenantId)
        : undefined;

    return Promise.resolve({
      keys: paginatedKeys,
      nextCursor,
    });
  }

  async getMany<T>(
    tenantId: string,
    keys: string[],
    context: RequestContext,
  ): Promise<Map<string, T>> {
    if (keys.length === 0) {
      return new Map<string, T>();
    }

    logger.debug(
      `[InMemoryProvider] Getting ${keys.length} keys for tenant: ${tenantId}`,
      context,
    );

    // Parallel fetch for better performance
    const promises = keys.map((key) => this.get<T>(tenantId, key, context));
    const values = await Promise.all(promises);

    const results = new Map<string, T>();
    keys.forEach((key, i) => {
      const value = values[i];
      if (value !== null) {
        results.set(key, value as T);
      }
    });

    logger.debug(
      `[InMemoryProvider] Retrieved ${results.size}/${keys.length} keys for tenant: ${tenantId}`,
      context,
    );
    return results;
  }

  async setMany(
    tenantId: string,
    entries: Map<string, unknown>,
    context: RequestContext,
    options?: StorageOptions,
  ): Promise<void> {
    if (entries.size === 0) {
      return;
    }

    logger.debug(
      `[InMemoryProvider] Setting ${entries.size} keys for tenant: ${tenantId}`,
      context,
    );

    // Parallel set for better performance
    const promises = Array.from(entries.entries()).map(([key, value]) =>
      this.set(tenantId, key, value, context, options),
    );
    await Promise.all(promises);

    logger.debug(
      `[InMemoryProvider] Successfully set ${entries.size} keys for tenant: ${tenantId}`,
      context,
    );
  }

  async deleteMany(
    tenantId: string,
    keys: string[],
    context: RequestContext,
  ): Promise<number> {
    if (keys.length === 0) {
      return 0;
    }

    logger.debug(
      `[InMemoryProvider] Deleting ${keys.length} keys for tenant: ${tenantId}`,
      context,
    );

    // Parallel delete for better performance
    const promises = keys.map((key) => this.delete(tenantId, key, context));
    const results = await Promise.all(promises);
    const deletedCount = results.filter((deleted) => deleted).length;

    logger.debug(
      `[InMemoryProvider] Deleted ${deletedCount}/${keys.length} keys for tenant: ${tenantId}`,
      context,
    );
    return deletedCount;
  }

  clear(tenantId: string, context: RequestContext): Promise<number> {
    logger.debug(
      `[InMemoryProvider] Clearing all keys for tenant: ${tenantId}`,
      context,
    );
    const tenantStore = this.getTenantStore(tenantId);
    const count = tenantStore.size;
    tenantStore.clear();
    logger.info(
      `[InMemoryProvider] Cleared ${count} keys for tenant: ${tenantId}`,
      context,
    );
    return Promise.resolve(count);
  }
}
