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
// B. BASE64 AND CONTENT UTILITIES
// ============================================================================

/**
 * Convert base64url (Gmail) -> standard base64
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
 * 
 * Note: Gmail API returns base64url-encoded data, which must be converted
 * to standard base64 before decoding.
 */
export function extractEmailContent(messagePart: GmailMessagePart): EmailContent {
    // Initialize containers for different content types
    let textContent = '';
    let htmlContent = '';

    // If the part has a body with data, process it based on MIME type
    if (messagePart.body && messagePart.body.data) {
        // Gmail API returns base64url encoding - convert to standard base64 first
        const standardBase64 = base64UrlToBase64(messagePart.body.data);
        const content = Buffer.from(standardBase64, 'base64').toString('utf8');

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

// ============================================================================
// C. BATCH PROCESSING UTILITIES
// ============================================================================

/**
 * Helper function to process operations in batches with automatic retry on failure
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
// D. ERROR HANDLING
// ============================================================================

/**
 * Gmail-specific error types for better error categorization
 */
export enum GmailErrorType {
    // Authentication & Authorization
    AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
    AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
    TOKEN_EXPIRED = 'TOKEN_EXPIRED',
    
    // Rate Limiting
    RATE_LIMIT_ERROR = 'RATE_LIMIT_ERROR',
    QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
    
    // Resource Errors
    NOT_FOUND = 'NOT_FOUND',
    ALREADY_EXISTS = 'ALREADY_EXISTS',
    
    // Validation Errors
    VALIDATION_ERROR = 'VALIDATION_ERROR',
    INVALID_INPUT = 'INVALID_INPUT',
    
    // Server Errors
    SERVER_ERROR = 'SERVER_ERROR',
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
    
    // Network Errors
    NETWORK_ERROR = 'NETWORK_ERROR',
    TIMEOUT_ERROR = 'TIMEOUT_ERROR',
    
    // Unknown
    UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

/**
 * Custom error class for Gmail MCP operations
 */
export class GmailMCPError extends Error {
    public readonly type: GmailErrorType;
    public readonly status?: number;
    public readonly retryable: boolean;
    public readonly details?: Record<string, unknown>;
    public readonly timestamp: Date;

    constructor(
        type: GmailErrorType,
        message: string,
        options?: {
            status?: number;
            retryable?: boolean;
            details?: Record<string, unknown>;
            cause?: Error;
        }
    ) {
        super(message);
        this.name = 'GmailMCPError';
        this.type = type;
        this.status = options?.status;
        this.retryable = options?.retryable ?? false;
        this.details = options?.details;
        this.timestamp = new Date();
        
        if (options?.cause) {
            this.cause = options.cause;
        }
    }
}

/**
 * Create a standardized Gmail error
 */
export function createGmailError(
    type: GmailErrorType,
    message: string,
    options?: {
        status?: number;
        retryable?: boolean;
        details?: Record<string, unknown>;
        originalError?: Error;
    }
): GmailMCPError {
    return new GmailMCPError(type, message, {
        status: options?.status,
        retryable: options?.retryable,
        details: options?.details,
        cause: options?.originalError,
    });
}

/**
 * Parse Google API errors into GmailMCPError
 */
export function parseGoogleApiError(error: any): GmailMCPError {
    const status = error?.response?.status || error?.code || error?.status;
    const message = error?.response?.data?.error?.message 
        || error?.message 
        || 'An unknown error occurred';
    const errorCode = error?.response?.data?.error?.code;
    const errors = error?.response?.data?.error?.errors || [];

    // Determine error type based on status code and error details
    let type: GmailErrorType;
    let retryable = false;

    switch (status) {
        case 400:
            type = GmailErrorType.INVALID_INPUT;
            break;
        case 401:
            type = GmailErrorType.AUTHENTICATION_ERROR;
            break;
        case 403:
            // Check for rate limiting vs authorization
            if (errors.some((e: any) => e.reason === 'rateLimitExceeded')) {
                type = GmailErrorType.RATE_LIMIT_ERROR;
                retryable = true;
            } else if (errors.some((e: any) => e.reason === 'quotaExceeded')) {
                type = GmailErrorType.QUOTA_EXCEEDED;
            } else {
                type = GmailErrorType.AUTHORIZATION_ERROR;
            }
            break;
        case 404:
            type = GmailErrorType.NOT_FOUND;
            break;
        case 409:
            type = GmailErrorType.ALREADY_EXISTS;
            break;
        case 429:
            type = GmailErrorType.RATE_LIMIT_ERROR;
            retryable = true;
            break;
        case 500:
            type = GmailErrorType.SERVER_ERROR;
            retryable = true;
            break;
        case 503:
            type = GmailErrorType.SERVICE_UNAVAILABLE;
            retryable = true;
            break;
        default:
            if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
                type = GmailErrorType.NETWORK_ERROR;
                retryable = true;
            } else if (error.code === 'ETIMEDOUT' || error.code === 'ESOCKETTIMEDOUT') {
                type = GmailErrorType.TIMEOUT_ERROR;
                retryable = true;
            } else {
                type = GmailErrorType.UNKNOWN_ERROR;
            }
    }

    return new GmailMCPError(type, message, {
        status,
        retryable,
        details: {
            errorCode,
            errors,
            originalMessage: error?.message,
        },
        cause: error,
    });
}

/**
 * Parse Zod validation errors into GmailMCPError
 */
export function parseZodError(error: any): GmailMCPError {
    const issues = error.issues || [];
    const formattedIssues = issues.map((issue: any) => {
        const path = issue.path.join('.');
        return `${path}: ${issue.message}`;
    }).join('; ');

    return new GmailMCPError(
        GmailErrorType.VALIDATION_ERROR,
        `Validation failed: ${formattedIssues}`,
        {
            retryable: false,
            details: {
                issues,
            },
            cause: error,
        }
    );
}

/**
 * Format error for user-friendly display
 */
export function formatGmailError(error: GmailMCPError, operation: string): string {
    const parts: string[] = [
        `Failed to ${operation}`,
    ];

    parts.push(`: ${error.message}`);

    if (error.retryable) {
        parts.push(' (this error may be temporary, consider retrying)');
    }

    return parts.join('');
}

/**
 * Add contextual guidance to error messages
 */
export function addErrorGuidance(
    errorMessage: string,
    error: GmailMCPError,
    context?: { operation?: string; suggestions?: string[] }
): string {
    const guidance: string[] = [errorMessage];

    // Add type-specific guidance
    switch (error.type) {
        case GmailErrorType.AUTHENTICATION_ERROR:
        case GmailErrorType.TOKEN_EXPIRED:
            guidance.push('Please re-authenticate with Gmail.');
            break;
        case GmailErrorType.AUTHORIZATION_ERROR:
            guidance.push('The required Gmail permissions may not be granted.');
            break;
        case GmailErrorType.RATE_LIMIT_ERROR:
            guidance.push('Too many requests. Please wait before trying again.');
            break;
        case GmailErrorType.QUOTA_EXCEEDED:
            guidance.push('Gmail API quota exceeded. Try again later or check your API limits.');
            break;
        case GmailErrorType.NOT_FOUND:
            guidance.push('The requested resource was not found. Verify the ID is correct.');
            break;
        case GmailErrorType.VALIDATION_ERROR:
            guidance.push('Please check the input parameters.');
            break;
    }

    // Add custom suggestions
    if (context?.suggestions && context.suggestions.length > 0) {
        guidance.push(...context.suggestions);
    }

    return guidance.join(' ');
}

// ============================================================================
// E. RETRY LOGIC
// ============================================================================

/**
 * Configuration for retry behavior
 */
export interface RetryConfig {
    maxRetries: number;
    initialDelayMs: number;
    maxDelayMs: number;
    backoffMultiplier: number;
    retryableTypes: GmailErrorType[];
}

export const DEFAULT_RETRY_CONFIG: RetryConfig = {
    maxRetries: 3,
    initialDelayMs: 1000,
    maxDelayMs: 30000,
    backoffMultiplier: 2,
    retryableTypes: [
        GmailErrorType.RATE_LIMIT_ERROR,
        GmailErrorType.SERVER_ERROR,
        GmailErrorType.SERVICE_UNAVAILABLE,
        GmailErrorType.NETWORK_ERROR,
        GmailErrorType.TIMEOUT_ERROR,
    ],
};

export const RATE_LIMIT_RETRY_CONFIG: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    maxRetries: 5,
    initialDelayMs: 2000,
};

export const BATCH_RETRY_CONFIG: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    maxRetries: 2,
    initialDelayMs: 500,
};

/**
 * Sleep utility for delays
 */
function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Calculate delay with exponential backoff and jitter
 */
function calculateDelay(attempt: number, config: RetryConfig): number {
    const exponentialDelay = config.initialDelayMs * Math.pow(config.backoffMultiplier, attempt);
    const cappedDelay = Math.min(exponentialDelay, config.maxDelayMs);
    // Add jitter (±25%)
    const jitter = cappedDelay * (0.75 + Math.random() * 0.5);
    return Math.floor(jitter);
}

/**
 * Execute an operation with automatic retry on transient failures
 */
export async function withRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
    operationName?: string
): Promise<T> {
    let lastError: GmailMCPError | null = null;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error: any) {
            const gmailError = error instanceof GmailMCPError 
                ? error 
                : parseGoogleApiError(error);

            lastError = gmailError;

            // Check if error is retryable
            const isRetryable = gmailError.retryable && 
                config.retryableTypes.includes(gmailError.type);

            if (!isRetryable || attempt === config.maxRetries) {
                throw gmailError;
            }

            const delay = calculateDelay(attempt, config);
            console.warn(
                `[${operationName || 'operation'}] Attempt ${attempt + 1} failed with ${gmailError.type}. ` +
                `Retrying in ${delay}ms...`
            );

            await sleep(delay);
        }
    }

    // This should never be reached, but TypeScript needs it
    throw lastError || new GmailMCPError(
        GmailErrorType.UNKNOWN_ERROR,
        'Retry logic completed without result'
    );
}

// ============================================================================
// F. INPUT VALIDATION UTILITIES
// ============================================================================

/**
 * Validate multiple email addresses
 */
export function validateEmailAddresses(emails: string[]): void {
    const invalidEmails = emails.filter(email => !validateEmail(email));
    if (invalidEmails.length > 0) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            `Invalid email address(es): ${invalidEmails.join(', ')}`,
            { retryable: false }
        );
    }
}

/**
 * Validate Gmail message ID format
 */
export function validateMessageId(messageId: string): void {
    if (!messageId || typeof messageId !== 'string' || messageId.trim().length === 0) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'Message ID is required and must be a non-empty string',
            { retryable: false }
        );
    }
}

/**
 * Validate Gmail thread ID format
 */
export function validateThreadId(threadId: string): void {
    if (!threadId || typeof threadId !== 'string' || threadId.trim().length === 0) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'Thread ID is required and must be a non-empty string',
            { retryable: false }
        );
    }
}

/**
 * Validate label IDs
 */
export function validateLabelIds(labelIds: string[]): void {
    if (!Array.isArray(labelIds)) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'Label IDs must be an array',
            { retryable: false }
        );
    }
    
    const invalidLabels = labelIds.filter(id => !id || typeof id !== 'string');
    if (invalidLabels.length > 0) {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'All label IDs must be non-empty strings',
            { retryable: false }
        );
    }
}

/**
 * Validate search query
 */
export function validateSearchQuery(query: string): void {
    if (typeof query !== 'string') {
        throw createGmailError(
            GmailErrorType.VALIDATION_ERROR,
            'Search query must be a string',
            { retryable: false }
        );
    }
    
    // Check for potentially dangerous patterns (basic XSS prevention)
    const dangerousPatterns = [/<script/i, /javascript:/i, /on\w+=/i];
    for (const pattern of dangerousPatterns) {
        if (pattern.test(query)) {
            throw createGmailError(
                GmailErrorType.VALIDATION_ERROR,
                'Search query contains potentially unsafe content',
                { retryable: false }
            );
        }
    }
}

/**
 * Validate API response structure
 */
export function validateApiResponse(
    response: any,
    requiredFields: string[],
    resourceType: string
): void {
    if (!response) {
        throw createGmailError(
            GmailErrorType.SERVER_ERROR,
            `Invalid response received for ${resourceType}`,
            { retryable: true }
        );
    }

    const missingFields = requiredFields.filter(field => !(field in response));
    if (missingFields.length > 0) {
        throw createGmailError(
            GmailErrorType.SERVER_ERROR,
            `Response for ${resourceType} missing required fields: ${missingFields.join(', ')}`,
            { retryable: false }
        );
    }
}

/**
 * Validate message response
 */
export function validateMessageResponse(response: any): void {
    validateApiResponse(response, ['id'], 'message');
}

/**
 * Validate thread response
 */
export function validateThreadResponse(response: any): void {
    validateApiResponse(response, ['id', 'messages'], 'thread');
}

/**
 * Sanitize email content to prevent injection attacks
 */
export function sanitizeEmailContent(content: string): string {
    // Basic sanitization - remove null bytes and control characters
    return content
        .replace(/\0/g, '')
        .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '');
}
