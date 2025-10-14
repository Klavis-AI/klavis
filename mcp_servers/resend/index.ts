#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';
import { Resend } from "resend";
import { AsyncLocalStorage } from 'async_hooks';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
  apiKey: string;
}>();

function getResendClient() {
  const store = asyncLocalStorage.getStore();
  if (!store) {
    throw new Error('API key not found in AsyncLocalStorage');
  }
  return new Resend(store.apiKey);
}

const getResendMcpServer = () => {
  // Create server instance
  const server = new McpServer({
    name: "resend-email-service",
    version: "1.0.0",
  });

  server.tool(
    "resend_send_email",
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
    { category: "RESEND_EMAIL" },
    async ({ from, to, subject, text, html, replyTo, scheduledAt, cc, bcc }) => {
      const fromEmailAddress = from;
      const replyToEmailAddresses = replyTo;

      // Type check on from, since "from" is optionally included in the arguments schema
      // This should never happen.
      if (typeof fromEmailAddress !== "string") {
        throw new Error("from argument must be provided.");
      }

      console.error(`Debug - Sending email with from: ${fromEmailAddress}`);

      // Explicitly structure the request with all parameters to ensure they're passed correctly
      const emailRequest: {
        to: string;
        subject: string;
        text: string;
        from: string;
        replyTo?: string | string[];
        html?: string;
        scheduledAt?: string;
        cc?: string[];
        bcc?: string[];
      } = {
        to,
        subject,
        text,
        from: fromEmailAddress,
      };

      // Add optional parameters conditionally
      if (replyToEmailAddresses) {
        emailRequest.replyTo = replyToEmailAddresses;
      }

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

  server.tool(
    "resend_create_audience",
    "Create a new audience in Resend",
    {
      name: z.string().describe("Name of the audience to create"),
    },
    { category: "RESEND_AUDIENCE" },
    async ({ name }) => {
      const resend = getResendClient();
      const response = await resend.audiences.create({ name });

      if (response.error) {
        throw new Error(
          `Failed to create audience: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Audience created successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_get_audience",
    "Retrieve audience details by ID in Resend",
    {
      id: z.string().describe("ID of the audience to retrieve"),
    },
    { category: "RESEND_AUDIENCE", readOnlyHint: true },
    async ({ id }) => {
      const resend = getResendClient();
      const response = await resend.audiences.get(id);

      if (response.error) {
        throw new Error(
          `Failed to retrieve audience: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Audience retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_delete_audience",
    "Delete an audience by ID in Resend",
    {
      id: z.string().describe("ID of the audience to delete"),
    },
    { category: "RESEND_AUDIENCE" },
    async ({ id }) => {
      const resend = getResendClient();
      const response = await resend.audiences.remove(id);

      if (response.error) {
        throw new Error(
          `Failed to delete audience: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Audience deleted successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_list_audiences",
    "List all audiences in Resend",
    {},
    { category: "RESEND_AUDIENCE", readOnlyHint: true },
    async () => {
      const resend = getResendClient();
      const response = await resend.audiences.list();

      if (response.error) {
        throw new Error(
          `Failed to list audiences: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Audiences retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_create_contact",
    "Create a new contact in a Resend audience",
    {
      email: z.string().email().describe("Email address of the contact"),
      audienceId: z.string().describe("ID of the audience to add the contact to"),
      firstName: z.string().optional().describe("First name of the contact"),
      lastName: z.string().optional().describe("Last name of the contact"),
      unsubscribed: z.boolean().optional().describe("Whether the contact is unsubscribed"),
    },
    { category: "RESEND_CONTACT" },
    async ({ email, audienceId, firstName, lastName, unsubscribed }) => {
      const resend = getResendClient();
      const response = await resend.contacts.create({
        email,
        audienceId,
        firstName,
        lastName,
        unsubscribed,
      });

      if (response.error) {
        throw new Error(
          `Failed to create contact: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Contact created successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_get_contact",
    "Retrieve a contact from a Resend audience by ID or email",
    {
      audienceId: z.string().describe("ID of the audience the contact belongs to"),
      id: z.string().optional().describe("ID of the contact to retrieve"),
      email: z.string().email().optional().describe("Email of the contact to retrieve"),
    },
    { category: "RESEND_CONTACT", readOnlyHint: true },
    async ({ audienceId, id, email }) => {
      if (!id && !email) {
        throw new Error("Either contact ID or email must be provided");
      }

      const resend = getResendClient();
      let response: any = null;

      if (id) {
        // Lookup by ID
        response = await resend.contacts.get({
          id,
          audienceId,
        });
      } else if (email) {
        // Based on the provided examples, we need to use different method or params for email lookup
        // Let's try to find the contact by email in the list
        const listResponse = await resend.contacts.list({ audienceId });

        if (listResponse.error) {
          throw new Error(`Failed to list contacts: ${JSON.stringify(listResponse.error)}`);
        }

        const contactData = listResponse.data?.data?.find(contact => contact.email === email);

        if (!contactData) {
          throw new Error(`Contact with email ${email} not found`);
        }

        // Now get the full contact details by ID
        response = await resend.contacts.get({
          id: contactData.id,
          audienceId,
        });
      }

      if (!response) {
        throw new Error("Failed to retrieve contact");
      }

      if (response.error) {
        throw new Error(
          `Failed to retrieve contact: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Contact retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_update_contact",
    "Update a contact in a Resend audience by ID or email",
    {
      audienceId: z.string().describe("ID of the audience the contact belongs to"),
      id: z.string().optional().describe("ID of the contact to update"),
      email: z.string().email().optional().describe("Email of the contact to update"),
      firstName: z.string().optional().describe("Updated first name"),
      lastName: z.string().optional().describe("Updated last name"),
      unsubscribed: z.boolean().optional().describe("Updated unsubscribed status"),
    },
    { category: "RESEND_CONTACT" },
    async ({ audienceId, id, email, firstName, lastName, unsubscribed }) => {
      if (!id && !email) {
        throw new Error("Either contact ID or email must be provided");
      }

      const resend = getResendClient();
      let response: any = null;

      // Prepare update data
      const updateData: any = {
        audienceId,
        ...(firstName !== undefined ? { firstName } : {}),
        ...(lastName !== undefined ? { lastName } : {}),
        ...(unsubscribed !== undefined ? { unsubscribed } : {})
      };

      if (id) {
        // Update by ID
        updateData.id = id;
        response = await resend.contacts.update(updateData);
      } else if (email) {
        // First check if we need to find the ID for this email
        const listResponse = await resend.contacts.list({ audienceId });

        if (listResponse.error) {
          throw new Error(`Failed to list contacts: ${JSON.stringify(listResponse.error)}`);
        }

        const contactData = listResponse.data?.data?.find(contact => contact.email === email);

        if (!contactData) {
          throw new Error(`Contact with email ${email} not found`);
        }

        // Now update using the ID
        updateData.id = contactData.id;
        response = await resend.contacts.update(updateData);
      }

      if (!response) {
        throw new Error("Failed to update contact");
      }

      if (response.error) {
        throw new Error(
          `Failed to update contact: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Contact updated successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_delete_contact",
    "Delete a contact from a Resend audience by ID or email",
    {
      audienceId: z.string().describe("ID of the audience the contact belongs to"),
      id: z.string().optional().describe("ID of the contact to delete"),
      email: z.string().email().optional().describe("Email of the contact to delete"),
    },
    { category: "RESEND_CONTACT" },
    async ({ audienceId, id, email }) => {
      if (!id && !email) {
        throw new Error("Either contact ID or email must be provided");
      }

      const resend = getResendClient();
      let response: any = null;

      if (id) {
        // Delete by ID
        response = await resend.contacts.remove({
          id,
          audienceId,
        });
      } else if (email) {
        // First check if we need to find the ID for this email
        const listResponse = await resend.contacts.list({ audienceId });

        if (listResponse.error) {
          throw new Error(`Failed to list contacts: ${JSON.stringify(listResponse.error)}`);
        }

        const contactData = listResponse.data?.data?.find(contact => contact.email === email);

        if (!contactData) {
          throw new Error(`Contact with email ${email} not found`);
        }

        // Now delete using the ID
        response = await resend.contacts.remove({
          id: contactData.id,
          audienceId,
        });
      }

      if (!response) {
        throw new Error("Failed to delete contact");
      }

      if (response.error) {
        throw new Error(
          `Failed to delete contact: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Contact deleted successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_list_contacts",
    "List all contacts in a Resend audience",
    {
      audienceId: z.string().describe("ID of the audience to list contacts from"),
    },
    { category: "RESEND_CONTACT", readOnlyHint: true },
    async ({ audienceId }) => {
      const resend = getResendClient();
      const response = await resend.contacts.list({
        audienceId,
      });

      if (response.error) {
        throw new Error(
          `Failed to list contacts: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Contacts retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_create_broadcast",
    "Create a new broadcast in Resend",
    {
      audienceId: z.string().describe("ID of the audience to send the broadcast to"),
      from: z.string().describe("Sender email and name in the format 'Name <email@domain.com>'"),
      subject: z.string().describe("Subject line of the broadcast"),
      html: z.string().describe("HTML content of the broadcast. Can include variables like {{{FIRST_NAME|there}}} and {{{RESEND_UNSUBSCRIBE_URL}}}"),
      name: z.string().optional().describe("Optional name for the broadcast"),
      replyTo: z.string().optional().describe("Optional reply-to email address"),
      previewText: z.string().optional().describe("Optional preview text that appears in email clients"),
    },
    { category: "RESEND_BROADCAST" },
    async ({ audienceId, from, subject, html, name, replyTo, previewText }) => {
      const resend = getResendClient();
      const response = await resend.broadcasts.create({
        audienceId,
        from,
        subject,
        html,
        ...(name && { name }),
        ...(replyTo && { replyTo }),
        ...(previewText && { previewText }),
      });

      if (response.error) {
        throw new Error(
          `Failed to create broadcast: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Broadcast created successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_get_broadcast",
    "Retrieve a broadcast by ID from Resend",
    {
      id: z.string().describe("ID of the broadcast to retrieve"),
    },
    { category: "RESEND_BROADCAST", readOnlyHint: true },
    async ({ id }) => {
      const resend = getResendClient();
      const response = await resend.broadcasts.get(id);

      if (response.error) {
        throw new Error(
          `Failed to retrieve broadcast: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Broadcast retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_send_broadcast",
    "Send or schedule a broadcast in Resend",
    {
      id: z.string().describe("ID of the broadcast to send"),
      scheduledAt: z.string().optional().describe("Optional scheduling time in natural language (e.g., 'in 1 hour', 'tomorrow at 9am')"),
    },
    { category: "RESEND_BROADCAST" },
    async ({ id, scheduledAt }) => {
      const resend = getResendClient();

      const sendOptions: any = {};
      if (scheduledAt) sendOptions.scheduledAt = scheduledAt;

      const response = await resend.broadcasts.send(id, sendOptions);

      if (response.error) {
        throw new Error(
          `Failed to send broadcast: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Broadcast ${scheduledAt ? 'scheduled' : 'sent'} successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_delete_broadcast",
    "Delete a broadcast by ID in Resend",
    {
      id: z.string().describe("ID of the broadcast to delete"),
    },
    { category: "RESEND_BROADCAST" },
    async ({ id }) => {
      const resend = getResendClient();
      const response = await resend.broadcasts.remove(id);

      if (response.error) {
        throw new Error(
          `Failed to delete broadcast: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Broadcast deleted successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  server.tool(
    "resend_list_broadcasts",
    "List all broadcasts in Resend",
    {},
    { category: "RESEND_BROADCAST", readOnlyHint: true },
    async () => {
      const resend = getResendClient();
      const response = await resend.broadcasts.list();

      if (response.error) {
        throw new Error(
          `Failed to list broadcasts: ${JSON.stringify(response.error)}`
        );
      }

      return {
        content: [
          {
            type: "text",
            text: `Broadcasts retrieved successfully! ${JSON.stringify(response.data)}`,
          },
        ],
      };
    }
  );

  return server;
}

function extractApiKey(req: Request): string {
  let authData = process.env.API_KEY;

  if (authData) {
    return authData;
  }
  
  if (!authData && req.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data JSON:', error);
    }
  }

  if (!authData) {
    console.error('Error: Resend API key is missing. Provide it via API_KEY env var or x-auth-data header with token field.');
    return '';
  }

  const authDataJson = JSON.parse(authData);
  return authDataJson.token ?? authDataJson.api_key ?? '';
}

const app = express();


//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
  const apiKey = extractApiKey(req);

  const server = getResendMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ apiKey }, async () => {
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
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================
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
    const apiKey = extractApiKey(req);

    asyncLocalStorage.run({ apiKey }, async () => {
      await transport!.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(5000, () => {
  console.log('server running on port 5000');
});
