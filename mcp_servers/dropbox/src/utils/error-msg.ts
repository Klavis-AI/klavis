/**
 * Utility functions for error handling in Dropbox MCP module
 */

import { DropboxMCPError, ErrorTypes, ErrorModules } from '../error.js';

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