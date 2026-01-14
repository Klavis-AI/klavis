#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { Fetcher } from "./Fetcher.js";
import { RequestPayload } from "./types.js";
import express, { Request, Response } from "express";
import { z } from "zod";

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
  url: z.string().describe("URL of the website to fetch"),
  headers: z.record(z.string(), z.string()).optional().describe("Optional headers to include in the request"),
};

// Factory function to create a new MCP server instance for each request
function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "fetch-url-mcp",
    version: "1.0.0",
  });

  // Register fetch_html tool
  server.registerTool(
    "fetch_html",
    {
      description: "Fetch a website and return the content as HTML",
      inputSchema: fetchInputSchema,
      annotations: { category: "FETCH_URL" },
    },
    async (args) => {
      return await Fetcher.html(args as RequestPayload);
    }
  );

  // Register fetch_markdown tool
  server.registerTool(
    "fetch_markdown",
    {
      description: "Fetch a website and return the content as Markdown",
      inputSchema: fetchInputSchema,
      annotations: { category: "FETCH_URL" },
    },
    async (args) => {
      return await Fetcher.markdown(args as RequestPayload);
    }
  );

  // Register fetch_txt tool
  server.registerTool(
    "fetch_txt",
    {
      description: "Fetch a website, return the content as plain text (no HTML)",
      inputSchema: fetchInputSchema,
      annotations: { category: "FETCH_URL" },
    },
    async (args) => {
      return await Fetcher.txt(args as RequestPayload);
    }
  );

  // Register fetch_json tool
  server.registerTool(
    "fetch_json",
    {
      description: "Fetch a JSON file from a URL",
      inputSchema: fetchInputSchema,
      annotations: { category: "FETCH_URL" },
    },
    async (args) => {
      return await Fetcher.json(args as RequestPayload);
    }
  );

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
