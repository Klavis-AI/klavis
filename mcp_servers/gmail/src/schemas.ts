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

export const AdvancedSearchEmailsSchema = z.object({
    from: z.string().optional().describe("Filter by sender email address"),
    to: z.string().optional().describe("Filter by recipient email address"),
    subject: z.string().optional().describe("Filter by email subject (partial match)"),
    hasAttachment: z.boolean().optional().describe("Filter emails with attachments (true) or without (false)"),
    after: z.string().optional().describe("Filter emails after this date (YYYY/MM/DD format or relative like '7d' for 7 days ago)"),
    before: z.string().optional().describe("Filter emails before this date (YYYY/MM/DD format)"),
    isUnread: z.boolean().optional().describe("Filter unread emails (true) or read emails (false)"),
    hasLabel: z.string().optional().describe("Filter by label name (e.g., 'Important', 'Work')"),
    excludeLabel: z.string().optional().describe("Exclude emails with this label"),
    largerThan: z.number().optional().describe("Filter emails larger than this size in bytes (e.g., 1048576 for 1MB)"),
    smallerThan: z.number().optional().describe("Filter emails smaller than this size in bytes"),
    hasWords: z.string().optional().describe("Filter emails containing all these words"),
    exactPhrase: z.string().optional().describe("Filter emails containing this exact phrase"),
    excludeWords: z.string().optional().describe("Exclude emails containing these words"),
    maxResults: z.number().optional().default(10).describe("Maximum number of results to return (default: 10)"),
    includeSpamTrash: z.boolean().optional().default(false).describe("Include emails from Spam and Trash (default: false)"),
});

export const ListLabelsSchema = z.object({
    includeSystemLabels: z.boolean().optional().default(true).describe("Include system labels like INBOX, SENT, DRAFT (default: true)"),
    includeUserLabels: z.boolean().optional().default(true).describe("Include user-created labels (default: true)"),
});

export const ListThreadsSchema = z.object({
    query: z.string().optional().describe("Gmail search query to filter threads (e.g., 'is:unread')"),
    maxResults: z.number().optional().default(10).describe("Maximum number of threads to return (default: 10)"),
    labelIds: z.array(z.string()).optional().describe("Only return threads with these label IDs"),
    includeSpamTrash: z.boolean().optional().default(false).describe("Include threads from Spam and Trash (default: false)"),
});

export const GetThreadSchema = z.object({
    threadId: z.string().describe("ID of the thread to retrieve"),
    format: z.enum(['full', 'metadata', 'minimal']).optional().default('full').describe("Format of the returned thread messages (default: full)"),
});

export const ModifyThreadSchema = z.object({
    threadId: z.string().describe("ID of the thread to modify"),
    addLabelIds: z.array(z.string()).optional().describe("List of label IDs to add to all messages in the thread"),
    removeLabelIds: z.array(z.string()).optional().describe("List of label IDs to remove from all messages in the thread"),
});

export const TrashThreadSchema = z.object({
    threadId: z.string().describe("ID of the thread to move to trash"),
});

export const GetVacationSettingsSchema = z.object({});

export const UpdateVacationSettingsSchema = z.object({
    enableAutoReply: z.boolean().describe("Enable or disable vacation auto-reply"),
    responseSubject: z.string().optional().describe("Subject line for the auto-reply message"),
    responseBodyPlainText: z.string().optional().describe("Plain text body of the auto-reply message"),
    responseBodyHtml: z.string().optional().describe("HTML body of the auto-reply message"),
    restrictToContacts: z.boolean().optional().describe("Only send auto-reply to contacts (default: false)"),
    restrictToDomain: z.boolean().optional().describe("Only send auto-reply to domain members (default: false)"),
    startTime: z.number().optional().describe("Start time for vacation (Unix timestamp in milliseconds)"),
    endTime: z.number().optional().describe("End time for vacation (Unix timestamp in milliseconds)"),
});

export const MoveToTrashSchema = z.object({
    messageId: z.string().describe("ID of the email message to move to trash"),
});

export const ListDraftsSchema = z.object({
    maxResults: z.number().optional().default(10).describe("Maximum number of drafts to return (default: 10)"),
    query: z.string().optional().describe("Gmail search query to filter drafts"),
    includeSpamTrash: z.boolean().optional().default(false).describe("Include drafts from Spam and Trash (default: false)"),
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
