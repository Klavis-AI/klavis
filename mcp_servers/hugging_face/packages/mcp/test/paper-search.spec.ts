import { describe, beforeEach, afterEach, it, expect } from 'vitest';
import type { PaperSearchResult } from '../src/paper-search.js';
import { authors } from '../src/paper-search.js';
import { published } from '../src/paper-search.js';
import { readFileSync } from 'fs';
import path from 'path';
import { formatDate } from '../src/utilities.js';

describe('PaperSearchService', () => {
	let kazakh: PaperSearchResult[];
	function loadTestData(filename: string) {
		const filePath = path.join(__dirname, '../test/fixtures', filename);
		const fileContent = readFileSync(filePath, 'utf-8');
		return JSON.parse(fileContent) as PaperSearchResult[];
	}

	beforeEach(() => {
		kazakh = loadTestData('paper_result_kazakh.json');
	});

	afterEach(() => {});

	it('format the published on date correctly', () => {
		expect(published(kazakh[0]?.paper.publishedAt)).toBe('Published on 6 Apr, 2024');
	});

	//github.com/huggingface/huggingface_hub/blob/a26b93e8ba0b51ce76ce5c2044896587c47c6b60/src/huggingface_hub/utils/_datetime.py#L50-L62
	it('handles times with no decimal point', () => {
		expect(published('2021-08-30T00:04:01Z')).toBe('Published on 30 Aug, 2021');
	});

	it('deals with bad inputs', () => {
		expect(published('invalid_date')).toBe('Publication date not available');
	});

	it('shows us not available for empty list', () => {
		expect(authors([])).toBe('**Authors:** Not available');
	});

	it('shows us hf profiles for authors when known ', () => {
		expect(authors(kazakh[2]?.paper?.authors || [])).toBe(
			'**Authors:** Rustem Yeshpanov ([yeshpanovrustem](https://hf.co/yeshpanovrustem)), Huseyin Atakan Varol'
		);
	});

	it('shows us hf profiles when known ', () => {
		expect(authors(kazakh[2]?.paper?.authors || [])).toBe(
			'**Authors:** Rustem Yeshpanov ([yeshpanovrustem](https://hf.co/yeshpanovrustem)), Huseyin Atakan Varol'
		);
	});

	it("it won't break with herd of llamas that has 500 authors", () => {
		expect(authors(kazakh[0]?.paper?.authors || [], 1)).toBe(
			'**Authors:** Rustem Yeshpanov ([yeshpanovrustem](https://hf.co/yeshpanovrustem)), and 4 more.'
		);
	});
});
