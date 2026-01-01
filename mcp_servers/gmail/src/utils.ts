// ============================================================================
// IMPORTS
// ============================================================================

import type { GmailMessagePart, EmailContent } from './schemas.js';

// ============================================================================
// A. EMAIL UTILITIES
// ============================================================================

/**
 * Helper function to encode email headers containing non-ASCII characters
 * according to RFC 2047 MIME specification
 */
function encodeEmailHeader(text: string): string {
    // Only encode if the text contains non-ASCII characters
    if (/[^\x00-\x7F]/.test(text)) {
        // Use MIME Words encoding (RFC 2047)
        return '=?UTF-8?B?' + Buffer.from(text).toString('base64') + '?=';
    }
    return text;
}

export const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
};

export function createEmailMessage(validatedArgs: any): string {
    const encodedSubject = encodeEmailHeader(validatedArgs.subject);
    // Determine content type based on available content and explicit mimeType
    let mimeType = validatedArgs.mimeType || 'text/plain';
    
    // If htmlBody is provided and mimeType isn't explicitly set to text/plain,
    // use multipart/alternative to include both versions
    if (validatedArgs.htmlBody && mimeType !== 'text/plain') {
        mimeType = 'multipart/alternative';
    }

    // Generate a random boundary string for multipart messages
    const boundary = `----=_NextPart_${Math.random().toString(36).substring(2)}`;

    // Validate email addresses
    (validatedArgs.to as string[]).forEach(email => {
        if (!validateEmail(email)) {
            throw new Error(`Recipient email address is invalid: ${email}`);
        }
    });

    // Common email headers
    const emailParts = [
        'From: me',
        `To: ${validatedArgs.to.join(', ')}`,
        validatedArgs.cc ? `Cc: ${validatedArgs.cc.join(', ')}` : '',
        validatedArgs.bcc ? `Bcc: ${validatedArgs.bcc.join(', ')}` : '',
        `Subject: ${encodedSubject}`,
        // Add thread-related headers if specified
        validatedArgs.inReplyTo ? `In-Reply-To: ${validatedArgs.inReplyTo}` : '',
        validatedArgs.inReplyTo ? `References: ${validatedArgs.inReplyTo}` : '',
        'MIME-Version: 1.0',
    ].filter(Boolean);

    // Construct the email based on the content type
    if (mimeType === 'multipart/alternative') {
        // Multipart email with both plain text and HTML
        emailParts.push(`Content-Type: multipart/alternative; boundary="${boundary}"`);
        emailParts.push('');
        
        // Plain text part
        emailParts.push(`--${boundary}`);
        emailParts.push('Content-Type: text/plain; charset=UTF-8');
        emailParts.push('Content-Transfer-Encoding: 7bit');
        emailParts.push('');
        emailParts.push(validatedArgs.body);
        emailParts.push('');
        
        // HTML part
        emailParts.push(`--${boundary}`);
        emailParts.push('Content-Type: text/html; charset=UTF-8');
        emailParts.push('Content-Transfer-Encoding: 7bit');
        emailParts.push('');
        emailParts.push(validatedArgs.htmlBody || validatedArgs.body); // Use body as fallback
        emailParts.push('');
        
        // Close the boundary
        emailParts.push(`--${boundary}--`);
    } else if (mimeType === 'text/html') {
        // HTML-only email
        emailParts.push('Content-Type: text/html; charset=UTF-8');
        emailParts.push('Content-Transfer-Encoding: 7bit');
        emailParts.push('');
        emailParts.push(validatedArgs.htmlBody || validatedArgs.body);
    } else {
        // Plain text email (default)
        emailParts.push('Content-Type: text/plain; charset=UTF-8');
        emailParts.push('Content-Transfer-Encoding: 7bit');
        emailParts.push('');
        emailParts.push(validatedArgs.body);
    }

    return emailParts.join('\r\n');
}

/**
 * Extracts text content from a PDF file encoded in base64
 * @param base64Data - The base64 encoded PDF data
 * @param filename - The filename for better error messages
 * @returns The extracted text content or an error message
 */
export async function extractPdfText(base64Data: string, filename: string): Promise<string> {
    try {
        // Dynamically import internal implementation to avoid debug harness in index.js
        // @ts-ignore - no type declarations for internal path
        const pdfParse = (await import('pdf-parse/lib/pdf-parse.js')).default as any;
        
        // Convert base64 to buffer
        const buffer = Buffer.from(base64Data, 'base64');
     
        // Parse PDF and extract text
        const data = await pdfParse(buffer);
        
        // Return extracted text with metadata
        const result = [
            `=== PDF Content from ${filename} ===`,
            `Pages: ${data.numpages}`,
            ``,
            `--- Text Content ---`,
            data.text,
            ``,
            `=== End of PDF Content ===`
        ].join('\n');
        
        return result;
    } catch (error) {
        console.error(`Error extracting text from PDF ${filename}:`, error);
        return `[Error: Unable to extract text from PDF "${filename}". The file may be corrupted, password-protected, or contain only images without text.]`;
    }
}

/**
 * Extracts text content from a DOCX Word document encoded in base64
 * Uses the mammoth library to extract raw text
 */
export async function extractDocxText(base64Data: string, filename: string): Promise<string> {
    try {
        // Dynamically import to avoid loading cost unless needed
        const mammoth = await import('mammoth');

        const buffer = Buffer.from(base64Data, 'base64');
        const result = await mammoth.extractRawText({ buffer });

        const messages = (result.messages || []).map((m: any) => `- ${m.message || m.value || JSON.stringify(m)}`).join('\n');
        const text = result.value || '';

        return [
            `=== Word (DOCX) Content from ${filename} ===`,
            messages ? `Messages:\n${messages}\n` : '',
            `--- Text Content ---`,
            text,
            '',
            `=== End of Word Content ===`
        ].filter(Boolean).join('\n');
    } catch (error) {
        console.error(`Error extracting text from DOCX ${filename}:`, error);
        return `[Error: Unable to extract text from Word file "${filename}". Ensure it is a .docx file. Legacy .doc format is not supported by mammoth.]`;
    }
}

/**
 * Extracts text/CSV-like content from an Excel (.xlsx) file encoded in base64
 * Uses exceljs (actively maintained) and intentionally does not process legacy .xls
 */
export async function extractXlsxText(base64Data: string, filename: string): Promise<string> {
    try {
        const ExcelJSImport = await import('exceljs');
        const ExcelJS: any = (ExcelJSImport as any).default ?? ExcelJSImport;
        const buffer = Buffer.from(base64Data, 'base64');

        const workbook = new ExcelJS.Workbook();
        await workbook.xlsx.load(buffer);

        const sheetTexts: string[] = [];
        workbook.worksheets.forEach((worksheet: any) => {
            const rowsOut: string[] = [];
            worksheet.eachRow({ includeEmpty: false }, (row: any) => {
                const values: any[] = Array.isArray(row.values) ? row.values.slice(1) : [];
                const cells = values.map((v) => {
                    if (v === null || v === undefined) return '';
                    if (typeof v === 'object') {
                        // Cell objects can be rich text, formulas, etc.
                        if (typeof v.text === 'string') return v.text;
                        if (typeof v.result !== 'undefined') return String(v.result);
                        if (typeof v.richText !== 'undefined') {
                            try { return v.richText.map((rt: any) => rt.text).join(''); } catch { return ''; }
                        }
                        return String(v.toString?.() ?? '');
                    }
                    return String(v);
                });
                rowsOut.push(cells.join(','));
            });
            sheetTexts.push([
                `Sheet: ${worksheet.name}`,
                rowsOut.join('\n')
            ].join('\n'));
        });

        return [
            `=== Excel Content from ${filename} ===`,
            ...sheetTexts,
            `=== End of Excel Content ===`
        ].join('\n\n');
    } catch (error) {
        console.error(`Error extracting text from Excel ${filename}:`, error);
        return `[Error: Unable to extract content from Excel file "${filename}". The file may be corrupted or in an unsupported format.]`;
    }
}

// ============================================================================
// B. HELPER FUNCTIONS
// ============================================================================

/**
 * Convert base64url (Gmail format) to standard base64
 */
export function base64UrlToBase64(input: string): string {
    let output = input.replace(/-/g, '+').replace(/_/g, '/');
    const padLen = output.length % 4;
    if (padLen === 2) output += '==';
    else if (padLen === 3) output += '=';
    else if (padLen === 1) output += '==='; // extremely rare, but safe guard
    return output;
}

/**
 * Recursively extract email body content from MIME message parts
 * Handles complex email structures with nested parts
 */
export function extractEmailContent(messagePart: GmailMessagePart): EmailContent {
    // Initialize containers for different content types
    let textContent = '';
    let htmlContent = '';

    // If the part has a body with data, process it based on MIME type
    if (messagePart.body && messagePart.body.data) {
        const content = Buffer.from(messagePart.body.data, 'base64').toString('utf8');

        // Store content based on its MIME type
        if (messagePart.mimeType === 'text/plain') {
            textContent = content;
        } else if (messagePart.mimeType === 'text/html') {
            htmlContent = content;
        }
    }

    // If the part has nested parts, recursively process them
    if (messagePart.parts && messagePart.parts.length > 0) {
        for (const part of messagePart.parts) {
            const { text, html } = extractEmailContent(part);
            if (text) textContent += text;
            if (html) htmlContent += html;
        }
    }

    // Return both plain text and HTML content
    return { text: textContent, html: htmlContent };
}

/**
 * Process operations in batches with fallback to individual items on failure
 */
export async function processBatches<T, U>(
    items: T[],
    batchSize: number,
    processFn: (batch: T[]) => Promise<U[]>
): Promise<{ successes: U[], failures: { item: T, error: Error }[] }> {
    const successes: U[] = [];
    const failures: { item: T, error: Error }[] = [];

    // Process in batches
    for (let i = 0; i < items.length; i += batchSize) {
        const batch = items.slice(i, i + batchSize);
        try {
            const results = await processFn(batch);
            successes.push(...results);
        } catch (error) {
            // If batch fails, try individual items
            for (const item of batch) {
                try {
                    const result = await processFn([item]);
                    successes.push(...result);
                } catch (itemError) {
                    failures.push({ item, error: itemError as Error });
                }
            }
        }
    }

    return { successes, failures };
}

// ============================================================================
// C. ERROR HANDLING MODULE
// ============================================================================

export enum GmailErrorType {
    // Authentication & Authorization
    AUTH_ERROR = 'AUTH_ERROR',
    INVALID_TOKEN = 'INVALID_TOKEN',
    INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS',

    // API Errors
    GMAIL_API_ERROR = 'GMAIL_API_ERROR',
    PEOPLE_API_ERROR = 'PEOPLE_API_ERROR',

    // Rate Limiting & Quota
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
    QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',

    // Validation Errors
    VALIDATION_ERROR = 'VALIDATION_ERROR',
    INVALID_EMAIL_FORMAT = 'INVALID_EMAIL_FORMAT',
    INVALID_MESSAGE_ID = 'INVALID_MESSAGE_ID',
    INVALID_THREAD_ID = 'INVALID_THREAD_ID',
    INVALID_LABEL_ID = 'INVALID_LABEL_ID',

    // Resource Errors
    NOT_FOUND = 'NOT_FOUND',
    MESSAGE_NOT_FOUND = 'MESSAGE_NOT_FOUND',
    THREAD_NOT_FOUND = 'THREAD_NOT_FOUND',
    ATTACHMENT_NOT_FOUND = 'ATTACHMENT_NOT_FOUND',

    // Document Processing Errors
    PDF_EXTRACTION_ERROR = 'PDF_EXTRACTION_ERROR',
    DOCX_EXTRACTION_ERROR = 'DOCX_EXTRACTION_ERROR',
    XLSX_EXTRACTION_ERROR = 'XLSX_EXTRACTION_ERROR',
    UNSUPPORTED_FORMAT = 'UNSUPPORTED_FORMAT',

    // Network & Transient Errors
    NETWORK_ERROR = 'NETWORK_ERROR',
    TIMEOUT_ERROR = 'TIMEOUT_ERROR',
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',

    // Other
    UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

export class GmailMCPError extends Error {
    readonly type: GmailErrorType;
    readonly module: string;
    readonly status?: number;
    readonly retryable: boolean;
    readonly originalError?: any;
    readonly timestamp: Date;

    constructor(
        type: GmailErrorType,
        message: string,
        options?: {
            status?: number;
            retryable?: boolean;
            originalError?: any;
            module?: string;
        }
    ) {
        super(message);
        this.name = 'GmailMCPError';
        this.type = type;
        this.module = options?.module || 'gmail-mcp';
        this.status = options?.status;
        this.retryable = options?.retryable ?? this.isRetryableByDefault();
        this.originalError = options?.originalError;
        this.timestamp = new Date();

        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
    }

    private isRetryableByDefault(): boolean {
        const retryableTypes = [
            GmailErrorType.RATE_LIMIT_EXCEEDED,
            GmailErrorType.NETWORK_ERROR,
            GmailErrorType.TIMEOUT_ERROR,
            GmailErrorType.SERVICE_UNAVAILABLE,
        ];
        return retryableTypes.includes(this.type);
    }

    toJSON() {
        return {
            name: this.name,
            type: this.type,
            message: this.message,
            module: this.module,
            status: this.status,
            retryable: this.retryable,
            timestamp: this.timestamp.toISOString(),
        };
    }
}

export function createGmailError(
    type: GmailErrorType,
    message: string,
    options?: {
        status?: number;
        retryable?: boolean;
        originalError?: any;
        module?: string;
    }
): GmailMCPError {
    return new GmailMCPError(type, message, options);
}

export function parseGoogleApiError(error: any): GmailMCPError {
    const status = error.code || error.status;
    const message = error.message || error.error || 'Unknown Gmail API error';

    switch (status) {
        case 401:
            return createGmailError(
                GmailErrorType.INVALID_TOKEN,
                'Authentication failed. Your access token may be invalid or expired.',
                { status, originalError: error, retryable: false }
            );
        case 403:
            if (message.toLowerCase().includes('quota')) {
                return createGmailError(
                    GmailErrorType.QUOTA_EXCEEDED,
                    'Gmail API quota exceeded. Please try again later.',
                    { status, originalError: error, retryable: false }
                );
            }
            return createGmailError(
                GmailErrorType.INSUFFICIENT_PERMISSIONS,
                'Insufficient permissions. Your token may lack required Gmail API scopes.',
                { status, originalError: error, retryable: false }
            );
        case 404:
            return createGmailError(
                GmailErrorType.NOT_FOUND,
                'Resource not found. The message, thread, or label may not exist.',
                { status, originalError: error, retryable: false }
            );
        case 429:
            return createGmailError(
                GmailErrorType.RATE_LIMIT_EXCEEDED,
                'Rate limit exceeded. Please wait before making more requests.',
                { status, originalError: error, retryable: true }
            );
        case 500:
        case 502:
        case 503:
        case 504:
            return createGmailError(
                GmailErrorType.SERVICE_UNAVAILABLE,
                'Gmail service temporarily unavailable. Please try again.',
                { status, originalError: error, retryable: true }
            );
        default:
            return createGmailError(
                GmailErrorType.GMAIL_API_ERROR,
                message,
                { status, originalError: error, retryable: false }
            );
    }
}

export function parseZodError(error: any): GmailMCPError {
    const issues = error.errors || error.issues || [];
    const messages = issues.map((issue: any) =>
        `${issue.path.join('.')}: ${issue.message}`
    );

    return createGmailError(
        GmailErrorType.VALIDATION_ERROR,
        `Input validation failed:\n${messages.join('\n')}`,
        { originalError: error, retryable: false }
    );
}

export function formatGmailError(
    error: GmailMCPError,
    operation: string,
    resource?: string
): string {
    let message = `Failed to ${operation}`;
    if (resource) {
        message += `: "${resource}"`;
    }
    message += `\n\nError Type: ${error.type}\n`;
    message += `Message: ${error.message}\n`;

    if (error.status) {
        message += `HTTP Status: ${error.status}\n`;
    }

    return message;
}

export function addErrorGuidance(
    errorMessage: string,
    error: GmailMCPError,
    context?: {
        resource?: string;
        operation?: string;
        suggestions?: string[];
    }
): string {
    let enhanced = errorMessage;

    // Add status-specific guidance
    if (error.status === 401) {
        enhanced += `\n\nCommon Solutions:\n`;
        enhanced += `- Verify your access token is valid and not expired\n`;
        enhanced += `- Ensure token has Gmail API permissions\n`;
        enhanced += `- Check AUTH_DATA environment variable or x-auth-data header\n`;
    } else if (error.status === 403) {
        enhanced += `\n\nCommon Solutions:\n`;
        enhanced += `- Check OAuth scopes include Gmail access\n`;
        enhanced += `- Verify you have permission to access this resource\n`;
        enhanced += `- If quota error, wait and try again later\n`;
    } else if (error.status === 404) {
        enhanced += `\n\nCommon Solutions:\n`;
        enhanced += `- Verify the ${context?.resource || 'resource'} ID is correct\n`;
        enhanced += `- Check that the ${context?.resource || 'resource'} hasn't been deleted\n`;
        enhanced += `- Ensure you have access to view this ${context?.resource || 'resource'}\n`;
    } else if (error.status === 429) {
        enhanced += `\n\nRate Limit Guidance:\n`;
        enhanced += `- Wait a few moments before retrying\n`;
        enhanced += `- Reduce frequency of requests\n`;
        enhanced += `- Consider batching operations\n`;
    }

    // Add custom suggestions
    if (context?.suggestions && context.suggestions.length > 0) {
        enhanced += `\n\nAdditional Suggestions:\n`;
        context.suggestions.forEach(suggestion => {
            enhanced += `- ${suggestion}\n`;
        });
    }

    return enhanced;
}

// ============================================================================
// D. RETRY LOGIC MODULE
// ============================================================================

export interface RetryConfig {
    maxAttempts: number;
    initialDelayMs: number;
    maxDelayMs: number;
    backoffMultiplier: number;
    retryableErrors: GmailErrorType[];
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxAttempts: 3,
    initialDelayMs: 1000,
    maxDelayMs: 10000,
    backoffMultiplier: 2,
    retryableErrors: [
        GmailErrorType.RATE_LIMIT_EXCEEDED,
        GmailErrorType.NETWORK_ERROR,
        GmailErrorType.TIMEOUT_ERROR,
        GmailErrorType.SERVICE_UNAVAILABLE,
    ],
};

export const RATE_LIMIT_RETRY_CONFIG: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    maxAttempts: 5,
    initialDelayMs: 2000,
    maxDelayMs: 30000,
};

export const BATCH_RETRY_CONFIG: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    maxAttempts: 2,
    initialDelayMs: 500,
};

export async function withRetry<T>(
    operation: () => Promise<T>,
    config: Partial<RetryConfig> = {},
    operationName: string = 'operation'
): Promise<T> {
    const finalConfig: RetryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
    let lastError: GmailMCPError | undefined;

    for (let attempt = 1; attempt <= finalConfig.maxAttempts; attempt++) {
        try {
            console.log(`[${operationName}] Attempt ${attempt}/${finalConfig.maxAttempts}`);
            const result = await operation();

            if (attempt > 1) {
                console.log(`[${operationName}] Succeeded after ${attempt} attempts`);
            }

            return result;
        } catch (error: any) {
            const gmailError = error instanceof GmailMCPError
                ? error
                : parseGoogleApiError(error);

            lastError = gmailError;

            const shouldRetryThis = shouldRetry(gmailError, attempt, finalConfig);

            if (!shouldRetryThis || attempt === finalConfig.maxAttempts) {
                console.error(
                    `[${operationName}] Failed after ${attempt} attempts: ${gmailError.message}`
                );
                throw gmailError;
            }

            const delay = calculateDelay(attempt, finalConfig);

            console.warn(
                `[${operationName}] Attempt ${attempt} failed (${gmailError.type}). ` +
                `Retrying in ${delay}ms... Error: ${gmailError.message}`
            );

            await sleep(delay);
        }
    }

    throw lastError || createGmailError(
        GmailErrorType.UNKNOWN_ERROR,
        `${operationName} failed after retries`
    );
}

export function shouldRetry(
    error: GmailMCPError,
    attempt: number,
    config: RetryConfig
): boolean {
    if (attempt >= config.maxAttempts) {
        return false;
    }

    const isRetryableType = config.retryableErrors.includes(error.type);
    return isRetryableType && error.retryable;
}

export function calculateDelay(attempt: number, config: RetryConfig): number {
    const exponentialDelay = config.initialDelayMs *
        Math.pow(config.backoffMultiplier, attempt - 1);

    const delay = Math.min(exponentialDelay, config.maxDelayMs);

    // Add jitter (±20%)
    const jitter = delay * 0.2 * (Math.random() * 2 - 1);

    return Math.round(delay + jitter);
}

export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// E. VALIDATION MODULE
// ============================================================================

export function validateEmailAddresses(emails: string[]): void {
    if (!emails || emails.length === 0) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'At least one email address is required'
        );
    }

    for (const email of emails) {
        if (!validateEmail(email)) {
            throw createGmailError(
                GmailErrorType.INVALID_EMAIL_FORMAT,
                `Invalid email address format: "${email}". Email must be in format: user@domain.com`,
                { retryable: false }
            );
        }
    }
}

export function validateMessageId(messageId: string): void {
    if (!messageId || messageId.trim() === '') {
        throw createGmailError(
            GmailErrorType.INVALID_MESSAGE_ID,
            'Message ID cannot be empty'
        );
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(messageId)) {
        throw createGmailError(
            GmailErrorType.INVALID_MESSAGE_ID,
            `Invalid message ID format: "${messageId}". Should contain only alphanumeric characters, hyphens, and underscores.`,
            { retryable: false }
        );
    }
}

export function validateThreadId(threadId: string): void {
    if (!threadId || threadId.trim() === '') {
        throw createGmailError(
            GmailErrorType.INVALID_THREAD_ID,
            'Thread ID cannot be empty'
        );
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(threadId)) {
        throw createGmailError(
            GmailErrorType.INVALID_THREAD_ID,
            `Invalid thread ID format: "${threadId}"`,
            { retryable: false }
        );
    }
}

export function validateLabelIds(labelIds: string[]): void {
    if (!labelIds || labelIds.length === 0) {
        return;
    }

    const validLabelPattern = /^[a-zA-Z0-9_-]+$/;

    for (const labelId of labelIds) {
        if (!validLabelPattern.test(labelId)) {
            throw createGmailError(
                GmailErrorType.INVALID_LABEL_ID,
                `Invalid label ID format: "${labelId}"`,
                { retryable: false }
            );
        }
    }
}

export function validateSearchQuery(query: string, maxLength: number = 500): void {
    if (query && query.length > maxLength) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            `Search query too long (${query.length} chars). Maximum is ${maxLength} characters.`,
            { retryable: false }
        );
    }
}

export function validateApiResponse<T>(
    response: any,
    expectedFields: string[],
    resourceType: string = 'resource'
): T {
    if (!response) {
        throw createGmailError(
            GmailErrorType.GMAIL_API_ERROR,
            `Gmail API returned empty response for ${resourceType}`,
            { retryable: false }
        );
    }

    const missingFields: string[] = [];
    for (const field of expectedFields) {
        if (!(field in response)) {
            missingFields.push(field);
        }
    }

    if (missingFields.length > 0) {
        console.warn(
            `Response missing expected fields for ${resourceType}: ${missingFields.join(', ')}`
        );
    }

    return response as T;
}

export function validateMessageResponse(response: any): void {
    validateApiResponse(response, ['id', 'threadId'], 'message');
}

export function validateThreadResponse(response: any): void {
    validateApiResponse(response, ['id', 'messages'], 'thread');

    if (!Array.isArray(response.messages) || response.messages.length === 0) {
        throw createGmailError(
            GmailErrorType.GMAIL_API_ERROR,
            'Thread contains no messages',
            { retryable: false }
        );
    }
}

export function sanitizeEmailContent(content: string): string {
    if (!content) return '';

    // Remove potential script tags or malicious content
    let sanitized = content
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '');

    return sanitized;
}