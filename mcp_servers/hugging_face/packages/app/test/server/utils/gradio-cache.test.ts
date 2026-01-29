import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
	spaceMetadataCache,
	schemaCache,
	getCacheStats,
	clearAllCaches,
	CACHE_CONFIG,
	type CachedSpaceMetadata,
	type CachedSchema,
} from '../../../src/server/utils/gradio-cache.js';

describe('SpaceMetadataCache', () => {
	beforeEach(() => {
		clearAllCaches();
	});

	describe('get()', () => {
		it('should return null for non-existent entries', () => {
			const result = spaceMetadataCache.get('nonexistent/space');
			expect(result).toBeNull();
		});

		it('should return cached entry within TTL', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			const result = spaceMetadataCache.get('test/space');

			expect(result).toEqual(metadata);
		});

		it('should return null for expired entries', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now() - CACHE_CONFIG.SPACE_METADATA_TTL - 1000, // Expired
			};

			spaceMetadataCache.set('test/space', metadata);
			const result = spaceMetadataCache.get('test/space');

			expect(result).toBeNull();
		});

		it('should return entry with ETag', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				etag: 'W/"test-etag"',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			const result = spaceMetadataCache.get('test/space');

			expect(result?.etag).toBe('W/"test-etag"');
		});
	});

	describe('getForRevalidation()', () => {
		it('should return entry even if expired', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				etag: 'W/"test-etag"',
				fetchedAt: Date.now() - CACHE_CONFIG.SPACE_METADATA_TTL - 1000, // Expired
			};

			spaceMetadataCache.set('test/space', metadata);
			const result = spaceMetadataCache.getForRevalidation('test/space');

			expect(result).toEqual(metadata);
		});

		it('should return null for non-existent entries', () => {
			const result = spaceMetadataCache.getForRevalidation('nonexistent/space');
			expect(result).toBeNull();
		});
	});

	describe('set()', () => {
		it('should store metadata', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			const result = spaceMetadataCache.get('test/space');

			expect(result).toEqual(metadata);
		});

		it('should overwrite existing metadata', () => {
			const metadata1: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			const metadata2: CachedSpaceMetadata = {
				...metadata1,
				emoji: '🚀',
				private: true,
			};

			spaceMetadataCache.set('test/space', metadata1);
			spaceMetadataCache.set('test/space', metadata2);

			const result = spaceMetadataCache.get('test/space');
			expect(result?.emoji).toBe('🚀');
			expect(result?.private).toBe(true);
		});
	});

	describe('updateTimestamp()', () => {
		it('should update timestamp of existing entry', () => {
			const oldTimestamp = Date.now() - 60000; // 1 minute ago
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: oldTimestamp,
			};

			spaceMetadataCache.set('test/space', metadata);
			spaceMetadataCache.updateTimestamp('test/space');

			const result = spaceMetadataCache.get('test/space');
			expect(result?.fetchedAt).toBeGreaterThan(oldTimestamp);
		});

		it('should do nothing for non-existent entry', () => {
			// Should not throw
			spaceMetadataCache.updateTimestamp('nonexistent/space');
		});
	});

	describe('clear()', () => {
		it('should remove all entries', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			spaceMetadataCache.clear();

			const result = spaceMetadataCache.get('test/space');
			expect(result).toBeNull();
		});
	});

	describe('getStats()', () => {
		it('should track hits and misses', () => {
			clearAllCaches(); // Reset stats

			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);

			// Hit
			spaceMetadataCache.get('test/space');
			// Miss
			spaceMetadataCache.get('nonexistent/space');
			// Another hit
			spaceMetadataCache.get('test/space');

			const stats = spaceMetadataCache.getStats();
			expect(stats.hits).toBe(2);
			expect(stats.misses).toBe(1);
		});

		it('should track cache size', () => {
			clearAllCaches();

			const metadata1: CachedSpaceMetadata = {
				_id: 'gradio_space1',
				name: 'test/space1',
				subdomain: 'space1',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			const metadata2: CachedSpaceMetadata = {
				_id: 'gradio_space2',
				name: 'test/space2',
				subdomain: 'space2',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space1', metadata1);
			spaceMetadataCache.set('test/space2', metadata2);

			const stats = spaceMetadataCache.getStats();
			expect(stats.size).toBe(2);
		});

		it('should track ETag revalidations', () => {
			clearAllCaches();

			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			spaceMetadataCache.updateTimestamp('test/space');

			const stats = spaceMetadataCache.getStats();
			expect(stats.etagRevalidations).toBe(1);
		});
	});
});

describe('SchemaCache', () => {
	beforeEach(() => {
		clearAllCaches();
	});

	describe('get()', () => {
		it('should return null for non-existent entries', () => {
			const result = schemaCache.get('nonexistent/space');
			expect(result).toBeNull();
		});

		it('should return cached schema within TTL', () => {
			const schema: CachedSchema = {
				tools: [
					{
						name: 'test_tool',
						description: 'Test tool',
						inputSchema: {
							type: 'object',
							properties: {},
						},
					},
				],
				fetchedAt: Date.now(),
			};

			schemaCache.set('test/space', schema);
			const result = schemaCache.get('test/space');

			expect(result).toEqual(schema);
		});

		it('should return null for expired entries', () => {
			const schema: CachedSchema = {
				tools: [
					{
						name: 'test_tool',
						description: 'Test tool',
						inputSchema: {
							type: 'object',
							properties: {},
						},
					},
				],
				fetchedAt: Date.now() - CACHE_CONFIG.SCHEMA_TTL - 1000, // Expired
			};

			schemaCache.set('test/space', schema);
			const result = schemaCache.get('test/space');

			expect(result).toBeNull();
		});
	});

	describe('set()', () => {
		it('should store schema', () => {
			const schema: CachedSchema = {
				tools: [
					{
						name: 'test_tool',
						description: 'Test tool',
						inputSchema: {
							type: 'object',
							properties: {},
						},
					},
				],
				fetchedAt: Date.now(),
			};

			schemaCache.set('test/space', schema);
			const result = schemaCache.get('test/space');

			expect(result).toEqual(schema);
		});

		it('should store multiple tools', () => {
			const schema: CachedSchema = {
				tools: [
					{
						name: 'tool1',
						description: 'Tool 1',
						inputSchema: { type: 'object', properties: {} },
					},
					{
						name: 'tool2',
						description: 'Tool 2',
						inputSchema: { type: 'object', properties: {} },
					},
				],
				fetchedAt: Date.now(),
			};

			schemaCache.set('test/space', schema);
			const result = schemaCache.get('test/space');

			expect(result?.tools).toHaveLength(2);
		});
	});

	describe('clear()', () => {
		it('should remove all entries', () => {
			const schema: CachedSchema = {
				tools: [],
				fetchedAt: Date.now(),
			};

			schemaCache.set('test/space', schema);
			schemaCache.clear();

			const result = schemaCache.get('test/space');
			expect(result).toBeNull();
		});
	});

	describe('getStats()', () => {
		it('should track hits and misses', () => {
			clearAllCaches();

			const schema: CachedSchema = {
				tools: [],
				fetchedAt: Date.now(),
			};

			schemaCache.set('test/space', schema);

			// Hit
			schemaCache.get('test/space');
			// Miss
			schemaCache.get('nonexistent/space');
			// Another hit
			schemaCache.get('test/space');

			const stats = schemaCache.getStats();
			expect(stats.hits).toBe(2);
			expect(stats.misses).toBe(1);
		});
	});
});

describe('Cache utility functions', () => {
	beforeEach(() => {
		clearAllCaches();
	});

	describe('getCacheStats()', () => {
		it('should return combined statistics', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			const schema: CachedSchema = {
				tools: [],
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			schemaCache.set('test/space', schema);

			// Generate some hits
			spaceMetadataCache.get('test/space');
			schemaCache.get('test/space');

			const stats = getCacheStats();
			expect(stats.metadataHits).toBeGreaterThan(0);
			expect(stats.schemaHits).toBeGreaterThan(0);
			expect(stats.metadataCacheSize).toBe(1);
			expect(stats.schemaCacheSize).toBe(1);
		});
	});

	describe('clearAllCaches()', () => {
		it('should clear both caches', () => {
			const metadata: CachedSpaceMetadata = {
				_id: 'gradio_test-space',
				name: 'test/space',
				subdomain: 'test-space',
				emoji: '🔧',
				private: false,
				sdk: 'gradio',
				fetchedAt: Date.now(),
			};

			const schema: CachedSchema = {
				tools: [],
				fetchedAt: Date.now(),
			};

			spaceMetadataCache.set('test/space', metadata);
			schemaCache.set('test/space', schema);

			clearAllCaches();

			expect(spaceMetadataCache.get('test/space')).toBeNull();
			expect(schemaCache.get('test/space')).toBeNull();
		});
	});
});

describe('CACHE_CONFIG', () => {
	it('should have default values', () => {
		expect(CACHE_CONFIG.SPACE_METADATA_TTL).toBeDefined();
		expect(CACHE_CONFIG.SCHEMA_TTL).toBeDefined();
		expect(CACHE_CONFIG.DISCOVERY_CONCURRENCY).toBeDefined();
		expect(CACHE_CONFIG.SPACE_INFO_TIMEOUT).toBeDefined();
		expect(CACHE_CONFIG.SCHEMA_TIMEOUT).toBeDefined();
	});

	it('should have reasonable default values', () => {
		// Default TTL should be 5 minutes (300000 ms) unless overridden
		expect(CACHE_CONFIG.SPACE_METADATA_TTL).toBeGreaterThan(0);
		expect(CACHE_CONFIG.SCHEMA_TTL).toBeGreaterThan(0);

		// Default concurrency should be 10
		expect(CACHE_CONFIG.DISCOVERY_CONCURRENCY).toBeGreaterThan(0);

		// Timeouts should be reasonable
		expect(CACHE_CONFIG.SPACE_INFO_TIMEOUT).toBeGreaterThan(0);
		expect(CACHE_CONFIG.SCHEMA_TIMEOUT).toBeGreaterThan(0);
	});
});
