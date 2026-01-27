/**
 * @fileoverview Pagination utilities for MCP list operations.
 * Implements cursor-based pagination per MCP specification 2025-06-18.
 *
 * MCP Pagination Model:
 * - Opaque cursor-based approach (not numbered pages)
 * - Cursor is an opaque string token representing a position in the result set
 * - Page size is determined by server (clients MUST NOT assume fixed page size)
 * - Invalid cursors should result in error code -32602 (Invalid params)
 *
 * @see {@link https://modelcontextprotocol.io/specification/2025-06-18/utils/pagination | MCP Pagination Spec}
 * @module src/utils/pagination
 */

import { JsonRpcErrorCode, McpError } from '@/types-global/errors.js';
import type { RequestContext } from '@/utils/index.js';
import { logger } from '@/utils/index.js';

/**
 * Generic pagination state that can be encoded into a cursor.
 * Implementations can extend this with additional fields as needed.
 */
export interface PaginationState {
  /** Current page offset or starting position */
  offset: number;
  /** Maximum number of items per page */
  limit: number;
  /** Optional additional state (implementation-specific) */
  [key: string]: unknown;
}

/**
 * Result of a paginated operation.
 */
export interface PaginatedResult<T> {
  /** Array of items for the current page */
  items: T[];
  /** Opaque cursor for the next page, undefined if no more results */
  nextCursor?: string;
  /** Total count if available (optional, some backends may not support this efficiently) */
  totalCount?: number;
}

/**
 * Encodes pagination state into an opaque cursor string.
 * Uses base64-encoded JSON for transparency during development.
 * Can be optimized to use more compact/opaque formats in production if needed.
 *
 * @param state - The pagination state to encode
 * @returns Base64-encoded cursor string
 * @throws {McpError} If encoding fails
 */
export function encodeCursor(state: PaginationState): string {
  try {
    const jsonString = JSON.stringify(state);
    const base64 = Buffer.from(jsonString, 'utf-8').toString('base64url');
    return base64;
  } catch (error) {
    throw new McpError(
      JsonRpcErrorCode.InternalError,
      'Failed to encode pagination cursor',
      { error: error instanceof Error ? error.message : String(error) },
    );
  }
}

/**
 * Decodes an opaque cursor string back into pagination state.
 * Validates the cursor format and throws McpError for invalid cursors per spec.
 *
 * @param cursor - The opaque cursor string to decode
 * @param context - Request context for logging
 * @returns Decoded pagination state
 * @throws {McpError} If cursor is invalid (code -32602)
 */
export function decodeCursor(
  cursor: string,
  context: RequestContext,
): PaginationState {
  try {
    const jsonString = Buffer.from(cursor, 'base64url').toString('utf-8');
    const state = JSON.parse(jsonString) as PaginationState;

    // Validate required fields
    if (
      typeof state.offset !== 'number' ||
      typeof state.limit !== 'number' ||
      state.offset < 0 ||
      state.limit <= 0
    ) {
      throw new Error('Invalid pagination state structure');
    }

    return state;
  } catch (error) {
    logger.warning('Failed to decode pagination cursor', {
      ...context,
      cursor,
      error: error instanceof Error ? error.message : String(error),
    });
    throw new McpError(
      JsonRpcErrorCode.InvalidParams,
      'Invalid pagination cursor. The cursor may be expired, corrupted, or from a different request.',
      { cursor },
    );
  }
}

/**
 * Extracts the cursor parameter from MCP request metadata.
 * Handles both params.cursor and _meta.cursor locations per spec.
 *
 * @param params - Request params object
 * @returns Cursor string if present, undefined otherwise
 */
export function extractCursor(params?: {
  cursor?: string;
  _meta?: { cursor?: string };
}): string | undefined {
  return params?.cursor ?? params?._meta?.cursor;
}

/**
 * Helper to paginate an in-memory array.
 * Useful for simple list operations that don't require database pagination.
 *
 * @param items - Full array of items to paginate
 * @param cursorStr - Optional cursor from client request
 * @param defaultPageSize - Default page size if cursor doesn't specify
 * @param maxPageSize - Maximum allowed page size
 * @param context - Request context for logging
 * @returns Paginated result with nextCursor if more items exist
 */
export function paginateArray<T>(
  items: T[],
  cursorStr: string | undefined,
  defaultPageSize: number,
  maxPageSize: number,
  context: RequestContext,
): PaginatedResult<T> {
  let offset = 0;
  let limit = defaultPageSize;

  // Decode cursor if provided
  if (cursorStr) {
    const state = decodeCursor(cursorStr, context);
    offset = state.offset;
    limit = Math.min(state.limit, maxPageSize); // Enforce max page size
  }

  // Validate bounds
  if (offset >= items.length) {
    return {
      items: [],
      totalCount: items.length,
    };
  }

  // Extract page
  const pageItems = items.slice(offset, offset + limit);
  const hasMore = offset + limit < items.length;

  // Build result, conditionally adding nextCursor only if it exists
  const result: PaginatedResult<T> = {
    items: pageItems,
    totalCount: items.length,
  };

  // Only add nextCursor if more results exist
  if (hasMore) {
    result.nextCursor = encodeCursor({ offset: offset + limit, limit });
  }

  return result;
}

/**
 * Default pagination configuration values.
 * These can be overridden via environment variables in config module.
 */
export const DEFAULT_PAGINATION_CONFIG = {
  /** Default number of items per page */
  DEFAULT_PAGE_SIZE: 50,
  /** Maximum allowed items per page */
  MAX_PAGE_SIZE: 1000,
  /** Minimum allowed items per page */
  MIN_PAGE_SIZE: 1,
} as const;
