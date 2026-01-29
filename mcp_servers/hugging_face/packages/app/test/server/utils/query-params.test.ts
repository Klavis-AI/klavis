import { describe, it, expect } from 'vitest';
import { extractQueryParamsToHeaders } from '../../../src/server/utils/query-params.js';
import type { Request } from 'express';

describe('extractQueryParamsToHeaders', () => {
	it('should extract bouquet query parameter to header', () => {
		const req = {
			query: { bouquet: 'search' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBe('search');
		expect(headers['x-mcp-mix']).toBeUndefined();
	});

	it('should extract mix query parameter to header', () => {
		const req = {
			query: { mix: 'all' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-mix']).toBe('all');
		expect(headers['x-mcp-bouquet']).toBeUndefined();
	});

	it('should join multiple mix query parameters', () => {
		const req = {
			query: { mix: ['hf_api', 'jobs'] },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-mix']).toBe('hf_api,jobs');
	});

	it('should extract both bouquet and mix query parameters', () => {
		const req = {
			query: { bouquet: 'search', mix: 'hf_api' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBe('search');
		expect(headers['x-mcp-mix']).toBe('hf_api');
	});

	it('should handle empty query parameters', () => {
		const req = {
			query: {},
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBeUndefined();
		expect(headers['x-mcp-mix']).toBeUndefined();
	});

	it('should handle undefined query parameters', () => {
		const req = {
			query: { bouquet: undefined, mix: undefined },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBeUndefined();
		expect(headers['x-mcp-mix']).toBeUndefined();
	});

	it('should not overwrite existing headers if query params are undefined', () => {
		const req = {
			query: { bouquet: undefined, mix: undefined },
		} as unknown as Request;

		const headers: Record<string, string> = {
			'x-mcp-bouquet': 'existing',
			'x-mcp-mix': 'existing',
		};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBe('existing');
		expect(headers['x-mcp-mix']).toBe('existing');
	});

	it('should preserve other headers', () => {
		const req = {
			query: { bouquet: 'search' },
		} as unknown as Request;

		const headers: Record<string, string> = {
			authorization: 'Bearer token123',
			'content-type': 'application/json',
		};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBe('search');
		expect(headers['authorization']).toBe('Bearer token123');
		expect(headers['content-type']).toBe('application/json');
	});

	it('should extract gradio query parameter to header', () => {
		const req = {
			query: { gradio: 'evalstate/flux1_schnell,foo/bar' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-gradio']).toBe('evalstate/flux1_schnell,foo/bar');
		expect(headers['x-mcp-bouquet']).toBeUndefined();
		expect(headers['x-mcp-mix']).toBeUndefined();
	});

	it('should extract gradio, bouquet, and mix together', () => {
		const req = {
			query: { 
				bouquet: 'docs',
				mix: 'search',
				gradio: 'evalstate/flux1_schnell'
			},
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-bouquet']).toBe('docs');
		expect(headers['x-mcp-mix']).toBe('search');
		expect(headers['x-mcp-gradio']).toBe('evalstate/flux1_schnell');
	});

	it('should set no-image header when no_image_content=true', () => {
		const req = {
			query: { no_image_content: 'true' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-no-image-content']).toBe('true');
	});

	it('should set no-image header when no_image_content is empty', () => {
		const req = {
			query: { no_image_content: '' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-no-image-content']).toBe('true');
	});

	it('should ignore no_image_content when false', () => {
		const req = {
			query: { no_image_content: 'false' },
		} as unknown as Request;

		const headers: Record<string, string> = {};
		extractQueryParamsToHeaders(req, headers);

		expect(headers['x-mcp-no-image-content']).toBeUndefined();
	});
});
