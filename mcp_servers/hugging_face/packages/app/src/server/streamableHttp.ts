#!/usr/bin/env node

import { Application } from './application.js';
import { WebServer } from './web-server.js';
import { DEFAULT_WEB_APP_PORT } from '../shared/constants.js';
import { parseArgs } from 'node:util';
import { logger } from './utils/logger.js';

// Parse command line arguments
const { values } = parseArgs({
	options: {
		port: { type: 'string', short: 'p' },
		json: { type: 'boolean', short: 'j' },
	},
	args: process.argv.slice(2),
});

logger.info('Starting Streamable HTTP server...');
if (values.json) {
	logger.info('JSON response mode enabled');
}

// Set development mode environment variable
process.env.NODE_ENV = process.env.NODE_ENV || 'production';

// Configuration with single port for both the web app and MCP API
const port = parseInt((values.port as string) || process.env.WEB_APP_PORT || DEFAULT_WEB_APP_PORT.toString());

async function start() {
	const useJsonMode = values.json || false;

	// Choose the appropriate transport type based on JSON mode
	const transportType = useJsonMode ? 'streamableHttpJson' : 'streamableHttp';

	// Create WebServer instance
	const webServer = new WebServer();

	// Create Application instance
	const app = new Application({
		transportType,
		webAppPort: port,
		webServerInstance: webServer,
	});

	// Start the application
	await app.start();

	// Handle server shutdown
	let shutdownInProgress = false;
	const shutdown = async () => {
		logger.info('Shutting down server...');
		shutdownInProgress = true;
		try {
			await app.stop();
			logger.info('Server shutdown complete');
		} catch (error) {
			logger.error({ error }, 'Error during shutdown');
			process.exit(1);
		}
	};

	process.once('SIGINT', () => {
		void shutdown();
		// Set up second SIGINT handler for force exit
		process.once('SIGINT', () => {
			if (shutdownInProgress) {
				logger.warn('Force exit requested, terminating immediately...');
				process.exit(1);
			}
		});
	});

	process.once('SIGTERM', () => {
		void shutdown();
	});
}

// Run the async start function
start().catch((error: unknown) => {
	logger.error({ error }, 'Server startup error');
	process.exit(1);
});
