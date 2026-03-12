#!/usr/bin/env node

import { startMcpServer } from './server.js';

// Check for required environment variables
if (!process.env.YOUTUBE_API_KEY) {
    console.error('Error: YOUTUBE_API_KEY environment variable is required.');
    console.error('Please set it before running this server.');
    process.exit(1);
}

// Start the MCP server
startMcpServer()
    .then(() => {
        console.log('YouTube MCP Server started successfully');
    })
    .catch(error => {
        console.error('Failed to start YouTube MCP Server:', error);
        process.exit(1);
    });
