import { config } from 'dotenv';
import { Klavis, KlavisClient } from 'klavis';
import { MultiServerMCPClient } from "@langchain/mcp-adapters";  
import { createAgent } from "langchain";
import { ChatOpenAI } from "@langchain/openai";
import open from 'open';
import { createInterface } from 'readline/promises';

// Load environment variables
config();

async function main() {
    const klavisClient = new KlavisClient({ apiKey: process.env.KLAVIS_API_KEY });

    // Step 1: Create a Strata MCP server with Gmail and YouTube integrations
    const response = await klavisClient.mcpServer.createStrataServer({
        userId: 'demo_user',
        servers: [Klavis.McpServerName.Gmail, Klavis.McpServerName.Youtube],
    });

    // Step 2: Handle OAuth authorization if needed
    if (response.oauthUrls) {
        const rl = createInterface({
            input: process.stdin,
            output: process.stdout,
        });

        for (const [serverName, oauthUrl] of Object.entries(response.oauthUrls)) {
            await open(oauthUrl);
            await rl.question(`Press Enter after completing ${serverName} OAuth authorization...`);
        }
        
        rl.close();
    }

    // Step 3: Setup LLM
    const llm = new ChatOpenAI({
        modelName: 'gpt-4o-mini',
        apiKey: process.env.OPENAI_API_KEY!,
    });

    // Create MCP client with Strata server
    const mcpClient = new MultiServerMCPClient({
        throwOnLoadError: true,
        useStandardContentBlocks: true,
        mcpServers: {
            strata: {
                url: response.strataServerUrl,
                transport: "http"
            }
        }
    });

    const tools = await mcpClient.getTools();  

    // Step 4: Create LangChain agent with MCP tools
    const agent = createAgent({
        model: llm,
        tools: tools,
        systemPrompt: 'You are a helpful assistant that can use MCP tools.',
    });

    const myEmail = 'golden-kpop@example.com'; // TODO: Replace with your email

    // Step 5: Invoke the agent
    const result = await agent.invoke({
        messages: [{
            role: 'user' as const,
            content: `summarize this video - https://youtu.be/yebNIHKAC4A?si=1Rz_ZsiVRz0YfOR7 and send the summary to my email ${myEmail}`
        }],
    });

    // Print only the final AI response content
    const lastMessage = result.messages[result.messages.length - 1];
    console.log(lastMessage.content);
}


main()