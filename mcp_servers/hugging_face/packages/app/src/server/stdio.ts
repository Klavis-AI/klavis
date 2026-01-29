#!/usr/bin/env node

// Set environment variables BEFORE importing logger
process.env.NODE_ENV = process.env.NODE_ENV || 'production';
process.env.TRANSPORT = process.env.TRANSPORT || 'STDIO';

import { Application } from './application.js';
import { WebServer } from './web-server.js';
import { DEFAULT_WEB_APP_PORT } from '../shared/constants.js';
import { parseArgs } from 'node:util';
import { logger, forceLoggerToStderr } from './utils/logger.js';

// Force logger to use STDERR. The environment variable may not have been set in dev, so just force it.
forceLoggerToStderr();

// Parse command line arguments
const { values } = parseArgs({
	options: {
		port: { type: 'string', short: 'p' },
	},
	args: process.argv.slice(2),
});

logger.info('Starting (STDIO) server...');

const port = parseInt((values.port as string) || process.env.WEB_APP_PORT || DEFAULT_WEB_APP_PORT.toString());

async function main() {
	// Create WebServer instance
	const webServer = new WebServer();

	// Create Application instance
	const app = new Application({
		transportType: 'stdio',
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

main().catch((error: unknown) => {
	logger.error({ error }, 'Server error');
	process.exit(1);
});
