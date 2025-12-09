import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import express from "express";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

export function startSSEServer(server: Server) {
  const app = express();

  // Currently just copying from docs & allowing for multiple transport connections: https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse
  // TODO: If exposed to web, then this will enable any client to connect to the server via http - so marked as UNSAFE until mcp has a proper auth solution.
  let transports: Array<SSEServerTransport> = [];

  app.get("/sse", async (req, res) => {
    const transport = new SSEServerTransport("/messages", res);
    transports.push(transport);
    await server.connect(transport);
  });

  app.post("/messages", (req, res) => {
    const transport = transports.find(
      (t) => t.sessionId === req.query.sessionId
    );

    if (transport) {
      transport.handlePostMessage(req, res);
    } else {
      res
        .status(404)
        .send("Not found. Must pass valid sessionId as query param.");
    }
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
  app.listen(port, host, () => {
    console.log(
      `mcp-kubernetes-server is listening on port ${port}\nUse the following url to connect to the server:\n\http://${host}:${port}/sse`
    );
  });
}
