import { describe, it, expect } from 'vitest';
import { extractArxivIdFromInput } from '../src/paper-summary.js';

describe('extractArxivIdFromInput', () => {
	it('should handle plain arXiv ID format', () => {
		expect(extractArxivIdFromInput('2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('2301.12345')).toBe('2301.12345');
		expect(extractArxivIdFromInput('1907.11692')).toBe('1907.11692');
	});

	it('should handle arxiv: prefix', () => {
		expect(extractArxivIdFromInput('arxiv:2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('ARXIV:2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('ArXiv:2502.16161')).toBe('2502.16161');
	});

	it('should handle arxiv. prefix (typo)', () => {
		expect(extractArxivIdFromInput('arxiv.2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('ARXIV.2502.16161')).toBe('2502.16161');
	});

	it('should handle Hugging Face paper URLs', () => {
		expect(extractArxivIdFromInput('https://huggingface.co/papers/2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('https://hf.co/papers/2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('huggingface.co/papers/2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('hf.co/papers/2502.16161')).toBe('2502.16161');
	});

	it('should handle arXiv.org URLs', () => {
		expect(extractArxivIdFromInput('https://arxiv.org/abs/2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('arxiv.org/abs/2502.16161')).toBe('2502.16161');
		expect(extractArxivIdFromInput('http://www.arxiv.org/abs/2502.16161')).toBe('2502.16161');
	});

	it('should trim whitespace', () => {
		expect(extractArxivIdFromInput('  2502.16161  ')).toBe('2502.16161');
		expect(extractArxivIdFromInput('\tarxiv:2502.16161\n')).toBe('2502.16161');
	});

	it('should reject invalid formats', () => {
		// Invalid arXiv ID patterns
		expect(() => extractArxivIdFromInput('2502.161')).toThrow('Invalid arXiv ID format');
		expect(() => extractArxivIdFromInput('502.16161')).toThrow('Invalid arXiv ID format');
		expect(() => extractArxivIdFromInput('2502.1616161')).toThrow('Invalid arXiv ID format');
		expect(() => extractArxivIdFromInput('abcd.efgh')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: abcd.efgh'
		);

		// Invalid prefixes
		expect(() => extractArxivIdFromInput('arxiv:2502.161')).toThrow('Invalid arXiv ID format after "arxiv:" prefix');
		expect(() => extractArxivIdFromInput('arxiv.abcd.efgh')).toThrow('Invalid arXiv ID format after "arxiv." prefix');

		// Invalid domains
		expect(() => extractArxivIdFromInput('https://example.com/papers/2502.16161')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: example.com'
		);
		expect(() => extractArxivIdFromInput('github.com/papers/2502.16161')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: github.com'
		);

		// Invalid paths on valid domains
		expect(() => extractArxivIdFromInput('https://arxiv.org/pdf/2502.16161')).toThrow(
			'arXiv URL must be in format: arxiv.org/abs/YYMM.NNNNN'
		);
		expect(() => extractArxivIdFromInput('https://hf.co/models/2502.16161')).toThrow(
			'Hugging Face URL must be in format: hf.co/papers/YYMM.NNNNN'
		);

		// Too short
		expect(() => extractArxivIdFromInput('25')).toThrow('Invalid arXiv ID format');
		expect(() => extractArxivIdFromInput('')).toThrow('Paper ID is required');

		// With query params or fragments
		expect(() => extractArxivIdFromInput('hf.co/papers/2502.16161?foo=bar')).toThrow(
			'URL must contain only the paper ID path'
		);
		expect(() => extractArxivIdFromInput('hf.co/papers/2502.16161#section')).toThrow(
			'URL must contain only the paper ID path'
		);
	});

	it('should reject obvious domain names without path', () => {
		expect(() => extractArxivIdFromInput('hf.co')).toThrow(
			'Hugging Face URL must be in format: hf.co/papers/YYMM.NNNNN'
		);
		expect(() => extractArxivIdFromInput('huggingface.com')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: huggingface.com'
		);
		expect(() => extractArxivIdFromInput('arxiv.org')).toThrow('arXiv URL must be in format: arxiv.org/abs/YYMM.NNNNN');
	});

	it('should handle edge cases for domain validation', () => {
		// Valid domains with valid paths
		expect(extractArxivIdFromInput('http://arxiv.org/abs/2301.12345')).toBe('2301.12345');
		expect(extractArxivIdFromInput('https://www.arxiv.org/abs/2301.12345')).toBe('2301.12345');

		// Invalid domains that might look similar
		expect(() => extractArxivIdFromInput('arxiv.com/abs/2502.16161')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: arxiv.com'
		);
		expect(() => extractArxivIdFromInput('huggingface.ai/papers/2502.16161')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: huggingface.ai'
		);
		expect(() => extractArxivIdFromInput('hf.ai/papers/2502.16161')).toThrow(
			'URL must be from arxiv.org, huggingface.co, or hf.co. Got: hf.ai'
		);

		// URLs without protocol should also work
		expect(extractArxivIdFromInput('arxiv.org/abs/2301.12345')).toBe('2301.12345');
		expect(extractArxivIdFromInput('hf.co/papers/2301.12345')).toBe('2301.12345');
		expect(extractArxivIdFromInput('huggingface.co/papers/2301.12345')).toBe('2301.12345');
	});
});
