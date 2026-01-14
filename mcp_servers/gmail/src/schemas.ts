import { z } from "zod";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface GmailMessagePart {
    partId?: string;
    mimeType?: string;
    filename?: string;
    headers?: Array<{
        name: string;
        value: string;
    }>;
    body?: {
        attachmentId?: string;
        size?: number;
        data?: string;
    };
    parts?: GmailMessagePart[];
}

export interface EmailAttachment {
    id: string;
    filename: string;
    mimeType: string;
    size: number;
}

export interface EmailContent {
    text: string;
    html: string;
}

// ============================================================================
// ZOD SCHEMAS
// ============================================================================

export const SendEmailSchema = z.object({
    to: z.array(z.string()).describe("List of recipient email addresses. You MUST NOT assume the emails unless they are explicitly provided. You may use gmail_search_contacts tool to find contact emails."),
    subject: z.string().describe("Email subject"),
    body: z.string().describe("Email body content (used for text/plain or when htmlBody not provided)"),
    htmlBody: z.string().optional().describe("HTML version of the email body"),
    mimeType: z.enum(['text/plain', 'text/html', 'multipart/alternative']).optional().default('text/plain').describe("Email content type"),
    cc: z.array(z.string()).optional().describe("List of CC recipients. You MUST NOT assume the emails unless they are explicitly provided. You may use gmail_search_contacts tool to find contact emails."),
    bcc: z.array(z.string()).optional().describe("List of BCC recipients. You MUST NOT assume the emails unless they are explicitly provided. You may use gmail_search_contacts tool to find contact emails."),
    threadId: z.string().optional().describe("Thread ID to reply to"),
    inReplyTo: z.string().optional().describe("Message ID being replied to"),
});

export const ReadEmailSchema = z.object({
    messageId: z.string().describe("ID of the email message to retrieve"),
});

export const SearchEmailsSchema = z.object({
    query: z.string().describe("Gmail search query (e.g., 'from:example@gmail.com')"),
    maxResults: z.number().optional().describe("Maximum number of results to return"),
});

export const ModifyEmailSchema = z.object({
    messageId: z.string().describe("ID of the email message to modify"),
    addLabelIds: z.array(z.string()).optional().describe("List of label IDs to add to the message"),
    removeLabelIds: z.array(z.string()).optional().describe("List of label IDs to remove from the message"),
});

export const DeleteEmailSchema = z.object({
    messageId: z.string().describe("ID of the email message to delete"),
});

export const SearchContactsSchema = z.object({
    query: z.string().describe("The plain-text search query for contact names, email addresses, phone numbers, etc."),
    contactType: z.enum(['all', 'personal', 'other', 'directory']).optional().default('all').describe("Type of contacts to search: 'all' (search all types - returns three separate result sets with independent pagination tokens), 'personal' (your saved contacts), 'other' (other contact sources like Gmail suggestions), or 'directory' (domain directory)"),
    pageSize: z.number().optional().default(10).describe("Number of results to return. For personal/other: max 30, for directory: max 500"),
    pageToken: z.string().optional().describe("Page token for pagination (used with directory searches)"),
    directorySources: z.enum(['UNSPECIFIED', 'DOMAIN_DIRECTORY', 'DOMAIN_CONTACTS']).optional().default('UNSPECIFIED').describe("Directory sources to search (only used for directory type)")
});

export const GetEmailAttachmentsSchema = z.object({
    messageId: z.string().describe("ID of the email message to retrieve attachments for"),
});

export const BatchModifyEmailsSchema = z.object({
    messageIds: z.array(z.string()).describe("List of message IDs to modify"),
    addLabelIds: z.array(z.string()).optional().describe("List of label IDs to add to all messages"),
    removeLabelIds: z.array(z.string()).optional().describe("List of label IDs to remove from all messages"),
    batchSize: z.number().optional().default(50).describe("Number of messages to process in each batch (default: 50)"),
});

export const BatchDeleteEmailsSchema = z.object({
    messageIds: z.array(z.string()).describe("List of message IDs to delete"),
    batchSize: z.number().optional().default(50).describe("Number of messages to process in each batch (default: 50)"),
});

// ============================================================================
// CONSTANTS
// ============================================================================

export const SYSTEM_LABEL_IDS = [
    'INBOX',
    'SENT',
    'DRAFT',
    'SPAM',
    'TRASH',
    'UNREAD',
    'STARRED',
    'IMPORTANT',
    'CHAT',
    'CATEGORY_PERSONAL',
    'CATEGORY_SOCIAL',
    'CATEGORY_PROMOTIONS',
    'CATEGORY_UPDATES',
    'CATEGORY_FORUMS'
];

export const DIRECTORY_SOURCE_MAP: Record<string, string[]> = {
    'UNSPECIFIED': ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE', 'DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
    'DOMAIN_DIRECTORY': ['DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE'],
    'DOMAIN_CONTACTS': ['DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT'],
};
