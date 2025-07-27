/**
 * Custom error class for the Dropbox MCP module
 */
export class DropboxMCPError extends Error {
    public type: string;
    public errorModule: string;
    public status: string;
    public error_summary : string;

    constructor(type: string, errorModule: string, message: string, status?: string) {
        super(message);
        this.name = 'DropboxMCPError';
        this.type = type;
        this.errorModule = errorModule;
        this.status = status || '400';
        this.error_summary = `${type} (${errorModule}): ${message}`;
    }
}

/**
 * Error types
 */
export const ErrorTypes = {
    DROPBOX_API_ERROR: 'DROPBOX_API_ERROR',
    GET_URI_ERROR: 'GET_URI_ERROR',
    OTHERS_ERROR: 'OTHERS_ERROR',
    UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

/**
 * Error modules
 */
export const ErrorModules = {
    DROPBOX_SDK: 'dropbox-sdk',
    GET_URI: 'get-uri',
    OTHERS: 'others',
    UNKNOWN: 'unknown'
} as const;
