import { describe, it, expect } from 'vitest';
import { extractUserIdFromInput } from '../src/user-summary.js';

describe('extractUserIdFromInput', () => {
	describe('valid inputs', () => {
		it('should extract user ID from plain username', () => {
			expect(extractUserIdFromInput('evalstate')).toBe('evalstate');
			expect(extractUserIdFromInput('meta-llama')).toBe('meta-llama');
			expect(extractUserIdFromInput('microsoft')).toBe('microsoft');
		});

		it('should handle usernames with whitespace', () => {
			expect(extractUserIdFromInput('  evalstate  ')).toBe('evalstate');
			expect(extractUserIdFromInput('\tevalstate\n')).toBe('evalstate');
		});

		it('should extract user ID from hf.co URLs', () => {
			expect(extractUserIdFromInput('hf.co/evalstate')).toBe('evalstate');
			expect(extractUserIdFromInput('https://hf.co/evalstate')).toBe('evalstate');
			expect(extractUserIdFromInput('http://hf.co/evalstate')).toBe('evalstate');
		});

		it('should extract user ID from huggingface.co URLs', () => {
			expect(extractUserIdFromInput('huggingface.co/evalstate')).toBe('evalstate');
			expect(extractUserIdFromInput('https://huggingface.co/evalstate')).toBe('evalstate');
			expect(extractUserIdFromInput('http://huggingface.co/evalstate')).toBe('evalstate');
		});

		it('should handle URLs with whitespace', () => {
			expect(extractUserIdFromInput('  hf.co/evalstate  ')).toBe('evalstate');
			expect(extractUserIdFromInput('\thttps://hf.co/evalstate\n')).toBe('evalstate');
		});

		it('should handle minimum length usernames', () => {
			expect(extractUserIdFromInput('abc')).toBe('abc');
			expect(extractUserIdFromInput('hf.co/abc')).toBe('abc');
		});
	});

	describe('invalid inputs', () => {
		it('should reject usernames shorter than 3 characters', () => {
			expect(() => extractUserIdFromInput('ab')).toThrow('User ID must be at least 3 characters long');
			expect(() => extractUserIdFromInput('a')).toThrow('User ID must be at least 3 characters long');
			expect(() => extractUserIdFromInput('')).toThrow('User ID must be at least 3 characters long');
		});

		it('should reject URLs with short usernames', () => {
			expect(() => extractUserIdFromInput('hf.co/ab')).toThrow('User ID must be at least 3 characters long');
			expect(() => extractUserIdFromInput('https://hf.co/a')).toThrow('User ID must be at least 3 characters long');
		});

		it('should reject non-Hugging Face domains', () => {
			expect(() => extractUserIdFromInput('github.com/evalstate')).toThrow(
				'URL must be from huggingface.co or hf.co domain'
			);
			expect(() => extractUserIdFromInput('https://example.com/evalstate')).toThrow(
				'URL must be from huggingface.co or hf.co domain'
			);
			expect(() => extractUserIdFromInput('evil-hf.co/evalstate')).toThrow(
				'URL must be from huggingface.co or hf.co domain'
			);
		});

		it('should reject URLs with multiple path segments', () => {
			expect(() => extractUserIdFromInput('hf.co/evalstate/models')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
			expect(() => extractUserIdFromInput('https://hf.co/evalstate/models/test')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
			expect(() => extractUserIdFromInput('huggingface.co/evalstate/datasets')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
		});

		it('should reject URLs with no path segments', () => {
			// "hf.co" without slash is treated as username but rejected as domain
			expect(() => extractUserIdFromInput('hf.co')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
			// URLs with explicit trailing slash should be rejected
			expect(() => extractUserIdFromInput('https://hf.co/')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
			// Domain-only format should be rejected as domain
			expect(() => extractUserIdFromInput('huggingface.co')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
		});

		it('should reject malformed URLs', () => {
			expect(() => extractUserIdFromInput('not://a/valid/url')).toThrow(
				'URL must be from huggingface.co or hf.co domain'
			);
			// Note: hf.co//evalstate actually gets normalized by URL constructor to hf.co/evalstate
			// so it's treated as valid. Testing a different malformed case instead:
			expect(() => extractUserIdFromInput('://invalid')).toThrow('Invalid URL format');
		});

		it('should reject URLs with query parameters', () => {
			expect(() => extractUserIdFromInput('hf.co/evalstate?tab=models')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
		});

		it('should reject URLs with fragments', () => {
			expect(() => extractUserIdFromInput('hf.co/evalstate#models')).toThrow(
				'URL must contain only the username (e.g., hf.co/username)'
			);
		});
	});

	describe('edge cases', () => {
		it('should handle special characters in usernames', () => {
			expect(extractUserIdFromInput('user-name')).toBe('user-name');
			expect(extractUserIdFromInput('user_name')).toBe('user_name');
			expect(extractUserIdFromInput('hf.co/user-name')).toBe('user-name');
			expect(extractUserIdFromInput('hf.co/user_name')).toBe('user_name');
		});

		it('should handle numeric usernames', () => {
			expect(extractUserIdFromInput('123')).toBe('123');
			expect(extractUserIdFromInput('hf.co/123')).toBe('123');
		});

		it('should handle mixed case usernames', () => {
			expect(extractUserIdFromInput('EvalState')).toBe('EvalState');
			expect(extractUserIdFromInput('hf.co/EvalState')).toBe('EvalState');
		});
	});
});
