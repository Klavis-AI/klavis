import { GmailMessagePart, EmailContent } from "./schemas.js";

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
 * Uses pdfjs-dist (official Mozilla PDF.js) for better compatibility
 * @param base64Data - The base64 encoded PDF data
 * @param filename - The filename for better error messages
 * @returns The extracted text content or an error message
 */
export async function extractPdfText(base64Data: string, filename: string): Promise<string> {
    try {
        // Use pdfjs-dist (official Mozilla PDF.js) for better PDF format support
        const pdfjsLib = await import('pdfjs-dist/legacy/build/pdf.mjs');

        // Convert base64 to Uint8Array
        const buffer = Buffer.from(base64Data, 'base64');
        const uint8Array = new Uint8Array(buffer);

        // Load the PDF document
        const loadingTask = pdfjsLib.getDocument({
            data: uint8Array,
            useSystemFonts: true,
        });
        const pdfDocument = await loadingTask.promise;

        const numPages = pdfDocument.numPages;
        const textParts: string[] = [];

        // Extract text from each page
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            const page = await pdfDocument.getPage(pageNum);
            const textContent = await page.getTextContent();

            // Combine text items into page text
            const pageText = textContent.items
                .map((item: any) => item.str)
                .join(' ');

            if (pageText.trim()) {
                textParts.push(`--- Page ${pageNum} ---\n${pageText}`);
            }
        }

        // Return extracted text with metadata
        const result = [
            `=== PDF Content from ${filename} ===`,
            `Pages: ${numPages}`,
            ``,
            `--- Text Content ---`,
            textParts.join('\n\n'),
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
 * Helper function to process operations in batches with fallback to individual items on failure
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

/**
 * Send warmup request with empty query to update the cache.
 *
 * According to Google's documentation, searchContacts and otherContacts.search
 * require a warmup request before actual searches for better performance.
 * See: https://developers.google.com/people/v1/contacts#search_the_users_contacts
 * and https://developers.google.com/people/v1/other-contacts#search_the_users_other_contacts
 */
export async function warmupContactSearch(peopleClient: any, contactType: 'personal' | 'other'): Promise<void> {
    try {
        if (contactType === 'personal') {
            // Warmup for people.searchContacts
            await peopleClient.people.searchContacts({
                query: '',
                pageSize: 1,
                readMask: 'names',
            });
            console.log('Warmup request sent for personal contacts');
        } else if (contactType === 'other') {
            // Warmup for otherContacts.search
            await peopleClient.otherContacts.search({
                query: '',
                pageSize: 1,
                readMask: 'names',
            });
            console.log('Warmup request sent for other contacts');
        }
    } catch (error) {
        // Don't fail if warmup fails, just log it
        console.warn(`Warmup request failed for ${contactType} contacts:`, error);
    }
}
