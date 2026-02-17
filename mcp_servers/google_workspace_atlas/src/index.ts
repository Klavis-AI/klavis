#!/usr/bin/env node
import express, { Request, Response } from "express";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from "googleapis";
import { AsyncLocalStorage } from "async_hooks";

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  gmail: any;
  calendar: any;
}>();

// Helper functions to get clients from context
function getGmail() {
  return asyncLocalStorage.getStore()!.gmail;
}

function getCalendar() {
  return asyncLocalStorage.getStore()!.calendar;
}

const GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token";

interface AuthInfo {
  access_token: string;
  client_id?: string;
  client_secret?: string;
  refresh_token?: string;
}

function extractAuthInfo(req: Request): AuthInfo {
  // First try environment variable
  let authData = process.env.AUTH_DATA;

  // If not in env, try to get from x-auth-data header
  if (!authData) {
    const headerValue = req.headers["x-auth-data"];
    if (headerValue) {
      try {
        // Header value is base64 encoded JSON
        authData = Buffer.from(headerValue as string, "base64").toString("utf8");
      } catch (error) {
        console.error("Error decoding x-auth-data header:", error);
      }
    }
  }

  if (!authData) {
    // No auth data available - this is normal for initialization requests
    return { access_token: "" };
  }

  try {
    // Parse the JSON auth data to extract auth fields
    const authJson = JSON.parse(authData);
    return {
      access_token: authJson.access_token ?? "",
      client_id: authJson.client_id,
      client_secret: authJson.client_secret,
      refresh_token: authJson.refresh_token,
    };
  } catch (error) {
    console.error("Failed to parse auth data JSON:", authData);
    return { access_token: "" };
  }
}

// Get Google Workspace MCP Server
const getGoogleWorkspaceMcpServer = () => {
  const server = new Server(
    {
      name: "google-workspace-server",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Error handling
  server.onerror = (error) => console.error("[MCP Error]", error);

  // Setup tool handlers
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: "list_emails",
        description: "List recent emails from Gmail inbox",
        inputSchema: {
          type: "object",
          properties: {
            maxResults: {
              type: "number",
              description: "Maximum number of emails to return (default: 10)",
            },
            query: {
              type: "string",
              description: "Search query to filter emails",
            },
          },
        },
      },
      {
        name: "search_emails",
        description: "Search emails with advanced query",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description:
                'Gmail search query (e.g., "from:example@gmail.com has:attachment"). Examples:\n' +
                '- "from:alice@example.com" (Emails from Alice)\n' +
                '- "to:bob@example.com" (Emails sent to Bob)\n' +
                '- "subject:Meeting Update" (Emails with "Meeting Update" in the subject)\n' +
                '- "has:attachment filename:pdf" (Emails with PDF attachments)\n' +
                '- "after:2024/01/01 before:2024/02/01" (Emails between specific dates)\n' +
                '- "is:unread" (Unread emails)\n' +
                '- "from:@company.com has:attachment" (Emails from a company domain with attachments)',
            },
            maxResults: {
              type: "number",
              description: "Maximum number of emails to return (default: 10)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "send_email",
        description: "Send a new email",
        inputSchema: {
          type: "object",
          properties: {
            to: {
              type: "string",
              description: "Recipient email address",
            },
            subject: {
              type: "string",
              description: "Email subject",
            },
            body: {
              type: "string",
              description: "Email body (can include HTML)",
            },
            cc: {
              type: "string",
              description: "CC recipients (comma-separated)",
            },
            bcc: {
              type: "string",
              description: "BCC recipients (comma-separated)",
            },
          },
          required: ["to", "subject", "body"],
        },
      },
      {
        name: "modify_email",
        description: "Modify email labels (archive, trash, mark read/unread)",
        inputSchema: {
          type: "object",
          properties: {
            id: {
              type: "string",
              description: "Email ID",
            },
            addLabels: {
              type: "array",
              items: { type: "string" },
              description: "Labels to add",
            },
            removeLabels: {
              type: "array",
              items: { type: "string" },
              description: "Labels to remove",
            },
          },
          required: ["id"],
        },
      },
      {
        name: "list_events",
        description: "List upcoming calendar events",
        inputSchema: {
          type: "object",
          properties: {
            maxResults: {
              type: "number",
              description: "Maximum number of events to return (default: 10)",
            },
            timeMin: {
              type: "string",
              description: "Start time in ISO format (default: now)",
            },
            timeMax: {
              type: "string",
              description: "End time in ISO format",
            },
          },
        },
      },
      {
        name: "create_event",
        description: "Create a new calendar event",
        inputSchema: {
          type: "object",
          properties: {
            summary: {
              type: "string",
              description: "Event title",
            },
            location: {
              type: "string",
              description: "Event location",
            },
            description: {
              type: "string",
              description: "Event description",
            },
            start: {
              type: "string",
              description: "Start time in ISO format",
            },
            end: {
              type: "string",
              description: "End time in ISO format",
            },
            attendees: {
              type: "array",
              items: { type: "string" },
              description: "List of attendee email addresses",
            },
          },
          required: ["summary", "start", "end"],
        },
      },
      {
        name: "update_event",
        description: "Update an existing calendar event",
        inputSchema: {
          type: "object",
          properties: {
            eventId: {
              type: "string",
              description: "Event ID to update",
            },
            summary: {
              type: "string",
              description: "New event title",
            },
            location: {
              type: "string",
              description: "New event location",
            },
            description: {
              type: "string",
              description: "New event description",
            },
            start: {
              type: "string",
              description: "New start time in ISO format",
            },
            end: {
              type: "string",
              description: "New end time in ISO format",
            },
            attendees: {
              type: "array",
              items: { type: "string" },
              description: "New list of attendee email addresses",
            },
          },
          required: ["eventId"],
        },
      },
      {
        name: "delete_event",
        description: "Delete a calendar event",
        inputSchema: {
          type: "object",
          properties: {
            eventId: {
              type: "string",
              description: "Event ID to delete",
            },
          },
          required: ["eventId"],
        },
      },
    ],
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const gmail = getGmail();
    const calendar = getCalendar();

    switch (request.params.name) {
      case "list_emails":
        return await handleListEmails(gmail, request.params.arguments);
      case "search_emails":
        return await handleSearchEmails(gmail, request.params.arguments);
      case "send_email":
        return await handleSendEmail(gmail, request.params.arguments);
      case "modify_email":
        return await handleModifyEmail(gmail, request.params.arguments);
      case "list_events":
        return await handleListEvents(calendar, request.params.arguments);
      case "create_event":
        return await handleCreateEvent(calendar, request.params.arguments);
      case "update_event":
        return await handleUpdateEvent(calendar, request.params.arguments);
      case "delete_event":
        return await handleDeleteEvent(calendar, request.params.arguments);
      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${request.params.name}`
        );
    }
  });

  return server;
};

async function handleListEmails(gmail: any, args: any) {
  try {
    const maxResults = args?.maxResults || 10;
    const query = args?.query || "";
    const getEmailBody = (payload: any): string => {
      if (!payload) return "";

      if (payload.body && payload.body.data) {
        return Buffer.from(payload.body.data, "base64").toString("utf-8");
      }

      if (payload.parts && payload.parts.length > 0) {
        for (const part of payload.parts) {
          if (part.mimeType === "text/plain") {
            return Buffer.from(part.body.data, "base64").toString("utf-8");
          }
        }
      }

      return "(No body content)";
    };

    const response = await gmail.users.messages.list({
      userId: "me",
      maxResults,
      q: query,
    });

    const messages = response.data.messages || [];
    const emailDetails = await Promise.all(
      messages.map(async (msg: any) => {
        const detail = await gmail.users.messages.get({
          userId: "me",
          id: msg.id!,
        });

        const headers = detail.data.payload?.headers;
        const subject =
          headers?.find((h: any) => h.name === "Subject")?.value || "";
        const from = headers?.find((h: any) => h.name === "From")?.value || "";
        const date = headers?.find((h: any) => h.name === "Date")?.value || "";
        const body = getEmailBody(detail.data.payload);

        return {
          id: msg.id,
          subject,
          from,
          date,
          body,
        };
      })
    );

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(emailDetails, null, 2),
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error fetching emails: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleSearchEmails(gmail: any, args: any) {
  try {
    const maxResults = args?.maxResults || 10;
    const query = args?.query || "";

    const getEmailBody = (payload: any): string => {
      if (!payload) return "";

      if (payload.body && payload.body.data) {
        return Buffer.from(payload.body.data, "base64").toString("utf-8");
      }

      if (payload.parts && payload.parts.length > 0) {
        for (const part of payload.parts) {
          if (part.mimeType === "text/plain") {
            return Buffer.from(part.body.data, "base64").toString("utf-8");
          }
        }
      }

      return "(No body content)";
    };

    const response = await gmail.users.messages.list({
      userId: "me",
      maxResults,
      q: query,
    });

    const messages = response.data.messages || [];
    const emailDetails = await Promise.all(
      messages.map(async (msg: any) => {
        const detail = await gmail.users.messages.get({
          userId: "me",
          id: msg.id!,
        });

        const headers = detail.data.payload?.headers;
        const subject =
          headers?.find((h: any) => h.name === "Subject")?.value || "";
        const from = headers?.find((h: any) => h.name === "From")?.value || "";
        const date = headers?.find((h: any) => h.name === "Date")?.value || "";
        const body = getEmailBody(detail.data.payload);

        return {
          id: msg.id,
          subject,
          from,
          date,
          body,
          labels: detail.data.labelIds || [],
        };
      })
    );

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(emailDetails, null, 2),
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error fetching emails: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleSendEmail(gmail: any, args: any) {
  try {
    const { to, subject, body, cc, bcc } = args;

    const headers = [
      'Content-Type: text/plain; charset="UTF-8"',
      "MIME-Version: 1.0",
      `To: ${to}`,
      cc ? `Cc: ${cc}` : null,
      bcc ? `Bcc: ${bcc}` : null,
      `Subject: ${subject}`,
    ]
      .filter(Boolean)
      .join("\r\n");

    // Ensure proper separation between headers and body
    const email = `${headers}\r\n\r\n${body}`;

    // Encode in base64url
    const encodedMessage = Buffer.from(email)
      .toString("base64")
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

    // Send the email
    const response = await gmail.users.messages.send({
      userId: "me",
      requestBody: {
        raw: encodedMessage,
      },
    });

    return {
      content: [
        {
          type: "text",
          text: `Email sent successfully. Message ID: ${response.data.id}`,
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error sending email: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleModifyEmail(gmail: any, args: any) {
  try {
    const { id, addLabels = [], removeLabels = [] } = args;

    const response = await gmail.users.messages.modify({
      userId: "me",
      id,
      requestBody: {
        addLabelIds: addLabels,
        removeLabelIds: removeLabels,
      },
    });

    return {
      content: [
        {
          type: "text",
          text: `Email modified successfully. Updated labels for message ID: ${response.data.id}`,
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error modifying email: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleCreateEvent(calendar: any, args: any) {
  try {
    const {
      summary,
      location,
      description,
      start,
      end,
      attendees = [],
    } = args;

    const event = {
      summary,
      location,
      description,
      start: {
        dateTime: start,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      end: {
        dateTime: end,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      attendees: attendees.map((email: string) => ({ email })),
    };

    const response = await calendar.events.insert({
      calendarId: "primary",
      requestBody: event,
    });

    return {
      content: [
        {
          type: "text",
          text: `Event created successfully. Event ID: ${response.data.id}`,
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error creating event: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleUpdateEvent(calendar: any, args: any) {
  try {
    const { eventId, summary, location, description, start, end, attendees } =
      args;

    const event: any = {};
    if (summary) event.summary = summary;
    if (location) event.location = location;
    if (description) event.description = description;
    if (start) {
      event.start = {
        dateTime: start,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      };
    }
    if (end) {
      event.end = {
        dateTime: end,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      };
    }
    if (attendees) {
      event.attendees = attendees.map((email: string) => ({ email }));
    }

    const response = await calendar.events.patch({
      calendarId: "primary",
      eventId,
      requestBody: event,
    });

    return {
      content: [
        {
          type: "text",
          text: `Event updated successfully. Event ID: ${response.data.id}`,
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error updating event: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleDeleteEvent(calendar: any, args: any) {
  try {
    const { eventId } = args;

    await calendar.events.delete({
      calendarId: "primary",
      eventId,
    });

    return {
      content: [
        {
          type: "text",
          text: `Event deleted successfully. Event ID: ${eventId}`,
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error deleting event: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

async function handleListEvents(calendar: any, args: any) {
  try {
    const maxResults = args?.maxResults || 10;
    const timeMin = args?.timeMin || new Date().toISOString();
    const timeMax = args?.timeMax;

    const response = await calendar.events.list({
      calendarId: "primary",
      timeMin,
      timeMax,
      maxResults,
      singleEvents: true,
      orderBy: "startTime",
    });

    const events = response.data.items?.map((event: any) => ({
      id: event.id,
      summary: event.summary,
      start: event.start,
      end: event.end,
      location: event.location,
    }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(events, null, 2),
        },
      ],
    };
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error fetching calendar events: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
}

// Create Express App
const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post("/mcp", async (req: Request, res: Response) => {
  const authInfo = extractAuthInfo(req);

  // Initialize Gmail and Calendar clients with the access token and refresh credentials
  const auth = new google.auth.OAuth2(authInfo.client_id, authInfo.client_secret);
  auth.setCredentials({
    access_token: authInfo.access_token,
    refresh_token: authInfo.refresh_token,
    token_type: "Bearer",
  });
  const gmailClient = google.gmail({ version: "v1", auth });
  const calendarClient = google.calendar({ version: "v3", auth });

  const server = getGoogleWorkspaceMcpServer();
  try {
    const transport: StreamableHTTPServerTransport =
      new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
      });
    await server.connect(transport);
    asyncLocalStorage.run({ gmail: gmailClient, calendar: calendarClient }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
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

app.delete("/mcp", async (req: Request, res: Response) => {
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

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Google Workspace MCP server running on port ${PORT}`);
});
