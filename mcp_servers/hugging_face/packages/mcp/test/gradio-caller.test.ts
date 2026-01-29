import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { rewriteReplicaUrlsInResult, extractReplicaId } from '../src/space/utils/gradio-caller.js';
import type { CallToolResult } from '@modelcontextprotocol/sdk/types.js';

const baseResult: CallToolResult = {
	content: [],
	isError: false,
};

describe('extractReplicaId', () => {
	it('extracts the suffix after hyphen', () => {
		expect(extractReplicaId('oyerizs4-dspr4')).toBe('dspr4');
	});

	it('returns null when no hyphen exists', () => {
		expect(extractReplicaId('singlepart')).toBeNull();
	});

	it('returns null for empty input', () => {
		expect(extractReplicaId('')).toBeNull();
		expect(extractReplicaId(undefined)).toBeNull();
	});
});

describe('rewriteReplicaUrlsInResult', () => {
	const matchUrl = 'https://mcp-tools-qwen-image-fast.hf.space/gradio_api';
	const rewrittenUrl = 'https://mcp-tools-qwen-image-fast.hf.space/--replicas/dspr4/gradio_api';

	beforeEach(() => {
		delete process.env.NO_REPLICA_REWRITE;
	});

	afterEach(() => {
		delete process.env.NO_REPLICA_REWRITE;
	});

	it('rewrites URLs in text content when header is present', () => {
		const result: CallToolResult = {
			...baseResult,
			content: [
				{ type: 'text', text: `prefix ${matchUrl} suffix` },
				`plain ${matchUrl}`,
				{ type: 'image', data: 'noop' },
			],
		};

		const rewritten = rewriteReplicaUrlsInResult(result, 'oyerizs4-dspr4');

		expect((rewritten.content[0] as { text: string }).text).toContain(rewrittenUrl);
		expect((rewritten.content[1] as { text: string }).text).toContain(rewrittenUrl);
		// Non-text blocks untouched
		expect(rewritten.content[2]).toEqual(result.content[2]);
	});

	it('does nothing when header is missing', () => {
		const result: CallToolResult = {
			...baseResult,
			content: [{ type: 'text', text: `prefix ${matchUrl} suffix` }],
		};

		const rewritten = rewriteReplicaUrlsInResult(result, undefined);

		expect(rewritten).toEqual(result);
	});

	it('respects NO_REPLICA_REWRITE env', () => {
		process.env.NO_REPLICA_REWRITE = '1';
		const result: CallToolResult = {
			...baseResult,
			content: [{ type: 'text', text: matchUrl }],
		};

		const rewritten = rewriteReplicaUrlsInResult(result, 'oyerizs4-dspr4');

		expect(rewritten).toEqual(result);
	});
});
