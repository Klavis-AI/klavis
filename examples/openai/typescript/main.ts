import * as dotenv from 'dotenv';
import OpenAI from 'openai';
import { KlavisAPI, ServerName } from './klavis';
import * as readlineSync from 'readline-sync';

dotenv.config();

const openaiApiKey = process.env.OPENAI_API_KEY;
const klavisApiKey = process.env.KLAVIS_API_KEY;

if (!openaiApiKey) {
    throw new Error('OPENAI_API_KEY is not set in the environment variables.');
}
if (!klavisApiKey) {
    throw new Error('KLAVIS_API_KEY is not set in the environment variables.');
}

type Message = {
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | null;
    tool_calls?: any[];
    tool_call_id?: string;
};

async function getFunctionDefinitions(klavisClient: KlavisAPI, mcpInstance: { serverUrl: string }): Promise<any[]> {
    if (!klavisClient || !mcpInstance) {
        return [];
    }
    
    const toolsInfo = await klavisClient.listTools(mcpInstance.serverUrl);
    if (!toolsInfo.success) {
        return [];
    }

    const openai_tools: any[] = [];
    if (toolsInfo.tools) {
        for (const tool of toolsInfo.tools) {
            openai_tools.push({
                type: "function",
                function: {
                    name: tool.name,
                    description: tool.description,
                    parameters: tool.inputSchema || {}
                }
            });
        }
    }
    return openai_tools;
}

async function handleFunctionCall(
    functionName: string, 
    functionArgs: string, 
    klavisClient: KlavisAPI, 
    mcpInstance: { serverUrl: string }
): Promise<string> {
    try {
        const args = JSON.parse(functionArgs);
        const result = await klavisClient.callTool(
            mcpInstance.serverUrl,
            functionName,
            args
        );
        return JSON.stringify(result);
    } catch (e: any) {
        return JSON.stringify({ error: e.message });
    }
}

async function streamChatCompletion(
    client: OpenAI, 
    messages: Message[], 
    klavisClient: KlavisAPI, 
    mcpInstance: { serverUrl: string; instanceId: string }
) {
    try {
        const tools = await getFunctionDefinitions(klavisClient, mcpInstance);
        const stream = await client.chat.completions.create({
            model: "gpt-4o-mini",
            messages: messages as any,
            tools: tools.length > 0 ? tools as any : undefined,
            tool_choice: tools.length > 0 ? "auto" : undefined,
            stream: true,
            temperature: 0.7
        });

        let currentMessage: Message = { role: "assistant", content: "" };
        let toolCalls: any[] = [];
        let isToolCall = false;
        
        process.stdout.write("\n🤖 Assistant: ");

        for await (const chunk of stream) {
            if (chunk.choices[0]?.delta?.content) {
                const content = chunk.choices[0].delta.content;
                process.stdout.write(content);
                currentMessage.content = (currentMessage.content || "") + content;
            } else if (chunk.choices[0]?.delta?.tool_calls) {
                isToolCall = true;
                const deltaToolCalls = chunk.choices[0].delta.tool_calls;
                for (const deltaToolCall of deltaToolCalls) {
                    if (deltaToolCall.index !== undefined) {
                        while (toolCalls.length <= deltaToolCall.index) {
                            toolCalls.push({
                                id: "",
                                type: "function",
                                function: { name: "", arguments: "" }
                            });
                        }
                        const currentToolCall = toolCalls[deltaToolCall.index];
                        if (deltaToolCall.id) {
                            currentToolCall.id += deltaToolCall.id;
                        }
                        if (deltaToolCall.function) {
                            if (deltaToolCall.function.name) {
                                currentToolCall.function.name += deltaToolCall.function.name;
                            }
                            if (deltaToolCall.function.arguments) {
                                currentToolCall.function.arguments += deltaToolCall.function.arguments;
                            }
                        }
                    }
                }
            }
        }
        
        console.log();

        if (isToolCall && toolCalls.length > 0) {
            currentMessage.tool_calls = toolCalls;
            currentMessage.content = currentMessage.content || null;
            messages.push(currentMessage);

            for (const toolCall of toolCalls) {
                if (toolCall.function.name) {
                    console.log(`\n🔧 Calling function: ${toolCall.function.name}`);
                    const functionResult = await handleFunctionCall(
                        toolCall.function.name,
                        toolCall.function.arguments,
                        klavisClient,
                        mcpInstance
                    );
                    messages.push({
                        role: "tool",
                        tool_call_id: toolCall.id,
                        content: functionResult
                    });
                }
            }

            process.stdout.write("\n🤖 Assistant: ");
            const finalStream = await client.chat.completions.create({
                model: "gpt-4o-mini",
                messages: messages as any,
                stream: true
            });

            let finalMessage: Message = { role: "assistant", content: "" };
            for await (const chunk of finalStream) {
                if (chunk.choices[0]?.delta?.content) {
                    const content = chunk.choices[0].delta.content;
                    process.stdout.write(content);
                    finalMessage.content = (finalMessage.content || "") + content;
                }
            }
            messages.push(finalMessage);

        } else {
            messages.push(currentMessage);
        }
        console.log();

    } catch (e: any) {
        console.error(`\n❌ Error: ${e.message}`);
    }
}

async function main() {
    const openaiClient = new OpenAI({ apiKey: openaiApiKey });
    const klavisClient = new KlavisAPI(klavisApiKey!);

    const mcpInstance = await klavisClient.createMcpInstance(
        "Close" as ServerName,
        "1234",
        "demo"
    );
    await klavisClient.redirectToOauth(mcpInstance.instanceId, "Close" as ServerName);

    const messages: Message[] = [
        {
            role: "system",
            content: "You are a helpful assistant with access to various Klavis MCP tools"
        }
    ];

    while (true) {
        try {
            const userInput = readlineSync.question("\n👤 You: ").trim();

            if (['quit', 'exit', 'q'].includes(userInput.toLowerCase())) {
                console.log("\n👋 Goodbye!");
                break;
            }

            if (!userInput) {
                continue;
            }

            messages.push({ role: "user", content: userInput });
            await streamChatCompletion(openaiClient, messages, klavisClient, mcpInstance);

        } catch (e: any) {
            if (e.code === 'SIGINT') { // Catches Ctrl+C
                 console.log("\n\n👋 Goodbye!");
                 break;
            }
            console.error(`\n❌ Unexpected error: ${e.message}`);
        }
    }
}

main().catch(e => console.error(e)); 