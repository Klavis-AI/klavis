/**
 * @fileoverview A Supabase-based storage provider.
 * Persists data to a specified table in a Supabase PostgreSQL database.
 * Assumes a table with columns: `key` (text), `value` (jsonb), and `expires_at` (timestamptz).
 * @module src/storage/providers/supabase/supabaseProvider
 */
import { inject, injectable } from 'tsyringe';

import { SupabaseClient } from '@supabase/supabase-js';

import { SupabaseAdminClient } from '@/container/tokens.js';
import type {
  IStorageProvider,
  StorageOptions,
  ListOptions,
  ListResult,
} from '@/storage/core/IStorageProvider.js';
import type {
  Json,
  Database,
} from '@/storage/providers/supabase/supabase.types.js';
import {
  encodeCursor,
  decodeCursor,
} from '@/storage/core/storageValidation.js';
import { ErrorHandler, type RequestContext, logger } from '@/utils/index.js';

const TABLE_NAME = 'kv_store';
const DEFAULT_LIST_LIMIT = 1000;

@injectable()
export class SupabaseProvider implements IStorageProvider {
  constructor(
    @inject(SupabaseAdminClient)
    private readonly client: SupabaseClient<Database>,
  ) {}

  private getClient() {
    return this.client;
  }

  async get<T>(
    tenantId: string,
    key: string,
    context: RequestContext,
  ): Promise<T | null> {
    return ErrorHandler.tryCatch(
      async () => {
        const { data, error } = await this.getClient()
          .from(TABLE_NAME)
          .select('value, expires_at')
          .eq('tenant_id', tenantId)
          .eq('key', key)
          .single();

        if (error) {
          if (error.code === 'PGRST116') {
            // "Not found" error code from PostgREST
            return null;
          }
          throw error;
        }

        if (
          data.expires_at &&
          new Date(data.expires_at).getTime() < Date.now()
        ) {
          await this.delete(tenantId, key, context);
          logger.debug(
            `[SupabaseProvider] Key expired and removed: ${key} for tenant: ${tenantId}`,
            context,
          );
          return null;
        }

        return data.value as T;
      },
      {
        operation: 'SupabaseProvider.get',
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
    return ErrorHandler.tryCatch(
      async () => {
        // Fix: Check for undefined instead of truthy to handle ttl=0 correctly
        const expires_at =
          options?.ttl !== undefined
            ? new Date(Date.now() + options.ttl * 1000).toISOString()
            : null;

        const { error } = await this.getClient()
          .from(TABLE_NAME)
          .upsert({
            tenant_id: tenantId,
            key,
            value: value as Json,
            expires_at,
          });

        if (error) throw error;
      },
      {
        operation: 'SupabaseProvider.set',
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
    return ErrorHandler.tryCatch(
      async () => {
        const { error, count } = await this.getClient()
          .from(TABLE_NAME)
          .delete({ count: 'exact' })
          .eq('tenant_id', tenantId)
          .eq('key', key);

        if (error) throw error;
        return (count ?? 0) > 0;
      },
      {
        operation: 'SupabaseProvider.delete',
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
    return ErrorHandler.tryCatch(
      async () => {
        const now = new Date().toISOString();
        const limit = options?.limit ?? DEFAULT_LIST_LIMIT;

        let query = this.getClient()
          .from(TABLE_NAME)
          .select('key')
          .eq('tenant_id', tenantId)
          .like('key', `${prefix}%`)
          .or(`expires_at.is.null,expires_at.gt.${now}`)
          .order('key', { ascending: true })
          .limit(limit + 1); // Fetch one extra to determine if there are more results

        // Apply cursor-based pagination with opaque cursors
        if (options?.cursor) {
          // Decode and validate cursor
          const lastKey = decodeCursor(options.cursor, tenantId, context);
          query = query.gt('key', lastKey);
        }

        const { data, error } = await query;

        if (error) throw error;

        const keys = data?.map((item) => item.key) ?? [];
        const hasMore = keys.length > limit;
        const resultKeys = hasMore ? keys.slice(0, limit) : keys;
        const nextCursor =
          hasMore && resultKeys.length > 0
            ? encodeCursor(resultKeys[resultKeys.length - 1]!, tenantId)
            : undefined;

        return {
          keys: resultKeys,
          nextCursor,
        };
      },
      {
        operation: 'SupabaseProvider.list',
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
    return ErrorHandler.tryCatch<Map<string, T>>(
      async () => {
        if (keys.length === 0) {
          return new Map<string, T>();
        }

        const { data, error } = await this.getClient()
          .from(TABLE_NAME)
          .select('key, value, expires_at')
          .eq('tenant_id', tenantId)
          .in('key', keys);

        if (error) throw error;

        const results = new Map<string, T>();
        for (const row of data ?? []) {
          if (
            !row.expires_at ||
            new Date(row.expires_at).getTime() >= Date.now()
          ) {
            results.set(row.key, row.value as T);
          } else {
            // Clean up expired entries
            await this.delete(tenantId, row.key, context);
          }
        }

        return results;
      },
      {
        operation: 'SupabaseProvider.getMany',
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

        // Fix: Check for undefined instead of truthy to handle ttl=0 correctly
        const expires_at =
          options?.ttl !== undefined
            ? new Date(Date.now() + options.ttl * 1000).toISOString()
            : null;

        const rows = Array.from(entries.entries()).map(([key, value]) => ({
          tenant_id: tenantId,
          key,
          value: value as Json,
          expires_at,
        }));

        const { error } = await this.getClient().from(TABLE_NAME).upsert(rows);

        if (error) throw error;
      },
      {
        operation: 'SupabaseProvider.setMany',
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

        const { error, count } = await this.getClient()
          .from(TABLE_NAME)
          .delete({ count: 'exact' })
          .eq('tenant_id', tenantId)
          .in('key', keys);

        if (error) throw error;
        return count ?? 0;
      },
      {
        operation: 'SupabaseProvider.deleteMany',
        context,
        input: { tenantId, keyCount: keys.length },
      },
    );
  }

  async clear(tenantId: string, context: RequestContext): Promise<number> {
    return ErrorHandler.tryCatch(
      async () => {
        const { error, count } = await this.getClient()
          .from(TABLE_NAME)
          .delete({ count: 'exact' })
          .eq('tenant_id', tenantId);

        if (error) throw error;
        logger.info(
          `[SupabaseProvider] Cleared ${count ?? 0} keys for tenant: ${tenantId}`,
          context,
        );
        return count ?? 0;
      },
      {
        operation: 'SupabaseProvider.clear',
        context,
        input: { tenantId },
      },
    );
  }
}
