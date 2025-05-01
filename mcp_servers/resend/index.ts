#!/usr/bin/env node

import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { z } from 'zod';
import { Resend } from "resend";
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  resendClient: Resend;
}>();

function getResendClient() {
  return asyncLocalStorage.getStore()!.resendClient;
}

const getResendMcpServer = () => {
  // Create server instance
  const server = new McpServer({
    name: "resend-email-service",
    version: "1.0.0",
  });

  server.tool(
    "send-email",
    "Send an email using Resend",
    {
      to: z.string().email().describe("Recipient email address"),
      subject: z.string().describe("Email subject line"),
      text: z.string().describe("Plain text email content"),
      html: z
        .string()
        .optional()
        .describe(
          "HTML email content. When provided, the plain text argument MUST be provided as well."
        ),
      cc: z
        .string()
        .email()
        .array()
        .optional()
        .describe("Optional array of CC email addresses. You MUST ask the user for this parameter. Under no circumstance provide it yourself"),
      bcc: z
        .string()
        .email()
        .array()
        .optional()
        .describe("Optional array of BCC email addresses. You MUST ask the user for this parameter. Under no circumstance provide it yourself"),
      scheduledAt: z
        .string()
        .optional()
        .describe(
          "Optional parameter to schedule the email. This uses natural language. Examples would be 'tomorrow at 10am' or 'in 2 hours' or 'next day at 9am PST' or 'Friday at 3pm ET'."
        ),
      // If sender email address is not provided, the tool requires it as an argument
      from: z
        .string()
        .email()
        .nonempty()
        .describe(
          "Sender email address. You MUST ask the user for this parameter. Under no circumstance provide it yourself"
        ),
      replyTo: z
        .string()
        .email()
        .array()
        .optional()
        .describe(
          "Optional email addresses for the email readers to reply to. You MUST ask the user for this parameter. Under no circumstance provide it yourself"
        ),
    },
    async ({ from, to, subject, text, html, replyTo, scheduledAt, cc, bcc }) => {
      const fromEmailAddress = from;
      const replyToEmailAddresses = replyTo;

      // Type check on from, since "from" is optionally included in the arguments schema
      // This should never happen.
      if (typeof fromEmailAddress !== "string") {
        throw new Error("from argument must be provided.");
      }

      // Similar type check for "reply-to" email addresses.
      if (
        typeof replyToEmailAddresses !== "string" &&
        !Array.isArray(replyToEmailAddresses)
      ) {
        throw new Error("replyTo argument must be provided.");
      }

      console.error(`Debug - Sending email with from: ${fromEmailAddress}`);

      // Explicitly structure the request with all parameters to ensure they're passed correctly
      const emailRequest: {
        to: string;
        subject: string;
        text: string;
        from: string;
        replyTo: string | string[];
        html?: string;
        scheduledAt?: string;
        cc?: string[];
        bcc?: string[];
      } = {
        to,
        subject,
        text,
        from: fromEmailAddress,
        replyTo: replyToEmailAddresses,
      };

      // Add optional parameters conditionally
      if (html) {
        emailRequest.html = html;
      }

      if (scheduledAt) {
        emailRequest.scheduledAt = scheduledAt;
      }

      if (cc) {
        emailRequest.cc = cc;
      }

      if (bcc) {
        emailRequest.bcc = bcc;
      }

      console.error(`Email request: ${JSON.stringify(emailRequest)}`);

      const resend = getResendClient();
      const response = await resend.emails.send(emailRequest);

      if (response.error) {
        throw new Error(
          `Email failed to send: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Email sent successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  return server;
}

const app = express();
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  // Set up cleanup when connection closes
  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
    }
  });

  transports.set(transport.sessionId, transport);

  const server = getResendMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    // Use environment variable for API key if available, otherwise use header
    const apiKey = process.env.RESEND_API_KEY || req.headers['x-auth-token'] as string;
    if (!apiKey) {
      console.error('Error: Resend API key is missing. Provide it via x-auth-token header.');
      const errorResponse = {
        jsonrpc: '2.0' as '2.0',
        error: {
          code: -32001,
          message: 'Unauthorized, Resend API key is missing. Have you set the Resend API key?'
        },
        id: 0
      };
      await transport.send(errorResponse);
      await transport.close();
      res.status(401).end(JSON.stringify({ error: "Unauthorized, Resend API key is missing. Have you set the Resend API key?" }));
      return;
    }

    const resendClient = new Resend(apiKey);

    asyncLocalStorage.run({ resendClient }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(5000, () => {
  console.log('server running on port 5000');
});
