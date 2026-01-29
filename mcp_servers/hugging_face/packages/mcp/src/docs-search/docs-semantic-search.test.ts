import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DocSearchTool } from './docs-semantic-search.js';
import { DOC_FETCH_CONFIG } from './doc-fetch.js';

// Mock the fetch function
const mockFetch = vi.fn();
global.fetch = mockFetch as typeof fetch;

// Helper to create a proper mock Response
function createMockResponse(data: unknown) {
	const jsonString = JSON.stringify(data);
	return {
		ok: true,
		text: () => Promise.resolve(jsonString),
		json: () => Promise.resolve(data),
		headers: new Headers({ 'content-type': 'application/json' }),
	};
}

describe('DocSearchTool', () => {
	let docSearchTool: DocSearchTool;

	beforeEach(() => {
		docSearchTool = new DocSearchTool();
		vi.clearAllMocks();
	});

	describe('search', () => {
		it('should return error when query is too short', async () => {
			await expect(docSearchTool.search({ query: 'ab' })).rejects.toThrow();
		});

		it('should return no results message when API returns empty array', async () => {
			mockFetch.mockResolvedValueOnce(createMockResponse([]));

			const result = await docSearchTool.search({ query: 'nonexistent' });
			expect(result.formatted).toBe(`No documentation found for query 'nonexistent'`);
			expect(result.totalResults).toBe(0);
			expect(result.resultsShared).toBe(0);
		});

		it('should return no results message with product filter', async () => {
			mockFetch.mockResolvedValueOnce(createMockResponse([]));

			const result = await docSearchTool.search({ query: 'nonexistent', product: 'hub' });
			expect(result.formatted).toBe(`No documentation found for query 'nonexistent' in product 'hub'`);
			expect(result.totalResults).toBe(0);
			expect(result.resultsShared).toBe(0);
		});

		it('should format results grouped by product and page', async () => {
			const sampleResults = [
				{
					text: 'Download a comprehensive CSV file containing analytics',
					product: 'hub',
					heading1: 'Analytics',
					source_page_url: 'https://huggingface.co/docs/hub/enterprise-hub-analytics#export-analytics-as-csv',
					source_page_title: 'Enterprise-hub-analytics',
					heading2: 'Export Analytics as CSV',
				},
				{
					text: 'View analytics for your repositories',
					product: 'hub',
					heading1: 'Analytics',
					source_page_url: 'https://huggingface.co/docs/hub/enterprise-hub-analytics#export-analytics-as-csv',
					source_page_title: 'Enterprise-hub-analytics',
					heading2: 'View Analytics',
				},
				{
					text: 'In this quickstart, you will learn how to use the dataset viewer REST API',
					product: 'dataset-viewer',
					heading1: 'Quickstart',
					source_page_url: 'https://huggingface.co/docs/dataset-viewer/quick_start#quickstart',
					source_page_title: 'Quick start',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'analytics' });

			// Check header
			expect(result.formatted).toContain('# Documentation Library Search Results for "analytics"');
			expect(result.formatted).toContain('Found 3 results');
			expect(result.totalResults).toBe(3);
			expect(result.resultsShared).toBe(3);

			// Check product grouping - hub should come before dataset-viewer (hub has 2 results, dataset-viewer has 1)
			const hubIndex = result.formatted.indexOf('## Results for Product: hub');
			const datasetViewerIndex = result.formatted.indexOf('## Results for Product: dataset-viewer');
			expect(hubIndex).toBeLessThan(datasetViewerIndex);
			expect(hubIndex).toBeGreaterThan(-1);
			expect(datasetViewerIndex).toBeGreaterThan(-1);

			// Check that result counts are shown
			expect(result.formatted).toContain('## Results for Product: hub (2 results)');
			expect(result.formatted).toContain('## Results for Product: dataset-viewer (1 results)');

			// Check page links (without anchors)
			expect(result.formatted).toContain(
				'### Results from [Analytics](https://huggingface.co/docs/hub/enterprise-hub-analytics)'
			);
			expect(result.formatted).toContain('### Results from [Quickstart](https://huggingface.co/docs/dataset-viewer/quick_start)');

			// Check excerpts with heading2
			expect(result.formatted).toContain('#### Excerpt from the "Export Analytics as CSV" section');
			expect(result.formatted).toContain('#### Excerpt from the "View Analytics" section');

			// Check excerpt content appears as plain text
			expect(result.formatted).toContain('Download a comprehensive CSV file containing analytics');
			expect(result.formatted).toContain('View analytics for your repositories');
			expect(result.formatted).toContain('In this quickstart, you will learn how to use the dataset viewer REST API');

			// Check footer
			expect(result.formatted).toContain('Use the "' + DOC_FETCH_CONFIG.name + '" tool to fetch a document from the library.');
		});

		it('should handle results without heading2', async () => {
			const sampleResults = [
				{
					text: 'This is a simple text without heading2',
					product: 'transformers',
					heading1: 'Introduction',
					source_page_url: 'https://huggingface.co/docs/transformers/index',
					source_page_title: 'Transformers',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'transformers' });

			// Should not contain "Excerpt from" when heading2 is missing
			expect(result.formatted).not.toContain('#### Excerpt from');
			expect(result.formatted).toContain('This is a simple text without heading2');
			expect(result.totalResults).toBe(1);
			expect(result.resultsShared).toBe(1);
		});

		it('should properly escape markdown special characters', async () => {
			const sampleResults = [
				{
					text: 'Text with [brackets] and *asterisks* and _underscores_',
					product: 'hub',
					heading1: 'Special * Characters',
					source_page_url: 'https://huggingface.co/docs/hub/test',
					source_page_title: 'Test',
					heading2: 'Section with [brackets]',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'special' });

			// Check that special characters are escaped in headings and page titles
			expect(result.formatted).toContain('Special \\* Characters');
			// Note: heading2 appears in header text, but brackets don't get escaped
			expect(result.formatted).toContain('#### Excerpt from the "Section with [brackets]" section');
			expect(result.totalResults).toBe(1);
			expect(result.resultsShared).toBe(1);
		});

		it('should clean HTML tags from text', async () => {
			const sampleResults = [
				{
					text: 'Text with <div class="test">HTML tags</div> and <img src="test.png" alt="image"/>',
					product: 'hub',
					heading1: 'HTML Test',
					source_page_url: 'https://huggingface.co/docs/hub/html-test',
					source_page_title: 'HTML Test',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'html' });

			// HTML tags should be removed
			expect(result.formatted).toContain('Text with HTML tags and');
			expect(result.formatted).not.toContain('<div');
			expect(result.formatted).not.toContain('<img');
			expect(result.totalResults).toBe(1);
			expect(result.resultsShared).toBe(1);
		});

		it('should sort multiple products and pages correctly by count', async () => {
			const sampleResults = [
				// Hub has 3 results (should be first)
				{
					text: 'Result from hub page 1 - first',
					product: 'hub',
					heading1: 'Page 1',
					source_page_url: 'https://huggingface.co/docs/hub/page1',
					source_page_title: 'Page 1',
				},
				{
					text: 'Result from hub page 1 - second',
					product: 'hub',
					heading1: 'Page 1',
					source_page_url: 'https://huggingface.co/docs/hub/page1',
					source_page_title: 'Page 1',
				},
				{
					text: 'Result from hub page 2',
					product: 'hub',
					heading1: 'Page 2',
					source_page_url: 'https://huggingface.co/docs/hub/page2',
					source_page_title: 'Page 2',
				},
				// Transformers has 1 result (should be second)
				{
					text: 'Result from transformers',
					product: 'transformers',
					heading1: 'Transformers Page',
					source_page_url: 'https://huggingface.co/docs/transformers/page1',
					source_page_title: 'Transformers',
				},
				// Datasets has 1 result (should be third)
				{
					text: 'Result from datasets',
					product: 'datasets',
					heading1: 'Datasets Page',
					source_page_url: 'https://huggingface.co/docs/datasets/page1',
					source_page_title: 'Datasets',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'test' });

			// Check product order by count: hub (3) > transformers (1) = datasets (1)
			const hubIndex = result.formatted.indexOf('## Results for Product: hub');
			const transformersIndex = result.formatted.indexOf('## Results for Product: transformers');
			const datasetsIndex = result.formatted.indexOf('## Results for Product: datasets');

			expect(hubIndex).toBeLessThan(transformersIndex);
			expect(hubIndex).toBeLessThan(datasetsIndex);

			// Check that hub shows total count
			expect(result.formatted).toContain('## Results for Product: hub (3 results)');

			// Check page order within hub product: page1 (2 results) should come before page2 (1 result)
			const page1Index = result.formatted.indexOf('https://huggingface.co/docs/hub/page1');
			const page2Index = result.formatted.indexOf('https://huggingface.co/docs/hub/page2');
			expect(page1Index).toBeLessThan(page2Index);

			// Check that page1 shows its multiple results count
			expect(result.formatted).toContain('### Results from [Page 1](https://huggingface.co/docs/hub/page1) (2 results)');
			expect(result.totalResults).toBe(5);
			expect(result.resultsShared).toBe(5);
		});

		it('should include product filter in API call when provided', async () => {
			mockFetch.mockResolvedValueOnce(createMockResponse([]));

			await docSearchTool.search({ query: 'test', product: 'hub' });

			expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('q=test&product=hub'), expect.any(Object));
		});

		it('should group results from the same page with different anchors together', async () => {
			const sampleResults = [
				{
					text: 'First result from section 1',
					product: 'hub',
					heading1: 'Analytics',
					source_page_url: 'https://huggingface.co/docs/hub/analytics#section1',
					source_page_title: 'Analytics Page',
					heading2: 'Section 1',
				},
				{
					text: 'Second result from section 2',
					product: 'hub',
					heading1: 'Analytics',
					source_page_url: 'https://huggingface.co/docs/hub/analytics#section2',
					source_page_title: 'Analytics Page',
					heading2: 'Section 2',
				},
				{
					text: 'Third result from section 3',
					product: 'hub',
					heading1: 'Analytics',
					source_page_url: 'https://huggingface.co/docs/hub/analytics#section3',
					source_page_title: 'Analytics Page',
					heading2: 'Section 3',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'analytics' });

			// All three results should be grouped under one page heading (without anchor)
			expect(result.formatted).toContain('### Results from [Analytics](https://huggingface.co/docs/hub/analytics) (3 results)');

			// All three excerpts should appear under the same page
			expect(result.formatted).toContain('First result from section 1');
			expect(result.formatted).toContain('Second result from section 2');
			expect(result.formatted).toContain('Third result from section 3');

			// There should only be one "Results from" heading for this page
			const resultsFromCount = (result.formatted.match(/### Results from/g) || []).length;
			expect(resultsFromCount).toBe(1);
			expect(result.totalResults).toBe(3);
			expect(result.resultsShared).toBe(3);
		});

		it('should handle API errors gracefully', async () => {
			mockFetch.mockRejectedValueOnce(new Error('Network error'));

			await expect(docSearchTool.search({ query: 'test' })).rejects.toThrow('Failed to search documentation:');
		});

		it('should handle token budget by truncating or switching to links', async () => {
			// Create a tool with a small token budget to trigger limits
			const smallBudgetTool = new DocSearchTool(undefined, undefined, 5000); // 5k token budget
			
			// Create a result with a very long excerpt
			const longText = 'This is a very long text that repeats. '.repeat(100); // ~3900 chars per excerpt
			
			// Create many results to exceed budget (5k tokens = ~16.5k chars)
			const manyResults: Array<{
				text: string;
				product: string;
				heading1: string;
				source_page_url: string;
				source_page_title: string;
				heading2: string;
			}> = [];
			// Create enough to exceed token budget when formatted
			for (let i = 0; i < 8; i++) {
				manyResults.push({
					text: longText,
					product: 'hub',
					heading1: `Page ${i}`,
					source_page_url: `https://huggingface.co/docs/hub/page${i}`,
					source_page_title: `Page ${i}`,
					heading2: `Section ${i}`,
				});
			}

			mockFetch.mockResolvedValueOnce(createMockResponse(manyResults));

			const result = await smallBudgetTool.search({ query: 'test' });

			// Should contain the header
			expect(result.formatted).toContain('# Documentation Library Search Results for "test"');
			expect(result.formatted).toContain('Found 8 results');

			// Early results should have full content
			expect(result.formatted).toContain('This is a very long text that repeats');

			// Debug: let's see what the result looks like
			console.log('Result length:', result.formatted.length);
			console.log('Estimated tokens:', Math.ceil(result.formatted.length / 3.3));
			
			// Check that early pages have content 
			expect(result.formatted).toContain('#### Excerpt from the "Section 0" section');
			expect(result.formatted).toContain('This is a very long text that repeats');
			
			// With token budget, we should see either truncation or link-only section
			const hasTruncation = result.formatted.includes(`*[Content truncated - use ${DOC_FETCH_CONFIG.name} for full text or narrow search terms]*`);
			const hasAdditionalResults = result.formatted.includes('## Further results were found in:');
			
			
			// At least one of these should indicate budget management
			expect(hasTruncation || hasAdditionalResults).toBeTruthy();

			// Should still contain the footer
			expect(result.formatted).toContain(`Use the "${DOC_FETCH_CONFIG.name}" tool to fetch a document from the library.`);

			// Result should be around our smaller token budget (5k tokens = ~16.5k chars)
			expect(result.formatted.length).toBeLessThan(25000); // Should be controlled by token budget
			expect(result.totalResults).toBe(8);
			expect(result.resultsShared).toBe(8);
		});
	});

	describe('groupResults', () => {
		it('should group results by product and page URL', async () => {
			const sampleResults = [
				{
					text: 'Result 1',
					product: 'hub',
					heading1: 'Page 1',
					source_page_url: 'https://example.com/page1',
					source_page_title: 'Page 1',
				},
				{
					text: 'Result 2',
					product: 'hub',
					heading1: 'Page 1',
					source_page_url: 'https://example.com/page1',
					source_page_title: 'Page 1',
				},
				{
					text: 'Result 3',
					product: 'transformers',
					heading1: 'Page 2',
					source_page_url: 'https://example.com/page2',
					source_page_title: 'Page 2',
				},
			];

			mockFetch.mockResolvedValueOnce(createMockResponse(sampleResults));

			const result = await docSearchTool.search({ query: 'test' });

			// Verify grouping structure in output
			expect(result.formatted).toContain('## Results for Product: hub');
			expect(result.formatted).toContain('## Results for Product: transformers');

			// Verify that both results from the same page are together
			const result1Index = result.formatted.indexOf('Result 1');
			const result2Index = result.formatted.indexOf('Result 2');
			const result3Index = result.formatted.indexOf('Result 3');

			// Results 1 and 2 should be close together (same page)
			expect(Math.abs(result2Index - result1Index)).toBeLessThan(100);
			// Result 3 should be further away (different product)
			expect(Math.abs(result3Index - result1Index)).toBeGreaterThan(50);
			expect(result.totalResults).toBe(3);
			expect(result.resultsShared).toBe(3);
		});
	});
});
