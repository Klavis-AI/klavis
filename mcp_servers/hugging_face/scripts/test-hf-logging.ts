#!/usr/bin/env tsx

/**
 * Simple HF Dataset Logging Test
 * Usage: tsx test-hf-logging.ts <dataset-id>
 */

import { HfDatasetLogger } from '../packages/app/src/server/utils/hf-dataset-transport.js';

interface TestConfig {
	datasetId: string;
	loggingToken?: string;
}

class SimpleHfLoggingTester {
	private config: TestConfig;

	constructor(config: TestConfig) {
		this.config = config;
	}

	public async testBasicLogging(): Promise<void> {
		console.log('\n🧪 Testing basic HF dataset logging...');

		if (!this.config.loggingToken) {
			console.error('❌ No logging token provided. Set LOGGING_HF_TOKEN or DEFAULT_HF_TOKEN');
			return;
		}

		const logger = new HfDatasetLogger({
			loggingToken: this.config.loggingToken,
			datasetId: this.config.datasetId,
			batchSize: 3,
			flushInterval: 5000, // 5 seconds for testing
			baseRetryDelay: 1000,
		});

		// Send some test logs
		const testLogs = [
			{ level: 30, time: Date.now(), msg: 'Test info message', test: 'basic' },
			{ level: 40, time: Date.now(), msg: 'Test warning message', test: 'basic' },
			{ level: 50, time: Date.now(), msg: 'Test error message', test: 'basic' },
			{ level: 30, time: Date.now(), msg: 'Test fourth message (should trigger batch)', test: 'basic' },
		];

		console.log(`Sending ${testLogs.length} test logs...`);
		for (const log of testLogs) {
			logger.processLog(log);
			await new Promise((resolve) => setTimeout(resolve, 500));
		}

		console.log('Waiting 10 seconds for upload...');
		await new Promise((resolve) => setTimeout(resolve, 10000));

		console.log('Test completed! Check your HF dataset for new logs.');
		await logger.destroy();
	}
}

// CLI Interface
const args = process.argv.slice(2);
if (args.length === 0) {
	console.error('Usage: tsx test-hf-logging.ts <dataset-id>');
	console.error('Example: tsx test-hf-logging.ts evalstate/test-logs');
	process.exit(1);
}

const [datasetId] = args;
const config: TestConfig = {
	datasetId,
	loggingToken: process.env.LOGGING_HF_TOKEN || process.env.DEFAULT_HF_TOKEN,
};

const tester = new SimpleHfLoggingTester(config);
tester.testBasicLogging().catch(console.error);
