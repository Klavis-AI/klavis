#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  Tool,
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Fetcher } from "./Fetcher.js";
import { RequestPayload } from "./types.js";
import express, { Request, Response } from "express";

process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  process.exit(1);
});

// Define the input schema for all fetch tools
const fetchInputSchema = {
  type: "object" as const,
  properties: {
    url: {
      type: "string",
      description: "URL of the website to fetch",
    },
    headers: {
      type: "object",
      additionalProperties: { type: "string" },
      description: "Optional headers to include in the request",
    },
  },
  required: ["url"],
};

// Tool definitions
const FETCH_HTML_TOOL: Tool = {
  name: "fetch_html",
  description: "Fetch a website and return the content as HTML",
  inputSchema: fetchInputSchema,
  annotations: {
    category: "FETCH_URL",
    readOnlyHint: true,
  },
};

const FETCH_MARKDOWN_TOOL: Tool = {
  name: "fetch_markdown",
  description: "Fetch a website and return the content as Markdown",
  inputSchema: fetchInputSchema,
  annotations: {
    category: "FETCH_URL",
    readOnlyHint: true,
  },
};

const FETCH_TXT_TOOL: Tool = {
  name: "fetch_txt",
  description: "Fetch a website, return the content as plain text (no HTML)",
  inputSchema: fetchInputSchema,
  annotations: {
    category: "FETCH_URL",
    readOnlyHint: true,
  },
};

const FETCH_JSON_TOOL: Tool = {
  name: "fetch_json",
  description: "Fetch a JSON file from a URL",
  inputSchema: fetchInputSchema,
  annotations: {
    category: "FETCH_URL",
    readOnlyHint: true,
  },
};

// Factory function to create a new MCP server instance for each request
function createMcpServer(): Server {
  const server = new Server(
    {
      name: "fetch-url-mcp",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        FETCH_HTML_TOOL,
        FETCH_MARKDOWN_TOOL,
        FETCH_TXT_TOOL,
        FETCH_JSON_TOOL,
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case "fetch_html": {
          return await Fetcher.html(args as RequestPayload);
        }
        case "fetch_markdown": {
          return await Fetcher.markdown(args as RequestPayload);
        }
        case "fetch_txt": {
          return await Fetcher.txt(args as RequestPayload);
        }
        case "fetch_json": {
          return await Fetcher.json(args as RequestPayload);
        }
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error: any) {
      console.error(`Tool ${name} failed:`, error.message);
      return {
        content: [
          {
            type: "text",
            text: `Error: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  });

  return server;
}

async function main() {
  const app = express();
  const PORT = process.env.PORT || 5000;

  app.use(express.json());

  app.post("/mcp", async (req: Request, res: Response) => {
    console.log("MCP connection request received");

    // Create new server and transport for each request
    const server = createMcpServer();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    try {
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);

      // Clean up when request closes
      res.on("close", () => {
        console.log("Request closed");
        transport.close();
        server.close();
      });
    } catch (error) {
      console.error("Error handling MCP request:", error);
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: {
            code: -32603,
            message: "Internal server error",
          },
          id: null,
        });
      }
    }
  });

  app.get("/mcp", async (req: Request, res: Response) => {
    console.log("Received GET MCP request");
    res.writeHead(405).end(JSON.stringify({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    }));
  });

  app.delete("/mcp", async (req: Request, res: Response) => {
    console.log("Received DELETE MCP request");
    res.writeHead(405).end(JSON.stringify({
      jsonrpc: "2.0",
      error: {
        code: -32000,
        message: "Method not allowed."
      },
      id: null
    }));
  });

  app.get("/health", (req: Request, res: Response) => {
    res.json({ status: "ok", name: "@tokenizin/mcp-npx-fetch" });
  });

  app.listen(PORT, () => {
    console.log(`MCP server listening on http://localhost:${PORT}`);
    console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}

main().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
