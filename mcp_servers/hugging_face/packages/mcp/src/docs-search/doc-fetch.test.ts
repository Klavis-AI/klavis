import { describe, it, expect, vi, afterEach } from 'vitest';
import { DocFetchTool, normalizeDocUrl } from './doc-fetch.js';

const createMockResponse = ({
	content,
	contentType = 'text/html',
	status = 200,
	statusText = 'OK',
}: {
	content: string;
	contentType?: string;
	status?: number;
	statusText?: string;
}) =>
	new Response(content, {
		status,
		statusText,
		headers: { 'content-type': contentType },
	});

const stubFetch = (factory: () => Response) => {
	const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(factory()));
	vi.stubGlobal('fetch', fetchMock);
	return fetchMock;
};

describe('DocFetchTool', () => {
    const tool = new DocFetchTool();

	afterEach(() => {
		vi.clearAllMocks();
		vi.unstubAllGlobals();
	});

	describe('URL validation', () => {
		it('should accept valid HF and Gradio docs URLs', () => {
			const validUrls = [
				'https://huggingface.co/docs/dataset-viewer/index',
				'https://huggingface.co/docs/huggingface_hub/guides/upload#faster-uploads',
				'https://huggingface.co/docs/transformers/model_doc/bert',
				'https://huggingface.co/docs/diffusers/api/pipelines/stable_diffusion',
				'https://huggingface.co/docs/timm/models',
				'https://huggingface.co/docs/transformers',
				'https://gradio.app',
				'https://www.gradio.app/guides',
			];

			for (const url of validUrls) {
				expect(() => tool.validateUrl(url)).not.toThrow();
			}
		});

		it('should throw error for URLs not starting with correct prefix', () => {
			const invalidUrls = [
				'https://example.com/docs/something',
				'https://github.com/huggingface/transformers',
				'http://huggingface.co/docs/transformers',
				'huggingface.co/docs/transformers',
				'https://huggingface.co/models/bert-base-uncased',
			];

			for (const url of invalidUrls) {
				expect(() => tool.validateUrl(url)).toThrow('That was not a valid documentation URL');
			}
		});
	});

	describe('document chunking', () => {
		it('uses markdown content from host when available', async () => {
			const markdown = '# Heading\nBody content';
			const fetchMock = stubFetch(() =>
				createMockResponse({
					content: markdown,
					contentType: 'text/markdown',
				}),
			);

			const result = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test' });
			expect(fetchMock).toHaveBeenCalledWith('https://huggingface.co/docs/test', {
				headers: { accept: 'text/markdown' },
			});
			expect(result).toBe(markdown);
		});

		it('should return small documents without chunking', async () => {
			
			// Mock fetch to return HTML that converts to short markdown
			stubFetch(() =>
				createMockResponse({
					content: '<h1>Short Document</h1><p>This is a short document.</p>',
				}),
			);

			const result = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test' });
			
			expect(result).toContain('# Short Document');
			expect(result).toContain('This is a short document');
			expect(result).not.toContain('DOCUMENT TRUNCATED');
		});

		it('should chunk large documents and show truncation message', async () => {
			// Mock fetch to return HTML that converts to long markdown
			const longHtml = '<h1>Long Document</h1>' + '<p>This is a very long sentence that will be repeated many times to create a document that exceeds the 7500 token limit for testing chunking functionality.</p>'.repeat(200);
			
			stubFetch(() =>
				createMockResponse({
					content: longHtml,
				}),
			);

			const result = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test' });
			
			expect(result).toContain('# Long Document');
			expect(result).toContain('DOCUMENT TRUNCATED');
			expect(result).toContain('CALL hf_doc_fetch WITH AN OFFSET OF');
		});

		it('normalizes gradio.app to www.gradio.app (pure function)', () => {
			const cases: Array<{ in: string; out: string }> = [
				{ in: 'https://gradio.app/guides/x', out: 'https://www.gradio.app/guides/x' },
				{ in: 'https://www.gradio.app/guides/x', out: 'https://www.gradio.app/guides/x' },
				{ in: 'https://huggingface.co/docs/transformers', out: 'https://huggingface.co/docs/transformers' },
				{ in: '/docs/diffusers/index', out: 'https://huggingface.co/docs/diffusers/index' },
				{ in: './docs/diffusers/index', out: 'https://huggingface.co/docs/diffusers/index' },
				{ in: 'not a url', out: 'not a url' },
			];
			for (const c of cases) {
				expect(normalizeDocUrl(c.in)).toBe(c.out);
			}
		});

		it('normalizes relative doc paths to the huggingface docs host', async () => {
			const fetchMock = stubFetch(() =>
				createMockResponse({
					content: '<h1>Title</h1><p>Body</p>',
				}),
			);

			const result = await tool.fetch({ doc_url: '/docs/test' });
			expect(fetchMock).toHaveBeenCalledWith('https://huggingface.co/docs/test', {
				headers: { accept: 'text/markdown' },
			});
			expect(result).toContain('# Title');
		});

		it('normalizes ./docs paths to the huggingface docs host', async () => {
			const fetchMock = stubFetch(() =>
				createMockResponse({
					content: '<h1>Another Title</h1><p>Body</p>',
				}),
			);

			await tool.fetch({ doc_url: './docs/another' });
			expect(fetchMock).toHaveBeenCalledWith('https://huggingface.co/docs/another', {
				headers: { accept: 'text/markdown' },
			});
		});

		it('should return subsequent chunks with offset', async () => {
			// Mock fetch to return the same long HTML
			const longHtml = '<h1>Long Document</h1>' + '<p>This is a very long sentence that will be repeated many times to create a document that exceeds the 7500 token limit for testing chunking functionality.</p>'.repeat(200);
			
			stubFetch(() =>
				createMockResponse({
					content: longHtml,
				}),
			);

			// Get first chunk
			const firstChunk = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test' });
			
			// Extract offset from truncation message
			const offsetMatch = firstChunk.match(/OFFSET OF (\d+)/);
			expect(offsetMatch).toBeTruthy();
			const offset = parseInt(offsetMatch?.[1] || '0', 10);

			// Get second chunk
			const secondChunk = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test', offset });
			
			expect(secondChunk).not.toEqual(firstChunk);
			expect(secondChunk.length).toBeGreaterThan(0);
		});

		it('should handle offset beyond document length', async () => {
			stubFetch(() =>
				createMockResponse({
					content: '<h1>Short Document</h1><p>This is short.</p>',
				}),
			);

			const result = await tool.fetch({ doc_url: 'https://huggingface.co/docs/test', offset: 10000 });
			
			expect(result).toContain('Error: Offset 10000 is beyond');
		});
	});
});
