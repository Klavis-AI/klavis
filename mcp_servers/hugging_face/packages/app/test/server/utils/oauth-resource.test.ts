import { describe, it, expect } from 'vitest';
import type { Request } from 'express';
import { buildOAuthResourceHeader } from '../../../src/server/utils/oauth-resource.js';
import { OAUTH_RESOURCE_BASE_URL } from '../../../src/shared/constants.js';

const createRequest = (options: {
	originalUrl?: string;
	url?: string;
	query?: Request['query'];
}): Request => {
	const { originalUrl, url, query } = options;

	return {
		originalUrl,
		url,
		query: query ?? {},
	} as unknown as Request;
};

describe('buildOAuthResourceHeader', () => {
	it('returns base OAuth resource when there is no query string', () => {
		const req = createRequest({ originalUrl: '/mcp' });

		const header = buildOAuthResourceHeader(req);

		expect(header).toBe(`Bearer resource_metadata="${OAUTH_RESOURCE_BASE_URL}"`);
	});

	it('appends raw query string from originalUrl', () => {
		const req = createRequest({ originalUrl: '/mcp?login&mix=foo' });

		const header = buildOAuthResourceHeader(req);

		expect(header).toBe(
			`Bearer resource_metadata="${OAUTH_RESOURCE_BASE_URL}?login&mix=foo"`,
		);
	});

	it('reconstructs query string from req.query when originalUrl is missing', () => {
		const req = createRequest({
			url: '/mcp',
			query: { login: '', mix: 'foo' } as Request['query'],
		});

		const header = buildOAuthResourceHeader(req);

		expect(header).toBe(
			`Bearer resource_metadata="${OAUTH_RESOURCE_BASE_URL}?login=&mix=foo"`,
		);
	});

	it('preserves duplicate query parameters', () => {
		const req = createRequest({
			originalUrl: '/mcp?mix=foo&mix=bar',
			query: { mix: ['foo', 'bar'] } as unknown as Request['query'],
		});

		const header = buildOAuthResourceHeader(req);

		expect(header).toBe(
			`Bearer resource_metadata="${OAUTH_RESOURCE_BASE_URL}?mix=foo&mix=bar"`,
		);
	});
});
