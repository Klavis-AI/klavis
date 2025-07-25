/**
 * Utility functions for error handling in Dropbox MCP module
 */

import { DropboxResponseError } from 'dropbox';
import { DropboxMCPError, ErrorTypes, ErrorModules } from '../error.js';

/**
 * Wraps a Dropbox API error into our standard error format
 * @param error - The DropboxResponseError to wrap
 * @param message - Optional custom message
 * @param operation - Optional operation name for context-specific guidance
 * @throws DropboxMCPError - Always throws, never returns
 */
export function wrapDropboxError(error: unknown, message?: string, operation?: string): never {
    if (error instanceof DropboxResponseError) {
        const status = error.status || 'Unknown';
        const tag = error.error?.error?.['.tag'] || 'unknown';
        const summary = error.error?.error_summary || 'No error summary available';

        // Construct detailed message and include user message if provided
        let detailMessage = `status: ${status}, tag: ${tag}, summary: ${summary}`;
        
        // Add specific guidance for sharing operations
        if (operation === 'share_file' && status === 409) {
            if (tag === 'settings_error' && summary.includes('not_authorized')) {
                detailMessage += `\n\n💡 This error typically means:\n- Advanced sharing settings (password, expiration) require a paid Dropbox account\n- Your account type doesn't support the requested sharing options\n- Try sharing without advanced settings for basic functionality`;
            } else if (tag === 'settings_error' && summary.includes('invalid_settings')) {
                detailMessage += `\n\n💡 This error typically means:\n- The combination of sharing settings is not valid\n- Team-only visibility requires team membership\n- Check that all settings are appropriate for your account type`;
            }
        }
        
        const fullMessage = message ? `${message}\n${detailMessage}` : detailMessage;

        throw new DropboxMCPError(
            ErrorTypes.DROPBOX_API_ERROR,
            ErrorModules.DROPBOX_SDK,
            fullMessage
        );
    } else {
        wrapUnknownError(error, message);
    }
}

/**
 * Wraps a get-uri error into our standard error format
 * @param error - The original error from get-uri
 * @param path - The path that failed
 * @throws DropboxMCPError - Always throws, never returns
 */
export function wrapGetUriError(error: unknown, path: string): never {
    if (error instanceof Error) {
        const code = (error as any).code ?? 'unknown';
        throw new DropboxMCPError(
            ErrorTypes.GET_URI_ERROR,
            ErrorModules.GET_URI,
            `Failed to get URI for path "${path}". Status: ${code}, message: ${error.message}`
        );
    }

    throw new DropboxMCPError(
        ErrorTypes.GET_URI_ERROR,
        ErrorModules.GET_URI,
        `Failed to get URI for path "${path}". Unknown error occurred`
    );
}

/**
 * Wraps any other unknown error into our standard error format
 * @param error - The original error
 * @param context - Additional context about where the error occurred
 * @throws DropboxMCPError - Always throws, never returns
 */
export function wrapUnknownError(error: unknown, context?: string): never {
    let message = context ? `${context}: ` : '';

    if (error instanceof DropboxMCPError) {
        // If it's already a DropboxMCPError, just rethrow it
        throw error;
    } else if (error instanceof Error) {
        message += error.message;
    } else if (typeof error === 'string') {
        message += error;
    } else {
        message += 'Unknown error occurred';
    }

    throw new DropboxMCPError(ErrorTypes.UNKNOWN_ERROR, ErrorModules.UNKNOWN, message);
}

/**
 * Converts our standard error to user-friendly message
 * This should be used at the top level to convert errors to response messages
 * @param error - The error to format
 * @returns User-friendly error message string
 */
export function formatErrorForUser(error: unknown): string {
    if (error instanceof DropboxMCPError) {
        return `Error: [${error.errorModule}] ${error.type}:\n${error.message}`;
    }

    if (error instanceof Error) {
        return `Error: ${error.message}`;
    }

    return 'Error: An unknown error occurred. Please try again later';
}
