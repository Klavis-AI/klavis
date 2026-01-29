/**
 * Gradio endpoint discovery with two-level caching and parallel fetching
 *
 * This module provides optimized discovery of Gradio spaces by:
 * 1. Caching space metadata with ETag support (reduces duplicate API calls)
 * 2. Caching schemas (reduces schema refetches)
 * 3. Parallel fetching with configurable concurrency
 * 4. Timeouts and graceful error handling
 */

import type { Tool } from '@modelcontextprotocol/sdk/types.js';
import { logger } from './logger.js';
import { gradioMetrics } from './gradio-metrics.js';
import {
	spaceMetadataCache,
	schemaCache,
	CACHE_CONFIG,
	type CachedSpaceMetadata,
	type CachedSchema,
	logCacheStats,
} from './gradio-cache.js';
import { parseSchemaResponse } from '../gradio-endpoint-connector.js';

/**
 * Complete Gradio space information (metadata + schema)
 */
export interface GradioSpaceInfo {
	// Identity
	name: string;              // e.g., "evalstate/flux1_schnell"
	subdomain: string;         // e.g., "evalstate-flux1-schnell"
	_id: string;               // e.g., "gradio_evalstate-flux1-schnell"
	emoji: string;             // e.g., "🏎️💨"

	// Metadata
	private: boolean;          // For auth header forwarding
	sdk: string;               // e.g., "gradio"

	// Schema
	tools: Tool[];             // Tool definitions with inputSchema

	// Optional runtime info
	runtime?: {
		stage?: string;        // "RUNNING", "SLEEPING", etc.
		hardware?: string;
	};

	// Cache status
	cached: boolean;           // Was this served from cache?
}

/**
 * Options for getGradioSpaces()
 */
export interface GetGradioSpacesOptions {
	skipSchemas?: boolean;     // Just get metadata, skip schema fetch
	includeRuntime?: boolean;  // Fetch runtime status from spaceInfo
	timeout?: number;          // Override default timeouts
}

/**
 * Result of fetching a single space's metadata
 */
type SpaceMetadataResult = {
	success: true;
	metadata: CachedSpaceMetadata;
	cached: boolean;
} | {
	success: false;
	spaceName: string;
	error: Error;
}

/**
 * Result of fetching a single space's schema
 */
type SchemaResult = {
	success: true;
	spaceName: string;
	schema: CachedSchema;
	cached: boolean;
} | {
	success: false;
	spaceName: string;
	error: Error;
}

/**
 * Fetches space metadata with cache and ETag support
 */
async function fetchSpaceMetadata(
	spaceName: string,
	hfToken?: string,
	options?: { includeRuntime?: boolean; timeout?: number }
): Promise<SpaceMetadataResult> {
	const timeout = options?.timeout || CACHE_CONFIG.SPACE_INFO_TIMEOUT;

	try {
		// Check cache first
		const cached = spaceMetadataCache.get(spaceName);
		if (cached) {
			logger.trace({ spaceName }, 'Using cached space metadata');
			return { success: true, metadata: cached, cached: true };
		}

		// Check if we have stale cache entry with ETag for revalidation
		const stale = spaceMetadataCache.getForRevalidation(spaceName);
		const etag = stale?.etag;

		logger.debug({ spaceName, hasEtag: !!etag }, 'Fetching space metadata from HuggingFace API');

		// Create abort controller for timeout
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), timeout);

		try {
			// Prepare additional fields
			const additionalFields = ['subdomain', 'private', 'sdk'];
			if (options?.includeRuntime) {
				additionalFields.push('runtime');
			}

			// Fetch space info with optional ETag header
			// Note: @huggingface/hub doesn't directly support custom headers for ETag,
			// so we'll use fetch directly for better control
			const url = `https://huggingface.co/api/spaces/${spaceName}`;
			const headers: Record<string, string> = {};

			if (hfToken) {
				headers['Authorization'] = `Bearer ${hfToken}`;
			}

			if (etag) {
				headers['If-None-Match'] = etag;
			}

			const response = await fetch(url, {
				headers,
				signal: controller.signal,
			});

			clearTimeout(timeoutId);

			// Handle 304 Not Modified
			if (response.status === 304 && stale) {
				logger.debug({ spaceName }, 'Space metadata not modified (304), using cached data');
				spaceMetadataCache.updateTimestamp(spaceName);
				return { success: true, metadata: stale, cached: true };
			}

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			// Parse response
			const info = await response.json() as {
				_id?: string;
				id: string;
				subdomain?: string;
				private?: boolean;
				sdk?: string;
				runtime?: { stage?: string; hardware?: string };
			};

			// Extract new ETag
			const newEtag = response.headers.get('etag') || undefined;

			// Validate required fields
			if (!info.subdomain) {
				throw new Error('Space does not have a subdomain');
			}

			// Create metadata object
			const metadata: CachedSpaceMetadata = {
				_id: info._id || `gradio_${info.subdomain}`,
				name: spaceName,
				subdomain: info.subdomain,
				emoji: '🔧', // Default emoji, can be overridden
				private: info.private || false,
				sdk: info.sdk || 'gradio',
				runtime: info.runtime,
				etag: newEtag,
				fetchedAt: Date.now(),
			};

			// Only cache public spaces - private spaces should always be fetched fresh
			if (!metadata.private) {
				spaceMetadataCache.set(spaceName, metadata);
				logger.debug({ spaceName, subdomain: metadata.subdomain, hasEtag: !!newEtag }, 'Space metadata fetched and cached');
			} else {
				logger.debug({ spaceName, subdomain: metadata.subdomain }, 'Private space metadata fetched (not cached)');
			}

			return { success: true, metadata, cached: false };
		} finally {
			clearTimeout(timeoutId);
		}
	} catch (error) {
		logger.warn({
			spaceName,
			error: error instanceof Error ? error.message : String(error),
		}, 'Failed to fetch space metadata');

		return {
			success: false,
			spaceName,
			error: error instanceof Error ? error : new Error(String(error)),
		};
	}
}

/**
 * Fetches space metadata in parallel batches with cache support
 */
async function fetchSpaceMetadataWithCache(
	spaceNames: string[],
	hfToken?: string,
	options?: { includeRuntime?: boolean; timeout?: number; concurrency?: number }
): Promise<Map<string, CachedSpaceMetadata>> {
	const concurrency = options?.concurrency || CACHE_CONFIG.DISCOVERY_CONCURRENCY;
	const results = new Map<string, CachedSpaceMetadata>();

	// Process in batches
	const batches: string[][] = [];
	for (let i = 0; i < spaceNames.length; i += concurrency) {
		batches.push(spaceNames.slice(i, i + concurrency));
	}

	logger.debug({
		totalSpaces: spaceNames.length,
		batchCount: batches.length,
		batchSize: concurrency,
	}, 'Fetching space metadata in parallel batches');

	for (const batch of batches) {
		const batchPromises = batch.map(spaceName =>
			fetchSpaceMetadata(spaceName, hfToken, options)
		);

		const batchResults = await Promise.all(batchPromises);

		for (const result of batchResults) {
			if (result.success) {
				results.set(result.metadata.name, result.metadata);
			}
		}
	}

	logger.debug({
		requested: spaceNames.length,
		successful: results.size,
		failed: spaceNames.length - results.size,
	}, 'Space metadata fetch complete');

	return results;
}

/**
 * Fetches schema from a single Gradio endpoint with cache support
 */
async function fetchSchema(
	metadata: CachedSpaceMetadata,
	hfToken?: string,
	options?: { timeout?: number }
): Promise<SchemaResult> {
	const spaceName = metadata.name;
	const timeout = options?.timeout || CACHE_CONFIG.SCHEMA_TIMEOUT;

	try {
		// Check cache first
		const cached = schemaCache.get(spaceName);
		if (cached) {
			logger.trace({ spaceName }, 'Using cached schema');
			return { success: true, spaceName, schema: cached, cached: true };
		}

		logger.debug({ spaceName, subdomain: metadata.subdomain }, 'Fetching schema from Gradio endpoint');

		const schemaUrl = `https://${metadata.subdomain}.hf.space/gradio_api/mcp/schema`;

		// Prepare headers
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
		};

		if (metadata.private && hfToken) {
			headers['X-HF-Authorization'] = `Bearer ${hfToken}`;
		}

		// Create abort controller for timeout
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), timeout);

		try {
			const response = await fetch(schemaUrl, {
				method: 'GET',
				headers,
				signal: controller.signal,
			});

			clearTimeout(timeoutId);

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const schemaResponse = await response.json() as unknown;

			// Parse the schema response using existing parser
			const endpointId = `gradio_${metadata.subdomain}`;
			const parsed = parseSchemaResponse(schemaResponse, endpointId, metadata.subdomain);

			// Convert to Tool format
			const tools: Tool[] = parsed
				.filter((parsedTool) => !parsedTool.name.toLowerCase().includes('<lambda'))
				.map((parsedTool) => {
					const inputSchema = parsedTool.inputSchema as {
						properties?: Record<string, object>;
						required?: string[];
						description?: string;
					};
					return {
						name: parsedTool.name,
						description: parsedTool.description || `${parsedTool.name} tool`,
						inputSchema: {
							type: 'object',
							properties: inputSchema.properties || {},
							required: inputSchema.required || [],
							description: inputSchema.description,
						},
					};
				});

			// Create schema object
			const schema: CachedSchema = {
				tools,
				fetchedAt: Date.now(),
			};

			// Only cache schemas for public spaces - private space schemas should always be fetched fresh
			if (!metadata.private) {
				schemaCache.set(spaceName, schema);
				logger.debug({ spaceName, toolCount: tools.length }, 'Schema fetched and cached');
			} else {
				logger.debug({ spaceName, toolCount: tools.length }, 'Private space schema fetched (not cached)');
			}

			return { success: true, spaceName, schema, cached: false };
		} finally {
			clearTimeout(timeoutId);
		}
	} catch (error) {
		const isFirstError = gradioMetrics.schemaFetchError(spaceName);
		const logFn = isFirstError ? 'warn' : 'trace';
		logger[logFn](
			{
				spaceName,
				subdomain: metadata.subdomain,
				error: error instanceof Error ? error.message : String(error),
			},
			'Failed to fetch schema'
		);

		return {
			success: false,
			spaceName,
			error: error instanceof Error ? error : new Error(String(error)),
		};
	}
}

/**
 * Fetches schemas in parallel with cache support
 */
async function fetchSchemasWithCache(
	metadataList: CachedSpaceMetadata[],
	hfToken?: string,
	options?: { timeout?: number }
): Promise<Map<string, CachedSchema>> {
	const results = new Map<string, CachedSchema>();

	if (metadataList.length === 0) {
		return results;
	}

	logger.debug({ count: metadataList.length }, 'Fetching schemas in parallel');

	// Fetch all schemas in parallel (no batching needed as Gradio endpoints can handle it)
	const schemaPromises = metadataList.map(metadata =>
		fetchSchema(metadata, hfToken, options)
	);

	const schemaResults = await Promise.all(schemaPromises);

	for (const result of schemaResults) {
		if (result.success) {
			results.set(result.spaceName, result.schema);
		}
	}

	logger.debug({
		requested: metadataList.length,
		successful: results.size,
		failed: metadataList.length - results.size,
	}, 'Schema fetch complete');

	return results;
}

/**
 * Combines metadata and schemas into complete GradioSpaceInfo objects
 */
function combineMetadataAndSchemas(
	metadataMap: Map<string, CachedSpaceMetadata>,
	schemaMap: Map<string, CachedSchema>,
	skipSchemas: boolean
): GradioSpaceInfo[] {
	const results: GradioSpaceInfo[] = [];

	for (const [spaceName, metadata] of metadataMap) {
		const schema = schemaMap.get(spaceName);

		// If schemas are required and not available, skip this space
		if (!skipSchemas && !schema) {
			logger.debug({ spaceName }, 'Skipping space without schema');
			continue;
		}

		const spaceInfo: GradioSpaceInfo = {
			_id: metadata._id,
			name: metadata.name,
			subdomain: metadata.subdomain,
			emoji: metadata.emoji,
			private: metadata.private,
			sdk: metadata.sdk,
			tools: schema?.tools || [],
			runtime: metadata.runtime,
			cached: false, // Will be set correctly by tracking cache hits
		};

		results.push(spaceInfo);
	}

	return results;
}

/**
 * Main API: Get complete Gradio space information with caching
 *
 * This is the primary entry point for discovering Gradio spaces.
 * It handles:
 * - Cache lookups and validation
 * - Parallel fetching with timeouts
 * - ETag revalidation
 * - Graceful error handling
 *
 * @param spaceNames - Array of space names (e.g., ["evalstate/flux1_schnell"])
 * @param hfToken - Optional HuggingFace token for authentication
 * @param options - Optional configuration
 * @returns Array of GradioSpaceInfo objects with complete metadata and schemas
 *
 * @example
 * ```typescript
 * const spaces = await getGradioSpaces(
 *   ['evalstate/flux1_schnell', 'microsoft/Phi-3'],
 *   hfToken
 * );
 * // Returns complete info, handles caching/parallelization/errors internally
 * ```
 */
export async function getGradioSpaces(
	spaceNames: string[],
	hfToken?: string,
	options?: GetGradioSpacesOptions
): Promise<GradioSpaceInfo[]> {
	if (spaceNames.length === 0) {
		return [];
	}

	const startTime = Date.now();

	logger.debug({
		count: spaceNames.length,
		spaces: spaceNames,
		skipSchemas: options?.skipSchemas,
		includeRuntime: options?.includeRuntime,
	}, 'Starting Gradio space discovery');

	// Step 1: Fetch/validate space metadata (parallel, with cache + ETag)
	const metadataMap = await fetchSpaceMetadataWithCache(spaceNames, hfToken, {
		includeRuntime: options?.includeRuntime,
		timeout: options?.timeout,
		concurrency: CACHE_CONFIG.DISCOVERY_CONCURRENCY,
	});

	// Step 2: Filter valid Gradio spaces
	const gradioMetadata = Array.from(metadataMap.values()).filter(
		m => m.sdk === 'gradio' && m.subdomain
	);

	logger.debug({
		total: metadataMap.size,
		gradio: gradioMetadata.length,
		filtered: metadataMap.size - gradioMetadata.length,
	}, 'Filtered Gradio spaces');

	// Step 3: Get schemas (parallel, with cache) - skip if requested
	let schemaMap = new Map<string, CachedSchema>();
	if (!options?.skipSchemas && gradioMetadata.length > 0) {
		schemaMap = await fetchSchemasWithCache(gradioMetadata, hfToken, {
			timeout: options?.timeout,
		});
	}

	// Step 4: Combine metadata + schema into complete objects
	const results = combineMetadataAndSchemas(metadataMap, schemaMap, !!options?.skipSchemas);

	const duration = Date.now() - startTime;

	logger.info({
		requested: spaceNames.length,
		successful: results.length,
		failed: spaceNames.length - results.length,
		durationMs: duration,
		skipSchemas: options?.skipSchemas,
	}, 'Gradio space discovery complete');

	// Log cache statistics
	logCacheStats();

	return results;
}

/**
 * Convenience wrapper for getting a single Gradio space
 *
 * @param spaceName - Space name (e.g., "evalstate/flux1_schnell")
 * @param hfToken - Optional HuggingFace token
 * @param options - Optional configuration
 * @returns Single GradioSpaceInfo or null if not found
 *
 * @example
 * ```typescript
 * const space = await getGradioSpace('evalstate/flux1_schnell', hfToken);
 * if (space?.runtime?.stage === 'RUNNING') {
 *   // Space is running
 * }
 * ```
 */
export async function getGradioSpace(
	spaceName: string,
	hfToken?: string,
	options?: GetGradioSpacesOptions
): Promise<GradioSpaceInfo | null> {
	const spaces = await getGradioSpaces([spaceName], hfToken, options);
	return spaces[0] || null;
}
