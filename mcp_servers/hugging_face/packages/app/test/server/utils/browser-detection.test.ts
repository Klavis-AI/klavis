import { describe, it, expect } from 'vitest';
import { isBrowser } from '../../../src/server/utils/browser-detection.js';

describe('isBrowser', () => {
	it('returns false when accept header is missing', () => {
		expect(isBrowser({})).toBe(false);
		expect(isBrowser({ 'user-agent': 'Mozilla/5.0' })).toBe(false);
	});

	it('returns false when accept contains text/event-stream', () => {
		// this is VSCode
		expect(isBrowser({ accept: 'text/event-stream' })).toBe(false);
		expect(isBrowser({ accept: 'text/event-stream, text/html' })).toBe(false);
	});

	it('returns false when accept contains application/json', () => {
		expect(isBrowser({ accept: 'application/json' })).toBe(false);
		expect(isBrowser({ accept: 'application/json, text/plain' })).toBe(false);
	});

	it('returns true when accept contains */*', () => {
		expect(isBrowser({ accept: '*/*' })).toBe(true);
		expect(isBrowser({ accept: 'text/html, */*' })).toBe(true);
	});

	it('returns false for other accept headers', () => {
		expect(isBrowser({ accept: 'text/html' })).toBe(false);
		expect(isBrowser({ accept: 'text/plain' })).toBe(false);
		expect(isBrowser({ accept: 'image/png' })).toBe(false);
	});

	it('handles array accept headers', () => {
		expect(isBrowser({ accept: ['text/event-stream'] })).toBe(false);
		expect(isBrowser({ accept: ['*/*', 'text/html'] })).toBe(true);
		expect(isBrowser({ accept: ['application/json', 'text/plain'] })).toBe(false);
	});

	it('real browser examples', () => {
		// Chrome
		expect(
			isBrowser({
				accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
			})
		).toBe(true);

		// Safari
		expect(
			isBrowser({
				accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			})
		).toBe(true);

		// hugging face javascript mcp-client
		expect(
			isBrowser({
				accept: 'text/event-stream',
			})
		).toBe(false);

		// hugging face javascript mcp-client
		expect(
			isBrowser({
				accept: 'text/event-stream',
			})
		).toBe(false);
	});

	it('API client examples', () => {
		// SSE client
		expect(isBrowser({ accept: 'text/event-stream' })).toBe(false);

		// JSON API client
		expect(isBrowser({ accept: 'application/json' })).toBe(false);

		// Mixed API client
		expect(isBrowser({ accept: 'application/json, text/event-stream' })).toBe(false);
	});
});
