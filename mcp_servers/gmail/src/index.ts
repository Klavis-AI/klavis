#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { google } from 'googleapis';
import { zodToJsonSchema } from "zod-to-json-schema";
import { AsyncLocalStorage } from 'async_hooks';

// Import schemas and types
import {
    GmailMessagePart,
    EmailAttachment,
    SendEmailSchema,
    ReadEmailSchema,
    SearchEmailsSchema,
    ModifyEmailSchema,
    DeleteEmailSchema,
    SearchContactsSchema,
    GetEmailAttachmentsSchema,
    BatchModifyEmailsSchema,
    BatchDeleteEmailsSchema,
    DIRECTORY_SOURCE_MAP,
} from "./schemas.js";

// Import utilities
import {
    createEmailMessage,
    extractPdfText,
    extractDocxText,
    extractXlsxText,
    base64UrlToBase64,
    extractEmailContent,
    processBatches,
    warmupContactSearch,
    // Error handling
    GmailMCPError,
    GmailErrorType,
    parseGoogleApiError,
    parseZodError,
    formatGmailError,
    addErrorGuidance,
    // Validation
    validateEmailAddresses,
    validateId,
} from "./utils.js";

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    gmailClient: any;
    peopleClient: any;
}>();

// Helper function to get Gmail client from context
function getGmailClient() {
    return asyncLocalStorage.getStore()!.gmailClient;
}

// Helper function to get People client from context
function getPeopleClient() {
    return asyncLocalStorage.getStore()!.peopleClient;
}

function extractAccessToken(req: Request): string {
    let authData = process.env.AUTH_DATA;

    if (!authData && req.headers['x-auth-data']) {
        try {
            authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
        } catch (error) {
            console.error('Error parsing x-auth-data JSON:', error);
        }
    }

    if (!authData) {
        console.error('Error: Gmail access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
        return '';
    }

    const authDataJson = JSON.parse(authData);
    return authDataJson.access_token ?? '';
}

// Get Gmail MCP Server
const getGmailMcpServer = () => {
    // Server implementation
    const server = new Server({
        name: "gmail",
        version: "1.0.0",
    }, {
        capabilities: {
            tools: {},
        },
    });

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            {
                name: "gmail_send_email",
                description: "Sends a new email. You MUST NOT assume the emails unless they are explicitly provided. You may use gmail_search_contacts tool to find contact emails.",
                inputSchema: zodToJsonSchema(SendEmailSchema),
                annotations: { category: "GMAIL_EMAIL" },
            },
            {
                name: "gmail_draft_email",
                description: "Draft a new email",
                inputSchema: zodToJsonSchema(SendEmailSchema),
                annotations: { category: "GMAIL_EMAIL" },
            },
            {
                name: "gmail_read_email",
                description: "Retrieves the content of a specific email and all messages in its thread. Returns a structured list of emails with individual metadata (messageId, subject, from, to, date, body, attachments) for each message in the conversation.",
                inputSchema: zodToJsonSchema(ReadEmailSchema),
                annotations: { category: "GMAIL_EMAIL", readOnlyHint: true },
            },
            {
                name: "gmail_search_emails",
                description: "Searches for emails using Gmail search syntax",
                inputSchema: zodToJsonSchema(SearchEmailsSchema),
                annotations: { category: "GMAIL_EMAIL", readOnlyHint: true },
            },
            {
                name: "gmail_modify_email",
                description: "Modifies email labels (move to different folders)",
                inputSchema: zodToJsonSchema(ModifyEmailSchema),
                annotations: { category: "GMAIL_EMAIL" },
            },
            {
                name: "gmail_delete_email",
                description: "Permanently deletes an email",
                inputSchema: zodToJsonSchema(DeleteEmailSchema),
                annotations: { category: "GMAIL_EMAIL" },
            },
            {
                name: "gmail_batch_modify_emails",
                description: "Modifies labels for multiple emails in batches",
                inputSchema: zodToJsonSchema(BatchModifyEmailsSchema),
                annotations: { category: "GMAIL_BATCH_EMAIL" },
            },
            {
                name: "gmail_batch_delete_emails",
                description: "Permanently deletes multiple emails in batches",
                inputSchema: zodToJsonSchema(BatchDeleteEmailsSchema),
                annotations: { category: "GMAIL_BATCH_EMAIL" },
            },
            {
                name: "gmail_get_email_attachments",
                description: "Returns attachments for an email by message ID. Extracts and returns text for PDFs, Word (.docx), and Excel (.xlsx); returns inline text for text/JSON/XML; returns base64 for images/audio; otherwise returns a data URI reference.",
                inputSchema: zodToJsonSchema(GetEmailAttachmentsSchema),
                annotations: { category: "GMAIL_EMAIL", readOnlyHint: true },
            },
            {
                name: "gmail_search_contacts",
                description: "Search for contacts when you need to know the contact details. Supports searching personal contacts, other contact sources, domain directory, or all sources simultaneously. When contactType is 'all' (default), returns three separate result sets (personal, other, directory) each with independent pagination tokens for flexible paginated access to individual sources.",
                inputSchema: zodToJsonSchema(SearchContactsSchema),
                annotations: { category: "GMAIL_CONTACTS", readOnlyHint: true },
            },
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        const gmail = getGmailClient();

        async function handleEmailAction(action: "send" | "draft", validatedArgs: any) {
            try {
                // Validate inputs before making API calls
                validateEmailAddresses(validatedArgs.to);
                if (validatedArgs.cc) {
                    validateEmailAddresses(validatedArgs.cc);
                }
                if (validatedArgs.bcc) {
                    validateEmailAddresses(validatedArgs.bcc);
                }
                if (validatedArgs.threadId) {
                    validateId(validatedArgs.threadId, 'thread');
                }

                const message = createEmailMessage(validatedArgs);

                const encodedMessage = Buffer.from(message).toString('base64')
                    .replace(/\+/g, '-')
                    .replace(/\//g, '_')
                    .replace(/=+$/, '');

                // Define the type for messageRequest
                interface GmailMessageRequest {
                    raw: string;
                    threadId?: string;
                }

                const messageRequest: GmailMessageRequest = {
                    raw: encodedMessage,
                };

                // Add threadId if specified
                if (validatedArgs.threadId) {
                    messageRequest.threadId = validatedArgs.threadId;
                }

                if (action === "send") {
                    const response = await gmail.users.messages.send({
                        userId: 'me',
                        requestBody: messageRequest,
                    });
                    const resultPayload = {
                        message: `Email sent successfully with ID: ${response.data.id}`,
                        messageId: response.data.id ?? null,
                    };
                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                } else {
                    const response = await gmail.users.drafts.create({
                        userId: 'me',
                        requestBody: {
                            message: messageRequest,
                        },
                    });
                    const resultPayload = {
                        message: `Email draft created successfully with ID: ${response.data.id}`,
                        draftId: response.data.id ?? null,
                    };
                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }
            } catch (error: any) {
                const gmailError = error instanceof GmailMCPError
                    ? error
                    : parseGoogleApiError(error);

                const errorMessage = formatGmailError(
                    gmailError,
                    action === 'send' ? 'send email' : 'create draft'
                );
                const enhanced = addErrorGuidance(errorMessage, gmailError, {
                    operation: action === 'send' ? 'gmail_send_email' : 'gmail_draft_email',
                    suggestions: [
                        'Verify all email addresses are valid',
                        'Check that the access token has Gmail send permissions',
                    ],
                });

                throw new GmailMCPError(gmailError.type, enhanced, {
                    status: gmailError.status,
                    originalError: gmailError.originalError,
                });
            }
        }

        try {

            switch (name) {
                case "gmail_send_email":
                case "gmail_draft_email": {
                    const validatedArgs = SendEmailSchema.parse(args);
                    const action = name === "gmail_send_email" ? "send" : "draft";
                    return await handleEmailAction(action, validatedArgs);
                }

                case "gmail_read_email": {
                    const validatedArgs = ReadEmailSchema.parse(args);
                    const response = await gmail.users.messages.get({
                        userId: 'me',
                        id: validatedArgs.messageId,
                        format: 'full',
                    });

                    const threadId = response.data.threadId || '';

                    // Get all messages in the thread
                    const threadResponse = await gmail.users.threads.get({
                        userId: 'me',
                        id: threadId,
                        format: 'full',
                    });

                    const threadMessages = threadResponse.data.messages || [];

                    // Process each message in the thread
                    const emails = threadMessages.map((msg: any) => {
                        const headers = msg.payload?.headers || [];
                        const subject = headers.find((h: any) => h.name?.toLowerCase() === 'subject')?.value || '';
                        const from = headers.find((h: any) => h.name?.toLowerCase() === 'from')?.value || '';
                        const to = headers.find((h: any) => h.name?.toLowerCase() === 'to')?.value || '';
                        const cc = headers.find((h: any) => h.name?.toLowerCase() === 'cc')?.value || '';
                        const date = headers.find((h: any) => h.name?.toLowerCase() === 'date')?.value || '';
                        const messageId = msg.id || '';

                        // Extract email content using the utility function
                        const { text, html } = extractEmailContent(msg.payload as GmailMessagePart || {});

                        // Get attachment information
                        const attachments: EmailAttachment[] = [];
                        const processAttachmentParts = (part: GmailMessagePart, path: string = '') => {
                            if (part.body && part.body.attachmentId) {
                                const filename = part.filename || `attachment-${part.body.attachmentId}`;
                                attachments.push({
                                    id: part.body.attachmentId,
                                    filename: filename,
                                    mimeType: part.mimeType || 'application/octet-stream',
                                    size: part.body.size || 0
                                });
                            }

                            if (part.parts) {
                                part.parts.forEach((subpart: GmailMessagePart) =>
                                    processAttachmentParts(subpart, `${path}/parts`)
                                );
                            }
                        };

                        if (msg.payload) {
                            processAttachmentParts(msg.payload as GmailMessagePart);
                        }

                        const preferredFormat = text ? 'text/plain' : (html ? 'text/html' : null);

                        return {
                            messageId,
                            subject,
                            from,
                            to,
                            cc: cc || undefined,
                            date,
                            body: {
                                text: text || '',
                                html: html || '',
                                preferredFormat,
                            },
                            attachments: attachments.length > 0 ? attachments : undefined,
                        };
                    });

                    const resultPayload = {
                        threadId,
                        messageCount: emails.length,
                        emails,
                    };

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_search_emails": {
                    const validatedArgs = SearchEmailsSchema.parse(args);
                    const response = await gmail.users.messages.list({
                        userId: 'me',
                        q: validatedArgs.query,
                        maxResults: validatedArgs.maxResults || 10,
                    });

                    const messages = response.data.messages || [];
                    const results = await Promise.all(
                        messages.map(async (msg: any) => {
                            const detail = await gmail.users.messages.get({
                                userId: 'me',
                                id: msg.id!,
                                format: 'metadata',
                                metadataHeaders: ['Subject', 'From', 'Date'],
                            });
                            const headers = detail.data.payload?.headers || [];
                            return {
                                id: msg.id,
                                subject: headers.find((h: any) => h.name === 'Subject')?.value || '',
                                from: headers.find((h: any) => h.name === 'From')?.value || '',
                                date: headers.find((h: any) => h.name === 'Date')?.value || '',
                            };
                        })
                    );

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(results, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_modify_email": {
                    const validatedArgs = ModifyEmailSchema.parse(args);

                    // Prepare request body
                    const requestBody: any = {};

                    if (validatedArgs.addLabelIds) {
                        requestBody.addLabelIds = validatedArgs.addLabelIds;
                    }

                    if (validatedArgs.removeLabelIds) {
                        requestBody.removeLabelIds = validatedArgs.removeLabelIds;
                    }

                    await gmail.users.messages.modify({
                        userId: 'me',
                        id: validatedArgs.messageId,
                        requestBody: requestBody,
                    });
                    const resultPayload: Record<string, unknown> = {
                        message: `Email ${validatedArgs.messageId} labels updated successfully`,
                        messageId: validatedArgs.messageId,
                    };
                    if (validatedArgs.addLabelIds) {
                        resultPayload.addedLabels = validatedArgs.addLabelIds;
                    }
                    if (validatedArgs.removeLabelIds) {
                        resultPayload.removedLabels = validatedArgs.removeLabelIds;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_delete_email": {
                    const validatedArgs = DeleteEmailSchema.parse(args);
                    await gmail.users.messages.delete({
                        userId: 'me',
                        id: validatedArgs.messageId,
                    });
                    const resultPayload = {
                        message: `Email ${validatedArgs.messageId} deleted successfully`,
                        messageId: validatedArgs.messageId,
                    };

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_batch_modify_emails": {
                    const validatedArgs = BatchModifyEmailsSchema.parse(args);
                    const messageIds = validatedArgs.messageIds;
                    const batchSize = validatedArgs.batchSize || 50;

                    // Prepare request body
                    const requestBody: any = {};

                    if (validatedArgs.addLabelIds) {
                        requestBody.addLabelIds = validatedArgs.addLabelIds;
                    }

                    if (validatedArgs.removeLabelIds) {
                        requestBody.removeLabelIds = validatedArgs.removeLabelIds;
                    }

                    // Process messages in batches
                    const { successes, failures } = await processBatches(
                        messageIds,
                        batchSize,
                        async (batch) => {
                            const results = await Promise.all(
                                batch.map(async (messageId) => {
                                    const result = await gmail.users.messages.modify({
                                        userId: 'me',
                                        id: messageId,
                                        requestBody: requestBody,
                                    });
                                    return { messageId, success: true };
                                })
                            );
                            return results;
                        }
                    );

                    // Generate summary of the operation
                    const successCount = successes.length;
                    const failureCount = failures.length;
                    const failureDetails = failures.map(({ item, error }) => ({
                        messageId: typeof item === 'string' ? item : String(item),
                        error: error.message,
                    }));
                    const resultPayload: Record<string, unknown> = {
                        message: "Batch label modification complete.",
                        successCount,
                        failureCount,
                    };
                    if (failureDetails.length > 0) {
                        resultPayload.failures = failureDetails;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_batch_delete_emails": {
                    const validatedArgs = BatchDeleteEmailsSchema.parse(args);
                    const messageIds = validatedArgs.messageIds;
                    const batchSize = validatedArgs.batchSize || 50;

                    // Process messages in batches
                    const { successes, failures } = await processBatches(
                        messageIds,
                        batchSize,
                        async (batch) => {
                            const results = await Promise.all(
                                batch.map(async (messageId) => {
                                    await gmail.users.messages.delete({
                                        userId: 'me',
                                        id: messageId,
                                    });
                                    return { messageId, success: true };
                                })
                            );
                            return results;
                        }
                    );

                    // Generate summary of the operation
                    const successCount = successes.length;
                    const failureCount = failures.length;
                    const failureDetails = failures.map(({ item, error }) => ({
                        messageId: typeof item === 'string' ? item : String(item),
                        error: error.message,
                    }));
                    const resultPayload: Record<string, unknown> = {
                        message: "Batch delete operation complete.",
                        successCount,
                        failureCount,
                    };
                    if (failureDetails.length > 0) {
                        resultPayload.failures = failureDetails;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: JSON.stringify(resultPayload, null, 2),
                            },
                        ],
                    };
                }

                case "gmail_get_email_attachments": {
                    const validatedArgs = GetEmailAttachmentsSchema.parse(args);
                    const messageId = validatedArgs.messageId;

                    // Get the message in full to inspect parts and attachment IDs
                    const messageResponse = await gmail.users.messages.get({
                        userId: 'me',
                        id: messageId,
                        format: 'full',
                    });

                    const attachmentsMeta: Array<{
                        attachmentId: string;
                        filename: string;
                        mimeType: string;
                        size: number;
                    }> = [];

                    const collectAttachments = (part: GmailMessagePart | undefined) => {
                        if (!part) return;
                        if (part.body && part.body.attachmentId) {
                            attachmentsMeta.push({
                                attachmentId: part.body.attachmentId,
                                filename: part.filename || `attachment-${part.body.attachmentId}`,
                                mimeType: part.mimeType || 'application/octet-stream',
                                size: part.body.size || 0,
                            });
                        }
                        if (part.parts && part.parts.length) {
                            part.parts.forEach(collectAttachments);
                        }
                    };

                    collectAttachments(messageResponse.data.payload as GmailMessagePart | undefined);

                    if (attachmentsMeta.length === 0) {
                        const resultPayload = {
                            message: `No attachments found for message ${messageId}`,
                            messageId,
                            attachmentCount: 0,
                        };
                        return {
                            content: [
                                {
                                    type: 'text',
                                    text: JSON.stringify(resultPayload, null, 2),
                                },
                            ],
                        };
                    }

                    // Retrieve each attachment's data and emit real content
                    const attachmentContents = await Promise.all(
                        attachmentsMeta.map(async (meta) => {
                            const att = await gmail.users.messages.attachments.get({
                                userId: 'me',
                                messageId,
                                id: meta.attachmentId,
                            });
                            const base64Url = att.data.data || '';
                            const base64 = base64UrlToBase64(base64Url);

                            const mime = meta.mimeType || 'application/octet-stream';

                            // Handle PDF files using pdfjs-dist
                            if (mime === 'application/pdf' || meta.filename.toLowerCase().endsWith('.pdf')) {
                                const pdfText = await extractPdfText(base64, meta.filename);

                                return {
                                    type: 'text' as const,
                                    text: pdfText,
                                };
                            }

                            // Handle Word DOCX files using mammoth
                            if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || meta.filename.toLowerCase().endsWith('.docx')) {
                                const docxText = await extractDocxText(base64, meta.filename);
                                return {
                                    type: 'text' as const,
                                    text: docxText,
                                };
                            }

                            // Handle Excel XLSX files using exceljs; legacy .xls is not supported
                            if (
                                mime === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                                meta.filename.toLowerCase().endsWith('.xlsx')
                            ) {
                                const xlsxText = await extractXlsxText(base64, meta.filename);
                                return {
                                    type: 'text' as const,
                                    text: xlsxText,
                                };
                            }
                            if (
                                mime === 'application/vnd.ms-excel' ||
                                meta.filename.toLowerCase().endsWith('.xls')
                            ) {
                                return {
                                    type: 'text' as const,
                                    text: `[Info] Attachment ${meta.filename}: legacy .xls format is not supported for text extraction. Please convert to .xlsx and retry.`,
                                };
                            }

                            if (mime.startsWith('text/') ||
                                ['application/json', 'application/xml', 'application/javascript', 'application/typescript'].includes(mime)) {
                                const text = Buffer.from(base64, 'base64').toString('utf8');
                                return {
                                    type: 'text' as const,
                                    text,
                                };
                            }

                            if (mime.startsWith('image/')) {
                                return {
                                    type: 'image' as const,
                                    data: base64,
                                    mimeType: mime,
                                    name: meta.filename,
                                };
                            }

                            if (mime.startsWith('audio/')) {
                                return {
                                    type: 'audio' as const,
                                    data: base64,
                                    mimeType: mime,
                                    name: meta.filename,
                                };
                            }

                            // Fallback for other binaries: return a data URI reference in text
                            const dataUri = `data:${mime};base64,${base64}`;
                            return {
                                type: 'text' as const,
                                text: `Attachment: ${meta.filename} (${mime}, ${meta.size} bytes)\n${dataUri}`,
                            };
                        })
                    );

                    // Optionally prepend a short summary line
                    const summary = {
                        type: 'text' as const,
                        text: JSON.stringify(
                            {
                                message: `Attachments for message ${messageId}`,
                                messageId,
                                attachmentCount: attachmentsMeta.length,
                                attachments: attachmentsMeta,
                            },
                            null,
                            2
                        ),
                    };

                    return {
                        content: [summary, ...attachmentContents],
                    };
                }

                case "gmail_search_contacts": {
                    const validatedArgs = SearchContactsSchema.parse(args);
                    const peopleClient = getPeopleClient();
                    const contactType = validatedArgs.contactType || 'personal';

                    try {
                        let response: any;
                        let results: any[] = [];
                        let typeLabel = '';

                        if (contactType === 'all') {
                            typeLabel = 'contact(s) from all sources';
                            // Send warmup requests for personal and other contacts
                            await Promise.all([
                                warmupContactSearch(peopleClient, 'personal'),
                                warmupContactSearch(peopleClient, 'other'),
                            ]);
                            // Execute all three searches in parallel
                            const [personalRes, otherRes, directoryRes] = await Promise.all([
                                // Personal contacts
                                peopleClient.people.searchContacts({
                                    query: validatedArgs.query,
                                    pageSize: Math.min(validatedArgs.pageSize || 10, 30),
                                    readMask: 'names,emailAddresses,organizations,phoneNumbers,metadata',
                                }),
                                // Other contacts
                                peopleClient.otherContacts.search({
                                    query: validatedArgs.query,
                                    pageSize: Math.min(validatedArgs.pageSize || 10, 30),
                                    readMask: 'emailAddresses,metadata,names,phoneNumbers',
                                }),
                                // Directory contacts
                                peopleClient.people.searchDirectoryPeople({
                                    query: validatedArgs.query,
                                    pageSize: Math.min(validatedArgs.pageSize || 10, 500),
                                    readMask: 'names,emailAddresses,organizations,phoneNumbers,metadata',
                                    sources: ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
                                }),
                            ]);

                            // Process personal results
                            const personalResults = (personalRes.data.results || []).map((result: any) => {
                                const person = result.person || {};
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];
                                const orgs = person.organizations || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    contactType: 'personal',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'other',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'other',
                                    })),
                                    organizations: orgs.map((o: any) => ({
                                        name: o.name,
                                        title: o.title,
                                    })),
                                };
                            });

                            // Process other results
                            const otherResults = (otherRes.data.results || []).map((result: any) => {
                                const person = result.person || {};
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    contactType: 'other',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'other',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'other',
                                    })),
                                    organizations: [],
                                };
                            });

                            // Process directory results
                            const directoryResults = (directoryRes.data.people || []).map((person: any) => {
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];
                                const orgs = person.organizations || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    contactType: 'directory',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'work',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'work',
                                    })),
                                    organizations: orgs.map((o: any) => ({
                                        name: o.name,
                                        title: o.title,
                                    })),
                                };
                            });

                            // Return three independent result sets with pagination info
                            const resultPayload = {
                                message: `Found contacts matching "${validatedArgs.query}" from all sources`,
                                query: validatedArgs.query,
                                contactType: 'all',
                                personal: {
                                    resultCount: personalResults.length,
                                    nextPageToken: (personalRes.data as any).nextPageToken || undefined,
                                    contacts: personalResults,
                                },
                                other: {
                                    resultCount: otherResults.length,
                                    nextPageToken: (otherRes.data as any).nextPageToken || undefined,
                                    contacts: otherResults,
                                },
                                directory: {
                                    resultCount: directoryResults.length,
                                    nextPageToken: (directoryRes.data as any).nextPageToken || undefined,
                                    contacts: directoryResults,
                                },
                            };

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: JSON.stringify(resultPayload, null, 2),
                                    },
                                ],
                            };

                        } else if (contactType === 'personal') {
                            typeLabel = 'personal contact(s)';
                            // Send warmup request before search
                            await warmupContactSearch(peopleClient, 'personal');
                            response = await peopleClient.people.searchContacts({
                                query: validatedArgs.query,
                                pageSize: Math.min(validatedArgs.pageSize || 10, 30),
                                readMask: 'names,emailAddresses,organizations,phoneNumbers,metadata',
                            });

                            results = (response.data.results || []).map((result: any) => {
                                const person = result.person || {};
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];
                                const orgs = person.organizations || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'other',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'other',
                                    })),
                                    organizations: orgs.map((o: any) => ({
                                        name: o.name,
                                        title: o.title,
                                    })),
                                };
                            });
                        } else if (contactType === 'other') {
                            typeLabel = 'other contact(s)';
                            // Send warmup request before search
                            await warmupContactSearch(peopleClient, 'other');
                            response = await peopleClient.otherContacts.search({
                                query: validatedArgs.query,
                                pageSize: Math.min(validatedArgs.pageSize || 10, 30),
                                readMask: 'emailAddresses,metadata,names,phoneNumbers',
                            });

                            results = (response.data.results || []).map((result: any) => {
                                const person = result.person || {};
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'other',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'other',
                                    })),
                                    organizations: [],
                                };
                            });
                        } else if (contactType === 'directory') {
                            typeLabel = 'directory contact(s)';
                            const directorySources = DIRECTORY_SOURCE_MAP[validatedArgs.directorySources || 'UNSPECIFIED'];

                            response = await peopleClient.people.searchDirectoryPeople({
                                query: validatedArgs.query,
                                pageSize: Math.min(validatedArgs.pageSize || 10, 500),
                                readMask: 'names,emailAddresses,organizations,phoneNumbers,metadata',
                                sources: directorySources,
                                pageToken: validatedArgs.pageToken,
                            });

                            results = (response.data.people || []).map((person: any) => {
                                const names = person.names || [];
                                const emails = person.emailAddresses || [];
                                const phones = person.phoneNumbers || [];
                                const orgs = person.organizations || [];

                                return {
                                    resourceName: person.resourceName,
                                    displayName: names.length > 0 ? names[0].displayName : 'Unknown',
                                    firstName: names.length > 0 ? names[0].givenName : '',
                                    lastName: names.length > 0 ? names[0].familyName : '',
                                    emailAddresses: emails.map((e: any) => ({
                                        email: e.value,
                                        type: e.type || 'work',
                                    })),
                                    phoneNumbers: phones.map((p: any) => ({
                                        number: p.value,
                                        type: p.type || 'work',
                                    })),
                                    organizations: orgs.map((o: any) => ({
                                        name: o.name,
                                        title: o.title,
                                    })),
                                };
                            });
                        }

                        const resultPayload = {
                            message: `Found ${results.length} ${typeLabel} matching "${validatedArgs.query}"`,
                            query: validatedArgs.query,
                            contactType: contactType,
                            resultCount: results.length,
                            contacts: results,
                        };

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: JSON.stringify(resultPayload, null, 2),
                                },
                            ],
                        };
                    } catch (error: any) {
                        throw new Error(`Failed to search ${contactType} contacts: ${error.message}`);
                    }
                }

                default:
                    throw new GmailMCPError(
                        GmailErrorType.VALIDATION_ERROR,
                        `Unknown tool: ${name}`
                    );
            }
        } catch (error: any) {
            let gmailError: GmailMCPError;

            if (error instanceof GmailMCPError) {
                gmailError = error;
            } else if (error.name === 'ZodError') {
                gmailError = parseZodError(error);
            } else {
                gmailError = parseGoogleApiError(error);
            }

            console.error(`[${name}] Error:`, {
                type: gmailError.type,
                message: gmailError.message,
                status: gmailError.status,
                timestamp: gmailError.timestamp.toISOString(),
            });

            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            error: gmailError.message,
                            type: gmailError.type,
                            ...(gmailError.status && { httpStatus: gmailError.status }),
                        }, null, 2),
                    },
                ],
            };
        }
    });

    return server;
};

// Create Express App
const app = express();
app.use(express.json());

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', async (req: Request, res: Response) => {
    const accessToken = extractAccessToken(req);

    // Initialize Gmail and People clients with the access token
    const auth = new google.auth.OAuth2();
    auth.setCredentials({ access_token: accessToken });
    const gmailClient = google.gmail({ version: 'v1', auth });
    const peopleClient = google.people({ version: 'v1', auth });

    const server = getGmailMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        await asyncLocalStorage.run({ gmailClient, peopleClient }, async () => {
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

// Map to store SSE transports
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req: Request, res: Response) => {
    const accessToken = extractAccessToken(req);

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

    const server = getGmailMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req: Request, res: Response) => {
    const sessionId = req.query.sessionId as string;
    const accessToken = extractAccessToken(req);

    let transport: SSEServerTransport | undefined;
    transport = sessionId ? transports.get(sessionId) : undefined;
    if (transport) {
        // Initialize Gmail and People clients with the access token
        const auth = new google.auth.OAuth2();
        auth.setCredentials({ access_token: accessToken });
        const gmailClient = google.gmail({ version: 'v1', auth });
        const peopleClient = google.people({ version: 'v1', auth });

        await asyncLocalStorage.run({ gmailClient, peopleClient }, async () => {
            await transport!.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
