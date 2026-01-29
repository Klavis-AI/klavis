import { z } from 'zod';
import TurndownService from 'turndown';
import { estimateTokens } from '../utilities.js';

export const DOC_FETCH_CONFIG = {
	name: 'hf_doc_fetch',
	description:
		'Fetch a document from the Hugging Face or Gradio documentation library. For large documents, use offset to get subsequent chunks.',
	schema: z.object({
		doc_url: z.string().max(200, 'Query too long').describe('Documentation URL (Hugging Face or Gradio)'),
		offset: z
			.number()
			.min(0)
			.optional()
			.describe('Token offset for large documents (use the offset from truncation message)'),
	}),
	annotations: {
		title: 'Fetch a document from the Hugging Face documentation library',
		destructiveHint: false,
		readOnlyHint: true,
		openWorldHint: true,
	},
} as const;

export type DocFetchParams = z.infer<typeof DOC_FETCH_CONFIG.schema>;

export class DocFetchTool {
	private turndownService: TurndownService;

	constructor() {
		this.turndownService = new TurndownService({
			headingStyle: 'atx',
			codeBlockStyle: 'fenced',
		});
		this.turndownService.remove('head');
		this.turndownService.remove('script');

		// Drop common non-content containers to reduce noise
		this.turndownService.remove((node) => {
			try {
				const tag = ((node as unknown as { nodeName?: string }).nodeName || '').toLowerCase();
				if (['header', 'nav', 'footer', 'aside', 'form', 'button', 'style', 'noscript', 'iframe'].includes(tag)) {
					return true;
				}
			} catch {
				/* ignore */
			}
			return false;
		});
		this.turndownService.remove((node) => {
			// Strip inline SVGs as they are noisy and rarely useful in text docs
			try {
				if (typeof (node as unknown as { nodeName?: string }).nodeName === 'string') {
					const tag = ((node as unknown as { nodeName: string }).nodeName || '').toLowerCase();
					if (tag === 'svg') {
						return true;
					}
				}
			} catch {
				/* ignore */
			}

			if (node.nodeName === 'a' && node.innerHTML.includes('<!-- HTML_TAG_START -->')) {
				return true;
			}
			// Remove <img ... src="...svg"> or data-uri SVGs to avoid markdown noise
			const nodeName = ((node as unknown as { nodeName?: string }).nodeName || '').toLowerCase();
			if (nodeName === 'img') {
				try {
					const src =
						(node as unknown as { getAttribute?: (name: string) => string | null }).getAttribute?.('src') ??
						((node as unknown as { src?: string }).src || '');
					if (
						/\.svg(\?|$)/i.test(src) ||
						/^data:image\/svg\+xml[,;]/i.test(src) ||
						src.toLowerCase().includes('image/svg+xml')
					) {
						return true;
					}
				} catch {
					/* ignore */
				}
			}
			return false;
		});

		// Drop anchor-only heading icons or anchors containing encoded SVG payloads
		this.turndownService.addRule('dropHeadingAnchors', {
			filter: (node) => {
				try {
					const n = node as unknown as {
						nodeName?: string;
						getAttribute?: (k: string) => string | null;
						textContent?: string;
						childNodes?: Array<{ nodeName?: string }>;
					};
					if ((n.nodeName || '').toLowerCase() !== 'a') return false;
					const href = n.getAttribute?.('href') || '';
					if (!href || !href.startsWith('#')) return false;
					const text = (n.textContent || '').trim();
					const children = (n as unknown as { childNodes?: Array<{ nodeName?: string }> }).childNodes || [];
					const onlyIcons =
						children.length > 0 &&
						children.every(
							(c) => (c.nodeName || '').toLowerCase() === 'img' || (c.nodeName || '').toLowerCase() === 'svg'
						);
					const looksLikeEncodedSvg = /data:image\/svg\+xml|%3csvg|svg%2bxml/i.test(text);
					const noAlnumText = text.length <= 3 && !/[a-z0-9]/i.test(text);
					return onlyIcons || looksLikeEncodedSvg || noAlnumText;
				} catch {
					return false;
				}
			},
			replacement: () => '',
		});
	}

	/**
	 * Validate HF docs URL
	 */
	validateUrl(hfUrl: string): void {
		try {
			const url = new URL(hfUrl);
			if (url.protocol !== 'https:') {
				throw new Error('That was not a valid documentation URL');
			}

			const hostname = url.hostname.toLowerCase();
			const isHfDocs =
				(hostname === 'huggingface.co' || hostname === 'www.huggingface.co') && url.pathname.startsWith('/docs/');
			const isGradio = hostname === 'gradio.app' || hostname === 'www.gradio.app';

			if (!isHfDocs && !isGradio) {
				throw new Error('That was not a valid documentation URL');
			}
		} catch {
			throw new Error('That was not a valid documentation URL');
		}
	}

	/**
	 * Fetch content from Hugging Face docs URL and convert HTML to Markdown
	 */
	async fetch(params: DocFetchParams): Promise<string> {
		try {
			const normalizedUrl = normalizeDocUrl(params.doc_url);
			this.validateUrl(normalizedUrl);

			const response = await fetch(normalizedUrl, { headers: { accept: 'text/markdown' } });
			if (!response.ok) {
				throw new Error(`Failed to fetch document: ${response.status} ${response.statusText}`);
			}
			let content = await response.text();
			const contentType = response.headers.get('content-type') || '';
			const isPlainOrMarkdown = contentType.includes('text/plain') || contentType.includes('text/markdown');
			if (!isPlainOrMarkdown) {
				// attempt conversion to markdown
				content = this.turndownService.turndown(content);

				// Post-process: strip any leftover SVG images that slipped past DOM filters
				//  - Markdown images pointing to data:image/svg+xml or *.svg
				//  - Empty links left behind after image removal: [](...)
				content = content
					.replace(/!\[[^\]]*\]\(\s*(?:data:image\/svg\+xml[^)]*|[^)]*\.svg(?:\?[^)]*)?)\s*\)/gi, '')
					.replace(/\[\s*\]\(\s*[^)]*\s*\)/g, '');

				// Remove anchors whose link text still contains encoded SVG payloads (edge cases)
				content = content.replace(/\[[^\]]*(?:data:image\/svg\+xml|%3csvg|svg%2bxml)[^\]]*\]\([^)]*\)/gi, '');
			}

			// Apply chunking logic
			return this.applyChunking(content, params.offset || 0);
		} catch (error) {
			throw new Error(`Failed to fetch document: ${error instanceof Error ? error.message : 'Unknown error'}`);
		}
	}

	/**
	 * Apply chunking logic to markdown content
	 */
	private applyChunking(markdownContent: string, offset: number): string {
		const totalTokens = estimateTokens(markdownContent);
		const maxTokensPerChunk = 7500;

		// Calculate character positions based on tokens
		const totalChars = markdownContent.length;
		const charsPerToken = totalChars / totalTokens;
		const startChar = Math.floor(offset * charsPerToken);

		// If offset is beyond document, return error message
		if (startChar >= totalChars) {
			return `Error: Offset ${offset} is beyond the document length (${totalTokens} tokens total).`;
		}

		// If document is small enough and no offset, return as-is
		if (totalTokens <= maxTokensPerChunk && offset === 0) {
			return markdownContent;
		}

		const maxCharsPerChunk = Math.floor(maxTokensPerChunk * charsPerToken);
		const endChar = Math.min(startChar + maxCharsPerChunk, totalChars);
		const chunk = markdownContent.slice(startChar, endChar);

		// Calculate next offset
		const nextOffset = offset + estimateTokens(chunk);
		const hasMore = nextOffset < totalTokens;

		let result = chunk;

		// Add truncation message if there's more content
		if (hasMore) {
			result += `\n\n=== DOCUMENT TRUNCATED. CALL ${DOC_FETCH_CONFIG.name} WITH AN OFFSET OF ${nextOffset} FOR THE NEXT CHUNK ===`;
		}

		return result;
	}
}

/**
 * Normalize incoming documentation URLs for known domains
 * - Convert gradio.app → www.gradio.app so pages resolve correctly
 */
export function normalizeDocUrl(input: string): string {
	try {
		const trimmed = input.trim();
		if (trimmed.startsWith('/docs')) {
			return `https://huggingface.co${trimmed}`;
		}
		if (trimmed.startsWith('./docs')) {
			return `https://huggingface.co/${trimmed.slice(2)}`;
		}

		const url = new URL(trimmed);
		const host = url.hostname.toLowerCase();
		if (host === 'gradio.app') {
			url.hostname = 'www.gradio.app';
			return url.toString();
		}
		return trimmed;
	} catch {
		return input;
	}
}
