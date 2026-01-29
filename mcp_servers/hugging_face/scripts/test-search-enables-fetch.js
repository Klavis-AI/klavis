#!/usr/bin/env node

// Test script to demonstrate SEARCH_ENABLES_FETCH feature

// Set up minimal test environment
process.env.NODE_ENV = 'test';

import { ToolSelectionStrategy } from '../packages/app/dist/server/lib/tool-selection-strategy.js';
import { McpApiClient } from '../packages/app/dist/server/lib/mcp-api-client.js';

// Create a mock API client
const config = {
	type: 'polling',
	baseUrl: 'http://localhost:3000',
	pollInterval: 5000,
	staticGradioEndpoints: [],
};

const transportInfo = {
	transport: 'streamableHttpJson',
	port: 3000,
	defaultHfTokenSet: false,
	jsonResponseEnabled: true,
	externalApiMode: false,
	stdioClient: null,
};

const apiClient = new McpApiClient(config, transportInfo);
const strategy = new ToolSelectionStrategy(apiClient);

async function testFeature() {
	console.log('Testing SEARCH_ENABLES_FETCH feature...\n');

	// Test 1: Without SEARCH_ENABLES_FETCH
	console.log('Test 1: Without SEARCH_ENABLES_FETCH');
	delete process.env.SEARCH_ENABLES_FETCH;

	const context1 = {
		headers: {},
		userSettings: {
			builtInTools: ['hf_doc_search', 'hf_model_search'],
			spaceTools: [],
		},
		hfToken: 'test-token',
	};

	const result1 = await strategy.selectTools(context1);
	console.log('Enabled tools:', result1.enabledToolIds);
	console.log('Contains hf_doc_fetch?', result1.enabledToolIds.includes('hf_doc_fetch'));
	console.log();

	// Test 2: With SEARCH_ENABLES_FETCH=true
	console.log('Test 2: With SEARCH_ENABLES_FETCH=true');
	process.env.SEARCH_ENABLES_FETCH = 'true';

	const context2 = {
		headers: {},
		userSettings: {
			builtInTools: ['hf_doc_search', 'hf_model_search'],
			spaceTools: [],
		},
		hfToken: 'test-token',
	};

	const result2 = await strategy.selectTools(context2);
	console.log('Enabled tools:', result2.enabledToolIds);
	console.log('Contains hf_doc_fetch?', result2.enabledToolIds.includes('hf_doc_fetch'));
	console.log();

	// Test 3: With SEARCH_ENABLES_FETCH=true but no hf_doc_search
	console.log('Test 3: With SEARCH_ENABLES_FETCH=true but no hf_doc_search');
	process.env.SEARCH_ENABLES_FETCH = 'true';

	const context3 = {
		headers: {},
		userSettings: {
			builtInTools: ['hf_model_search', 'hf_dataset_search'],
			spaceTools: [],
		},
		hfToken: 'test-token',
	};

	const result3 = await strategy.selectTools(context3);
	console.log('Enabled tools:', result3.enabledToolIds);
	console.log('Contains hf_doc_fetch?', result3.enabledToolIds.includes('hf_doc_fetch'));
}

testFeature().catch(console.error);
