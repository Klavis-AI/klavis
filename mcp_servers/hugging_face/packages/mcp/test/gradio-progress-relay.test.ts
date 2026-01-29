import { describe, it, expect, vi, beforeAll } from 'vitest';

// Stub out the Streamable HTTP transport to simulate progress + response without network.
vi.mock('@modelcontextprotocol/sdk/client/streamableHttp.js', () => {
	class FakeStreamableHTTPClientTransport {
		onmessage?: (msg: unknown) => void;
		onclose?: () => void;
		onerror?: (err: unknown) => void;
		sessionId = 'fake';

		constructor(_url: URL, _options: unknown) {}

		async start() {
			/* no-op */
		}

		async close() {
			this.onclose?.();
		}

		async send(message: any) {
			// Simulate two progress notifications followed by a result.
			const progressToken = message?.id ?? message?.params?._meta?.progressToken ?? 0;
			queueMicrotask(() => {
				this.onmessage?.({
					jsonrpc: '2.0',
					method: 'notifications/progress',
					params: { progressToken, progress: 1, total: 10, message: 'first' },
				});
				this.onmessage?.({
					jsonrpc: '2.0',
					method: 'notifications/progress',
					params: { progressToken, progress: 2, total: 10, message: 'second' },
				});
				this.onmessage?.({
					jsonrpc: '2.0',
					id: message.id,
					result: { isError: false, content: [{ type: 'text', text: 'ok' }] },
				});
			});
		}
	}

	return { StreamableHTTPClientTransport: FakeStreamableHTTPClientTransport };
});

let callGradioToolWithHeaders: typeof import('../src/space/utils/gradio-caller.js').callGradioToolWithHeaders;

beforeAll(async () => {
	({ callGradioToolWithHeaders } = await import('../src/space/utils/gradio-caller.js'));
});

describe('callGradioToolWithHeaders progress relay', () => {
	it('swallows progress send failures after disconnect', async () => {
		let attempts = 0;
		const extra = {
			_meta: { progressToken: 42 },
			sendNotification: vi.fn().mockImplementation(async () => {
				attempts += 1;
				throw new Error('Not connected');
			}),
			signal: new AbortController().signal,
		};

		const { result } = await callGradioToolWithHeaders(
			'http://fake-mcp.local/gradio_api/mcp/',
			'tools/call',
			{},
			undefined,
			extra as any
		);

		// Allow pending microtasks (progress relay) to flush
		await new Promise((resolve) => setTimeout(resolve, 0));

		expect(result.isError).toBe(false);
		// Progress relay should never crash and should not spam after failure.
		expect(attempts).toBeLessThanOrEqual(1);
		expect(extra.sendNotification.mock.calls.length).toBeLessThanOrEqual(1);
	});
});
