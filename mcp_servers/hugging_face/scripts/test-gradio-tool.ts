import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import {
	LoggingMessageNotificationSchema,
	ResourceListChangedNotificationSchema,
	ToolListChangedNotificationSchema,
} from '@modelcontextprotocol/sdk/types.js';

const client = new Client(
	{
		name: 'hf-mcp-server-test-client',
		version: '0.0.1',
	},
	{
		capabilities: {},
	}
);

// Track notification counts
let notificationCount = 0;
const notificationCounts = {
	logging: 0,
	progress: 0,
	resourceListChanged: 0,
	toolListChanged: 0,
};

// Set up notification handlers for different notification types
client.setNotificationHandler(LoggingMessageNotificationSchema, (notification) => {
	notificationCount++;
	notificationCounts.logging++;
	console.log('[NOTIFICATION - Logging]', {
		level: notification.params.level,
		data: notification.params.data,
		logger: notification.params.logger,
		timestamp: new Date().toISOString(),
	});
});

async function testGradioTool() {
	try {
		const transport = new StreamableHTTPClientTransport(new URL('http://localhost:3000/mcp'));
		await client.connect(transport);
		console.log('[CLIENT] Connected to MCP server at http://localhost:3000');

		console.log('[CLIENT] Calling tool: gr1_evalstate_flux1_schnell');
		console.log("[CLIENT] Arguments: { prompt: 'kittens in space' }");

		const result = await client.callTool(
			{
				name: 'gr1_evalstate_flux1_schnell',
				arguments: {
					prompt: 'kittens in space',
				},
			},
			undefined,
			{
				onprogress: (progress) => {
					notificationCount++;
					notificationCounts.progress++;
					console.log('[PROGRESS]', {
						progress: progress.progress,
						total: progress.total,
						message: progress.message || 'Processing...',
						timestamp: new Date().toISOString(),
					});
				},
			}
		);

		console.log('[CLIENT] Tool result:', JSON.stringify(result, null, 2));

		// Wait a bit for any trailing notifications
		await new Promise((resolve) => setTimeout(resolve, 2000));

		// Display notification counts
		console.log('\n[NOTIFICATION SUMMARY]');
		console.log('─'.repeat(40));
		console.log(`Total notifications received: ${notificationCount}`);
		console.log('Breakdown by type:');
		console.log(`  - Logging: ${notificationCounts.logging}`);
		console.log(`  - Progress: ${notificationCounts.progress}`);
		console.log(`  - Resource List Changed: ${notificationCounts.resourceListChanged}`);
		console.log(`  - Tool List Changed: ${notificationCounts.toolListChanged}`);
		console.log('─'.repeat(40));

		console.log('\n[CLIENT] Test completed successfully');
		process.exit(0);
	} catch (error) {
		console.error('[CLIENT] Error calling tool:', error);
		process.exit(1);
	}
}

// Run the test
testGradioTool();
