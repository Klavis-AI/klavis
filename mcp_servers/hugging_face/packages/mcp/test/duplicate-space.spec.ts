import { describe, it, expect } from 'vitest';
import { DuplicateSpaceTool } from '../src/duplicate-space.js';
import { NO_TOKEN_INSTRUCTIONS } from '../dist/utilities.js';

describe('DuplicateSpaceTool', () => {
	describe('normalizeSpaceName', () => {
		it('should prepend username when only space name is provided', () => {
			const tool = new DuplicateSpaceTool(undefined, 'evalstate');
			expect(tool.normalizeSpaceName('my-new-space')).toBe('evalstate/my-new-space');
		});

		it('should preserve space ID when username matches', () => {
			const tool = new DuplicateSpaceTool(undefined, 'evalstate');
			expect(tool.normalizeSpaceName('evalstate/their-space')).toBe('evalstate/their-space');
		});

		it('should throw error when trying to use different username', () => {
			const tool = new DuplicateSpaceTool(undefined, 'myusername');
			expect(() => tool.normalizeSpaceName('bad-user/new-space')).toThrow(
				'Invalid space ID: bad-user/new-space. You can only create spaces in your own namespace. Try "myusername/new-space"'
			);
		});

		it('should handle empty username gracefully', () => {
			const tool = new DuplicateSpaceTool();
			expect(tool.normalizeSpaceName('my-space')).toBe('unknown/my-space');
		});
	});

	describe('createToolConfig', () => {
		it('should include username in tool description', () => {
			const config = DuplicateSpaceTool.createToolConfig('evalstate');
			expect(config.description).toContain('evalstate/<new-space-name>');
		});

		it('should handle undefined username in description', () => {
			const config = DuplicateSpaceTool.createToolConfig();
			expect(config.description).toContain(NO_TOKEN_INSTRUCTIONS);
		});
	});
});
