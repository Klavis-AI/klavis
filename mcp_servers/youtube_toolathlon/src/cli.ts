#!/usr/bin/env node

import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createMcpServer } from './server.js';

const server = createMcpServer();
const transport = new StdioServerTransport();
server.connect(transport).then(() => {
    console.error('YouTube MCP Server started on stdio');
}).catch(error => {
    console.error('Failed to start YouTube MCP Server:', error);
    process.exit(1);
});
