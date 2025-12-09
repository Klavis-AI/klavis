import express from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import http from "http";

export function startStreamableHTTPServer(server: Server): http.Server {
  const app = express();
  app.use(express.json());

  app.post("/mcp", async (req: express.Request, res: express.Response) => {
    // In stateless mode, create a new instance of transport and server for each request
    // to ensure complete isolation. A single instance would cause request ID collisions
    // when multiple clients connect concurrently.

    try {
      // DNS rebinding protection is disabled by default for backwards compatibility. If you are running this server
      // locally, make sure to set DNS_REBINDING_PROTECTION=true
      const enableDnsRebindingProtection =
        process.env.DNS_REBINDING_PROTECTION === "true";
      const allowedHosts = process.env.DNS_REBINDING_ALLOWED_HOST
        ? [process.env.DNS_REBINDING_ALLOWED_HOST]
        : ["127.0.0.1"];

      const transport: StreamableHTTPServerTransport =
        new StreamableHTTPServerTransport({
          sessionIdGenerator: undefined,
          enableDnsRebindingProtection,
          allowedHosts,
        });
      res.on("close", () => {
        transport.close();
        // Note: server.close() should NOT be called here as server is shared
        // across all requests. Calling it would close the global MCP Server
        // instance and cause the Node.js process to exit. Only the transport
        // instance needs to be closed when the HTTP connection ends.
      });
      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
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

  // SSE notifications not supported in stateless mode
  app.get("/mcp", async (req: express.Request, res: express.Response) => {
    console.log("Received GET MCP request");
    res.writeHead(405).end(
      JSON.stringify({
        jsonrpc: "2.0",
        error: {
          code: -32000,
          message: "Method not allowed.",
        },
        id: null,
      })
    );
  });

  // Session termination not needed in stateless mode
  app.delete("/mcp", async (req: express.Request, res: express.Response) => {
    console.log("Received DELETE MCP request");
    res.writeHead(405).end(
      JSON.stringify({
        jsonrpc: "2.0",
        error: {
          code: -32000,
          message: "Method not allowed.",
        },
        id: null,
      })
    );
  });

  app.get("/health", async (req: express.Request, res: express.Response) => {
    res.json({ status: "ok" });
  });

  app.get("/ready", async (req: express.Request, res: express.Response) => {
    try {
      // We can add more checks if required
      // For now, we'll consider the server ready if it can respond to this request
      res.json({
        status: "ready",
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Readiness check failed:", error);
      res.status(503).json({
        status: "not ready",
        reason: "Server initialization incomplete",
        timestamp: new Date().toISOString()
      });
    }
  });

  let port = 3000;
  try {
    port = parseInt(process.env.PORT || "3000", 10);
  } catch (e) {
    console.error(
      "Invalid PORT environment variable, using default port 3000."
    );
  }

  const host = process.env.HOST || "localhost";
  const httpServer = app.listen(port, host, () => {
    console.log(
      `mcp-kubernetes-server is listening on port ${port}\nUse the following url to connect to the server:\nhttp://${host}:${port}/mcp`
    );
  });
  return httpServer;
}
