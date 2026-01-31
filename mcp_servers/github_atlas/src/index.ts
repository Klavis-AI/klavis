#!/usr/bin/env node
import express, { Request, Response } from 'express';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { Octokit } from "octokit"
import { z } from "zod"
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';
import { registerIssueTools } from "./tools/issues.js"
import { registerPullRequestTools } from "./tools/pullrequests.js"
import { registerRepositoryTools } from "./tools/repositories.js"
import { registerSearchTools } from "./tools/search.js"

dotenv.config();

export const configSchema = z.object({
	githubPersonalAccessToken: z.string(),
})

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
	octokit: Octokit;
}>();

// Getter function for the Octokit client
export function getOctokit(): Octokit {
	const store = asyncLocalStorage.getStore();
	if (!store) {
		throw new Error('Octokit client not found in AsyncLocalStorage');
	}
	return store.octokit;
}

// Utility function to extract access token from request
function extractAccessToken(req: Request): string {
	let authData = process.env.AUTH_DATA;
	
	if (!authData && req.headers['x-auth-data']) {
		try {
			authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
		} catch (error) {
			console.error('Error parsing x-auth-data JSON:', error);
		}
	}

	if (!authData) {
		console.error('Error: GitHub access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
		return '';
	}

	const authDataJson = JSON.parse(authData);
	return authDataJson.access_token ?? '';
}

// Create the MCP server
function getGitHubMcpServer() {
	try {
		console.log("Creating GitHub MCP Server...")

		// Create a new MCP server
		const server = new McpServer({
			name: "GitHub MCP Server",
			version: "1.0.0",
		})

		// Register tool groups (they will use getOctokit() internally)
		registerSearchTools(server)
		registerIssueTools(server)
		registerRepositoryTools(server)
		registerPullRequestTools(server)

		return server.server
	} catch (e) {
		console.error(e)
		throw e
	}
}

const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
	const accessToken = extractAccessToken(req);
	const octokit = new Octokit({ auth: accessToken });

	const server = getGitHubMcpServer();
	try {
		const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
			sessionIdGenerator: undefined,
		});
		await server.connect(transport);
		asyncLocalStorage.run({ octokit }, async () => {
			await transport.handleRequest(req, res, req.body);
		});
		res.on('close', () => {
			console.log('Request closed');
			transport.close();
			server.close();
		});
	} catch (error) {
		console.error('Error handling MCP request:', error);
		if (!res.headersSent) {
			res.status(500).json({
				jsonrpc: '2.0',
				error: {
					code: -32603,
					message: 'Internal server error',
				},
				id: null,
			});
		}
	}
});

app.get('/mcp', async (req: Request, res: Response) => {
	console.log('Received GET MCP request');
	res.writeHead(405).end(JSON.stringify({
		jsonrpc: "2.0",
		error: {
			code: -32000,
			message: "Method not allowed."
		},
		id: null
	}));
});

app.delete('/mcp', async (req: Request, res: Response) => {
	console.log('Received DELETE MCP request');
	res.writeHead(405).end(JSON.stringify({
		jsonrpc: "2.0",
		error: {
			code: -32000,
			message: "Method not allowed."
		},
		id: null
	}));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// to support multiple simultaneous connections we have a lookup object from
// sessionId to transport
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
	const transport = new SSEServerTransport(`/messages`, res);

	// Set up cleanup when connection closes
	res.on('close', async () => {
		console.log(`SSE connection closed for transport: ${transport.sessionId}`);
		try {
			transports.delete(transport.sessionId);
		} finally {
		}
	});

	transports.set(transport.sessionId, transport);

	const server = getGitHubMcpServer();
	await server.connect(transport);

	console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
	const sessionId = req.query.sessionId as string;
	const transport = transports.get(sessionId);
	if (transport) {
		const accessToken = extractAccessToken(req);
		const octokit = new Octokit({ auth: accessToken });

		asyncLocalStorage.run({ octokit }, async () => {
			await transport.handlePostMessage(req, res);
		});
	} else {
		console.error(`Transport not found for session ID: ${sessionId}`);
		res.status(404).send({ error: "Transport not found" });
	}
});

app.listen(5000, () => {
	console.log('GitHub MCP server running on port 5000');
});
