#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import express, { Request, Response } from "express";
import dotenv from "dotenv";
import { AsyncLocalStorage } from "async_hooks";

dotenv.config();

// Added: Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  perplexityApiKey: string;
}>();

// Retrieve the Perplexity API key from environment variables
const PERPLEXITY_API_KEY = process.env.PERPLEXITY_API_KEY;

/**
 * Definition of the Perplexity Ask Tool.
 * This tool accepts an array of messages and returns a chat completion response
 * from the Perplexity API, with citations appended to the message if provided.
 */
const PERPLEXITY_ASK_TOOL: Tool = {
  name: "perplexity_ask",
  description:
    "Engages in a conversation using the Sonar API. " +
    "Accepts an array of messages (each with a role and content) " +
    "and returns a ask completion response from the Perplexity model.",
  inputSchema: {
    type: "object",
    properties: {
      messages: {
        type: "array",
        items: {
          type: "object",
          properties: {
            role: {
              type: "string",
              description: "Role of the message (e.g., system, user, assistant)",
            },
            content: {
              type: "string",
              description: "The content of the message",
            },
          },
          required: ["role", "content"],
        },
        description: "Array of conversation messages",
      },
    },
    required: ["messages"],
  },
};

/**
 * Definition of the Perplexity Research Tool.
 * This tool performs deep research queries using the Perplexity API.
 */
const PERPLEXITY_RESEARCH_TOOL: Tool = {
  name: "perplexity_research",
  description:
    "Performs deep research using the Perplexity API. " +
    "Accepts an array of messages (each with a role and content) " +
    "and returns a comprehensive research response with citations.",
  inputSchema: {
    type: "object",
    properties: {
      messages: {
        type: "array",
        items: {
          type: "object",
          properties: {
            role: {
              type: "string",
              description: "Role of the message (e.g., system, user, assistant)",
            },
            content: {
              type: "string",
              description: "The content of the message",
            },
          },
          required: ["role", "content"],
        },
        description: "Array of conversation messages",
      },
    },
    required: ["messages"],
  },
};

/**
 * Definition of the Perplexity Reason Tool.
 * This tool performs reasoning queries using the Perplexity API.
 */
const PERPLEXITY_REASON_TOOL: Tool = {
  name: "perplexity_reason",
  description:
    "Performs reasoning tasks using the Perplexity API. " +
    "Accepts an array of messages (each with a role and content) " +
    "and returns a well-reasoned response using the sonar-reasoning-pro model.",
  inputSchema: {
    type: "object",
    properties: {
      messages: {
        type: "array",
        items: {
          type: "object",
          properties: {
            role: {
              type: "string",
              description: "Role of the message (e.g., system, user, assistant)",
            },
            content: {
              type: "string",
              description: "The content of the message",
            },
          },
          required: ["role", "content"],
        },
        description: "Array of conversation messages",
      },
    },
    required: ["messages"],
  },
};

/**
 * Performs a chat completion by sending a request to the Perplexity API.
 * Appends citations to the returned message content if they exist.
 *
 * @param {Array<{ role: string; content: string }>} messages - An array of message objects.
 * @param {string} model - The model to use for the completion.
 * @returns {Promise<string>} The chat completion result with appended citations.
 * @throws Will throw an error if the API request fails.
 */
async function performChatCompletion(
  messages: Array<{ role: string; content: string }>,
  model: string = "sonar-pro",
  apiKey: string
): Promise<string> {
  // Construct the API endpoint URL and request body
  const url = new URL("https://api.perplexity.ai/chat/completions");
  const body = {
    model: model, // Model identifier passed as parameter
    messages: messages,
    // Additional parameters can be added here if required (e.g., max_tokens, temperature, etc.)
    // See the Sonar API documentation for more details: 
    // https://docs.perplexity.ai/api-reference/chat-completions
  };

  let response;
  try {
    response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(`Network error while calling Perplexity API: ${error}`);
  }

  // Check for non-successful HTTP status
  if (!response.ok) {
    let errorText;
    try {
      errorText = await response.text();
    } catch (parseError) {
      errorText = "Unable to parse error response";
    }
    throw new Error(
      `Perplexity API error: ${response.status} ${response.statusText}\n${errorText}`
    );
  }

  // Attempt to parse the JSON response from the API
  let data;
  try {
    data = await response.json();
  } catch (jsonError) {
    throw new Error(`Failed to parse JSON response from Perplexity API: ${jsonError}`);
  }

  // Directly retrieve the main message content from the response 
  let messageContent = data.choices[0].message.content;

  // If citations are provided, append them to the message content
  if (data.citations && Array.isArray(data.citations) && data.citations.length > 0) {
    messageContent += "\n\nCitations:\n";
    data.citations.forEach((citation: string, index: number) => {
      messageContent += `[${index + 1}] ${citation}\n`;
    });
  }

  return messageContent;
}

// Function to create a server instance
function createPerplexityServer(apiKey: string) {
  // Initialize the server with tool metadata and capabilities
  const server = new Server({
    id: "perplexity-mcp",
    name: "Perplexity MCP Server",
    version: "1.0.0",
  });
  
  // Register tools with the server
  server.registerToolProvider({
    prefix: "perplexity",
    listTools: async function listTools(request: any) {
      if (request.kind !== "list_tools") {
        throw new Error("Invalid request kind");
      }

      // Parse and validate the request
      const parsedRequest = ListToolsRequestSchema.parse(request);
      
      // Return the list of tools
      return {
        tools: [
          PERPLEXITY_ASK_TOOL,
          PERPLEXITY_RESEARCH_TOOL,
          PERPLEXITY_REASON_TOOL,
        ],
      };
    },
    callTool: async function callTool(request: any) {
      if (request.kind !== "call_tool") {
        throw new Error("Invalid request kind");
      }

      // Parse and validate the request
      const parsedRequest = CallToolRequestSchema.parse(request);
      const { tool, arguments: args } = parsedRequest;

      // Validate that messages are provided
      if (!args.messages || !Array.isArray(args.messages)) {
        throw new Error("Missing or invalid 'messages' in arguments");
      }

      try {
        // Get the API key from the context
        const ctx = asyncLocalStorage.getStore();
        const currentApiKey = ctx ? ctx.perplexityApiKey : apiKey;
        
        if (!currentApiKey) {
          throw new Error("Perplexity API key not found");
        }
        
        let model = "sonar-pro"; // Default model
        
        // Select the appropriate model based on the tool
        if (tool === "perplexity_research") {
          model = "sonar-pro";
        } else if (tool === "perplexity_reason") {
          model = "sonar-reasoning-pro";
        }
        
        // Perform the chat completion
        const result = await performChatCompletion(args.messages, model, currentApiKey);
        
        // Return the result
        return {
          result: {
            content: result,
          },
        };
      } catch (error: any) {
        // Handle errors
        const errorMessage = error.message || "Unknown error occurred";
        console.error(`Error calling Perplexity API: ${errorMessage}`);
        
        return {
          result: {
            error: errorMessage,
          },
        };
      }
    },
  });

  return server;
}

// Initialize Express app
const app = express();
const port = process.env.PORT || 5000;

// Get server type from command line arguments
const serverType = process.argv[2] || "stdio";

// For stdio mode, just create and serve a single instance
if (serverType === "stdio") {
  const stdioServer = createPerplexityServer(PERPLEXITY_API_KEY || "");
  stdioServer.serve(new StdioServerTransport());
} else {
  // For HTTP and SSE modes, set up express endpoints
  
  // Map to store SSE transports by session ID
  const transports = new Map<string, SSEServerTransport>();

  //=============================================================================
  // STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
  //=============================================================================
  
  app.post('/mcp', async (req: Request, res: Response) => {
    // Extract API key from environment or header
    const apiKey = process.env.PERPLEXITY_API_KEY || 
                  req.headers['x-auth-token'] as string || 
                  req.headers['access_token'] as string;
    
    if (!apiKey) {
      console.error('Error: Perplexity API key is missing. Provide it via PERPLEXITY_API_KEY env var, x-auth-token or access_token header.');
      res.status(401).json({ error: 'API key is required' });
      return;
    }
    
    try {
      // Create a new server instance for this request
      const server = createPerplexityServer(apiKey);
      const transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });
      
      await server.connect(transport);
      
      // Run within AsyncLocalStorage context
      asyncLocalStorage.run({ perplexityApiKey: apiKey }, async () => {
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
    res.status(405).json({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    });
  });

  //=============================================================================
  // DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
  //=============================================================================
  
  app.get("/sse", async (req: Request, res: Response) => {
    const transport = new SSEServerTransport(`/messages`, res);
    
    // Set up cleanup when connection closes
    res.on('close', async () => {
      console.log(`SSE connection closed for transport: ${transport.sessionId}`);
      transports.delete(transport.sessionId);
    });
    
    transports.set(transport.sessionId, transport);
    
    // Create a new server for this SSE connection
    const apiKey = process.env.PERPLEXITY_API_KEY || '';
    const server = createPerplexityServer(apiKey);
    await server.connect(transport);
    
    console.log(`SSE connection established with transport: ${transport.sessionId}`);
  });
  
  app.post("/messages", async (req: Request, res: Response) => {
    const sessionId = req.query.sessionId as string;
    const transport = transports.get(sessionId);
    
    if (transport) {
      // Extract API key from environment or header
      const apiKey = process.env.PERPLEXITY_API_KEY || 
                    req.headers['x-auth-token'] as string || 
                    req.headers['access_token'] as string;
      
      if (!apiKey) {
        console.error('Error: Perplexity API key is missing. Provide it via PERPLEXITY_API_KEY env var, x-auth-token or access_token header.');
        res.status(401).json({ error: 'API key is required' });
        return;
      }
      
      // Run within AsyncLocalStorage context
      asyncLocalStorage.run({ perplexityApiKey: apiKey }, async () => {
        await transport.handlePostMessage(req, res);
      });
    } else {
      console.error(`Transport not found for session ID: ${sessionId}`);
      res.status(404).send({ error: "Transport not found" });
    }
  });

  // Start the server
  app.listen(port, () => {
    console.log(`Perplexity MCP server is running on port ${port}`);
  });
}
