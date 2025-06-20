import * as dotenv from 'dotenv';
import OpenAI from 'openai';
import { KlavisClient, Klavis } from 'klavis';
import open from 'open';

// Load environment variables
dotenv.config();

const openaiApiKey = process.env.OPENAI_API_KEY;
const klavisApiKey = process.env.KLAVIS_API_KEY;

if (!openaiApiKey) {
    throw new Error('OPENAI_API_KEY is not set in the environment variables.');
}
if (!klavisApiKey) {
    throw new Error('KLAVIS_API_KEY is not set in the environment variables.');
}

const openaiClient = new OpenAI({ apiKey: openaiApiKey });
const klavisClient = new KlavisClient({ apiKey: klavisApiKey });

type Message = {
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | null;
    tool_calls?: any[];
    tool_call_id?: string;
};

/**
 * General method to use MCP Server with OpenAI
 */
async function openaiWithMcpServer(mcpServerUrl: string, userQuery: string): Promise<string> {
    const messages: Message[] = [
        { role: "system", content: "You are a helpful assistant. Use the available tools to answer the user's question." },
        { role: "user", content: userQuery }
    ];

    // Get tools from MCP server
    const mcpServerTools = await klavisClient.mcpServer.listTools({
        serverUrl: mcpServerUrl,
        connectionType: Klavis.ConnectionType.StreamableHttp,
        format: Klavis.ToolFormat.Openai
    });
    
    const openaiTools = mcpServerTools.tools || [];

    const response = await openaiClient.chat.completions.create({
        model: "gpt-4o-mini",
        messages: messages as any,
        tools: mcpServerTools.tools as any
    });

    messages.push(response.choices[0].message as any);

    // Handle tool calls if any
    if (response.choices[0].message.tool_calls) {
        for (const toolCall of response.choices[0].message.tool_calls) {
            const functionName = toolCall.function.name;
            const functionArgs = JSON.parse(toolCall.function.arguments);
            
            console.log(`🔧 Calling: ${functionName}, with args:`, functionArgs);
            
            // Call the tool via Klavis
            const result = await klavisClient.mcpServer.callTools({
                serverUrl: mcpServerUrl,
                toolName: functionName,
                toolArgs: functionArgs,
                connectionType: Klavis.ConnectionType.StreamableHttp
            });
            
            messages.push({
                role: "tool",
                tool_call_id: toolCall.id,
                content: JSON.stringify(result)
            });
        }
    }

    // Final completion with tool results
    const finalResponse = await openaiClient.chat.completions.create({
        model: "gpt-4o-mini",
        messages: messages as any
    });

    return finalResponse.choices[0].message.content || "";
}

/**
 * Gmail Integration Demo (OAuth required)
 */
async function demoGmailIntegration() {
    console.log("\n📧 === OpenAI + Gmail MCP Server Demo (OAuth needed) ===\n");

    // Step 1: Create Gmail MCP Server
    console.log("📨 Creating Gmail MCP server instance...");
    const gmailMcpServer = await klavisClient.mcpServer.createServerInstance({
        serverName: Klavis.McpServerName.Gmail,
        userId: "1234", 
        platformName: "Klavis",
        connectionType: Klavis.ConnectionType.StreamableHttp
    });

    // Step 2: Handle OAuth authentication
    if (gmailMcpServer.oauthUrl) {
        console.log("🔐 Opening OAuth authorization for Gmail...");
        await open(gmailMcpServer.oauthUrl);
    }
    
    console.log("⏳ Please complete the OAuth authorization in your browser.");
    console.log("📋 Press Enter after completing OAuth authorization...");
    
    // Wait for user input (press enter to continue)
    await new Promise(resolve => {
        process.stdin.once('data', () => resolve(true));
    });

    // Step 3: Send test email
    const EMAIL_RECIPIENT = "zihaolin@klavis.ai"; // Replace with your email
    const EMAIL_SUBJECT = "Test OpenAI + Gmail MCP Server";
    const EMAIL_BODY = "Hello World from TypeScript demo!";
    
    try {
        const result = await openaiWithMcpServer(
            gmailMcpServer.serverUrl,
            `Please send an email to ${EMAIL_RECIPIENT} with subject "${EMAIL_SUBJECT}" and body "${EMAIL_BODY}"`
        );

        console.log("📧 Email Result:");
        console.log(result);
        console.log("\n✅ Gmail integration completed successfully!\n");
    } catch (error) {
        console.error("❌ Gmail integration failed:", error);
        console.log("💡 Make sure you've completed the OAuth authorization process.\n");
    }
}

async function main() {
    try {
        await demoGmailIntegration();

        console.log("🎉 Demo completed successfully!");
        console.log("🛠️  You can now build powerful AI applications with OpenAI + Klavis MCP servers!");

    } catch (error) {
        console.error("❌ Demo failed:", error);
        process.exit(1);
    }
}

// Run the demo
if (require.main === module) {
    main().catch(console.error);
}
