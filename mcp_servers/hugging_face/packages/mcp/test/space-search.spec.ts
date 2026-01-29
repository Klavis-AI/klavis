import { describe, beforeEach, afterEach, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import path from 'path';
import { SpaceSearchResult } from '../dist/space-search.js';

describe('SpaceSearchService', () => {
	let space: SpaceSearchResult[];
	function loadTestData(filename: string) {
		const filePath = path.join(__dirname, '../test/fixtures', filename);
		const fileContent = readFileSync(filePath, 'utf-8');
		return JSON.parse(fileContent) as SpaceSearchResult[];
	}

	beforeEach(() => {
		space = loadTestData('space-result.json');
	});

	afterEach(() => {});

	it('read the test file', () => {
		expect('evalstate').toBe(space[2].author);
	});

	it('picked up other results', () => {
		expect('RUNNING').toBe(space[2].runtime.stage);
		expect('Image Generation').toBe(space[2].ai_category);
		expect('Generate images from text prompts').toBe(space[2].ai_short_description);
	});
});
