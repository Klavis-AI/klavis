/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { StatelessHttpTransport } from '../../../src/server/transport/stateless-http-transport.js';
import type { ServerFactory } from '../../../src/server/transport/base-transport.js';
import express from 'express';

describe('StatelessHttpTransport', () => {
	let transport: StatelessHttpTransport;

	beforeEach(() => {
		// Create a minimal instance for testing private methods
		const mockServerFactory = vi.fn() as unknown as ServerFactory;
		const mockApp = express();
		transport = new StatelessHttpTransport(mockServerFactory, mockApp);
	});

	describe('shouldHandle', () => {
		it('should handle tools/list requests', () => {
			const result = (transport as any).shouldHandle({ method: 'tools/list' });
			expect(result).toBe(true);
		});

		it('should handle tools/call requests', () => {
			const result = (transport as any).shouldHandle({ method: 'tools/call' });
			expect(result).toBe(true);
		});

		it('should handle initialize requests', () => {
			const result = (transport as any).shouldHandle({ method: 'initialize' });
			expect(result).toBe(true);
		});

		it('should not handle ping requests', () => {
			const result = (transport as any).shouldHandle({ method: 'ping' });
			expect(result).toBe(false);
		});

		it('should handle prompts/list requests', () => {
			const result = (transport as any).shouldHandle({ method: 'prompts/list' });
			expect(result).toBe(true);
		});

		it('should handle prompts/get requests', () => {
			const result = (transport as any).shouldHandle({ method: 'prompts/get' });
			expect(result).toBe(true);
		});

		it('should NOT handle resources/list requests for non-openai-mcp clients', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/list' });
			expect(result).toBe(false);
		});

		it('should handle resources/list requests for openai-mcp client', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/list' }, 'openai-mcp');
			expect(result).toBe(true);
		});

		it('should NOT handle resources/read requests for non-openai-mcp clients', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/read' });
			expect(result).toBe(false);
		});

		it('should handle resources/read requests for openai-mcp client', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/read' }, 'openai-mcp');
			expect(result).toBe(true);
		});

		it('should NOT handle resources/templates/list requests for non-openai-mcp clients', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/templates/list' });
			expect(result).toBe(false);
		});

		it('should handle resources/templates/list requests for openai-mcp client', () => {
			const result = (transport as any).shouldHandle({ method: 'resources/templates/list' }, 'openai-mcp');
			expect(result).toBe(true);
		});

		it('should handle undefined method gracefully', () => {
			const result = (transport as any).shouldHandle({});
			expect(result).toBe(false);
		});

		it('should handle undefined body gracefully', () => {
			const result = (transport as any).shouldHandle(undefined);
			expect(result).toBe(false);
		});

		it('should handle null body gracefully', () => {
			const result = (transport as any).shouldHandle(null);
			expect(result).toBe(false);
		});
	});
});
