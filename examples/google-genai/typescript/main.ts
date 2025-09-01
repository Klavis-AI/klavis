import * as dotenv from 'dotenv';
import { GoogleGenAI, ToolListUnion } from '@google/genai';
import { KlavisClient, Klavis } from 'klavis';
import open from 'open';
import * as readline from 'readline';

// Load environment variables
dotenv.config();

const geminiApiKey = process.env.GEMINI_API_KEY;
const klavisApiKey = process.env.KLAVIS_API_KEY;

if (!geminiApiKey) {
    throw new Error('GEMINI_API_KEY is not set in the environment variables.');
}
if (!klavisApiKey) {
    throw new Error('KLAVIS_API_KEY is not set in the environment variables.');
}

const geminiClient = new GoogleGenAI({ apiKey: geminiApiKey });
const klavisClient = new KlavisClient({ apiKey: klavisApiKey });

// Create readline interface for user input
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// Helper function to prompt user input
function promptUser(question: string): Promise<string> {
    return new Promise((resolve) => {
        rl.question(question, (answer: string) => {
            resolve(answer);
        });
    });
}

async function main() {
    try {
        // Create MCP server instance
        const mcpInstance = await klavisClient.mcpServer.createServerInstance({
            serverName: Klavis.McpServerName.Notion,
            userId: "1234"});
        
        console.log("--- mcp_instance ---", mcpInstance);

        // Handle OAuth if needed
        if (mcpInstance.oauthUrl) {
            console.log(`🔐 Opening OAuth authorization: ${mcpInstance.oauthUrl}`);
            await open(mcpInstance.oauthUrl);
            console.log("Please complete the OAuth authorization in your browser...");
            await promptUser("Press Enter after completing OAuth authorization...");
        }

        // Get tools from Klavis
        const mcpTools = await klavisClient.mcpServer.listTools({
            serverUrl: mcpInstance.serverUrl,
            format: Klavis.ToolFormat.Gemini
        });

        const contents: any[] = [];

        // Extract function declarations from the Klavis response
        const gemini_tools = mcpTools.tools as ToolListUnion;
        const functionDeclarations = (gemini_tools[0] as any)?.function_declarations || [];

        console.log(`✅ Loaded ${functionDeclarations.length} function declarations`);

        // Chat loop
        while (true) {
            try {
                const userInput = await promptUser("👤 You: ");
                
                if (userInput.toLowerCase().trim() === 'quit' || 
                    userInput.toLowerCase().trim() === 'exit' || 
                    userInput.toLowerCase().trim() === 'q') {
                    break;
                }

                if (!userInput.trim()) {
                    continue;
                }

                contents.push({
                    role: "user",
                    parts: [{ text: userInput }]
                });

                const response = await geminiClient.models.generateContent({
                    model: 'gemini-2.5-flash',
                    contents: contents,
                    config: {
                        tools: [{
                            functionDeclarations: functionDeclarations
                        }]
                    }
                });

                if (!response.candidates || !response.candidates[0]?.content?.parts) {
                    console.log("No response generated.");
                    continue;
                }

                contents.push(response.candidates[0].content);
                
                // Check for function calls in the response
                let hasFunctionCalls = false;
                const functionCallResults: any[] = [];

                // Check if response has functionCalls property
                if (response.functionCalls && response.functionCalls.length > 0) {
                    hasFunctionCalls = true;
                    for (const functionCall of response.functionCalls) {
                        console.log(`\n🔧 Calling function: ${functionCall.name}`);

                        try {
                            // Execute tool call via Klavis
                            const functionResult = await klavisClient.mcpServer.callTools({
                                serverUrl: mcpInstance.serverUrl,
                                toolName: functionCall.name || '',
                                toolArgs: functionCall.args || {}
                            });
                            
                            functionCallResults.push({
                                functionResponse: {
                                    name: functionCall.name,
                                    response: functionResult.result
                                }
                            });
                        } catch (error) {
                            console.error(`❌ Function call error: ${error}`);
                            functionCallResults.push({
                                functionResponse: {
                                    name: functionCall.name,
                                    response: { error: String(error) }
                                }
                            });
                        }
                    }
                }

                // If there were function calls, add the results and get final response
                if (hasFunctionCalls && functionCallResults.length > 0) {
                    // Add function responses to conversation history
                    contents.push({
                        role: 'tool',
                        parts: functionCallResults
                    });

                    // Get final response after function execution
                    const finalResponse = await geminiClient.models.generateContent({
                        model: 'gemini-2.5-flash',
                        contents: contents,
                        config: {
                            tools: [{
                                functionDeclarations: functionDeclarations
                            }],
                            temperature: 0
                        }
                    });
                    
                    // Add final response to conversation history
                    if (finalResponse.candidates && finalResponse.candidates[0]?.content) {
                        contents.push(finalResponse.candidates[0].content);
                    }
                    
                    console.log(`\n🤖 Assistant: ${finalResponse.text || 'No response text'}`);
                } else {
                    // No function calls, just display the response
                    console.log(`\n🤖 Assistant: ${response.text || 'No response text'}`);
                }
                
            } catch (error) {
                console.error(`\n❌ Error: ${error}`);
                if (error instanceof Error) {
                    console.error(`Stack trace: ${error.stack}`);
                }
            }
        }
        
        console.log("\n\n👋 Goodbye!");
        
    } catch (error) {
        console.error("❌ Demo failed:", error);
        if (error instanceof Error) {
            console.error(`Stack trace: ${error.stack}`);
        }
        process.exit(1);
    } finally {
        rl.close();
    }
}

main();