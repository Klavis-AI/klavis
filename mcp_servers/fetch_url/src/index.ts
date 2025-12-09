#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { Fetcher } from "./Fetcher.js";
import { RequestPayload } from "./types.js";
import express, { Request, Response } from "express";
import crypto from "crypto";
import { z } from "zod";

process.on("uncaughtException", (error) => {
  console.error("Uncaught Exception:", error);
  process.exit(1);
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  process.exit(1);
});

const server = new McpServer(
  {
    name: "fetch-url-mcp",
    version: "1.0.0",
  }
);

// Define the input schema for all fetch tools
const fetchInputSchema = {
  url: z.string().describe("URL of the website to fetch"),
  headers: z.record(z.string(), z.string()).optional().describe("Optional headers to include in the request"),
};

// Register fetch_html tool
server.registerTool(
  "fetch_html",
  {
    description: "Fetch a website and return the content as HTML",
    inputSchema: fetchInputSchema,
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
  },
  async (args) => {
    return await Fetcher.json(args as RequestPayload);
  }
);

async function main() {
  const app = express();
  const PORT = process.env.PORT || 5000;

  app.use(express.json());

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => crypto.randomUUID(),
  });

  await server.connect(transport);

  app.post("/mcp", async (req: Request, res: Response) => {
    console.log("MCP connection request received");
    await transport.handleRequest(req, res, req.body);
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
