/**
 * Formats Dropbox API errors with detailed information for better debugging
 * @param error The error object from Dropbox API
 * @param operation The operation that failed (e.g., "upload file", "share folder")
 * @param resource The resource being operated on (e.g., file path, folder name)
 * @returns Formatted error message with detailed information
 */
export function formatDropboxError(error: any, operation: string, resource?: string): string {
    let errorMessage = `Failed to ${operation}`;
    if (resource) {
        errorMessage += `: "${resource}"`;
    }
    errorMessage += `\n`;

    // Add detailed API error information
    errorMessage += `\nDetailed Error Information:\n`;
    errorMessage += `- HTTP Status: ${error.status || 'Unknown'}\n`;
    errorMessage += `- Error Summary: ${error.error_summary || 'Not provided'}\n`;
    errorMessage += `- Error Message: ${error.message || 'Not provided'}\n`;

    // Add the full error object for debugging if available
    if (error.error) {
        errorMessage += `- API Error Details: ${JSON.stringify(error.error, null, 2)}\n`;
    }

    return errorMessage;
}

/**
 * Adds common HTTP status code explanations to error messages
 * @param errorMessage The base error message
 * @param error The error object
 * @param context Additional context for specific status codes
 * @returns Enhanced error message with status-specific guidance
 */
export function addCommonErrorGuidance(errorMessage: string, error: any, context?: {
    resource?: string;
    operation?: string;
    requiresAuth?: boolean;
    requiresOwnership?: boolean;
}): string {
    const status = error.status;
    const resource = context?.resource || 'resource';

    if (status === 400) {
        errorMessage += `\nError 400: Bad request - Invalid parameters or malformed request.\n\nCommon causes:\n- Invalid path format (must start with '/')\n- Invalid parameter values\n- Malformed request data\n- Resource doesn't exist or isn't accessible`;
    } else if (status === 401) {
        errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\nCheck:\n- Access token is valid and not expired\n- Token has the required permissions`;
        if (context?.requiresAuth) {
            errorMessage += `\n- Token has the specific scope needed for this operation`;
        }
        errorMessage += `\n- You're authenticated with the correct Dropbox account`;
    } else if (status === 403) {
        errorMessage += `\nError 403: Permission denied - You don't have permission for this operation.\n\nThis could mean:\n- You don't own the ${resource}\n- Your access token lacks required permissions`;
        if (context?.requiresOwnership) {
            errorMessage += `\n- Only the owner can perform this operation`;
        }
        errorMessage += `\n- The ${resource} has restricted access settings`;
    } else if (status === 404) {
        errorMessage += `\nError 404: Not found - The ${resource} doesn't exist.\n\nMake sure:\n- The path is correct and starts with '/'\n- The ${resource} exists in your Dropbox\n- You have access to the ${resource}\n- The ${resource} hasn't been moved or deleted`;
    } else if (status === 409) {
        errorMessage += `\nError 409: Conflict - Operation failed due to a conflict.\n\nCommon causes:\n- Resource already exists\n- Concurrent modifications\n- Operation conflicts with current state\n- Name or path conflicts`;
        
        // Add specific guidance for sharing operations
        if (context?.operation === 'share_file' || context?.operation === 'share_folder') {
            errorMessage += `\n\nFor sharing operations specifically:\n- 'settings_error/not_authorized': Advanced settings (password, expiration) require paid Dropbox accounts\n- 'settings_error/invalid_settings': Check that settings combination is valid for your account type\n- Team-only visibility requires team membership\n- Password protection requires Dropbox Plus/Professional`;
        }
    } else if (status === 429) {
        errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\nTips:\n- Wait a moment before trying again\n- Reduce the frequency of requests\n- Consider batching operations if available`;
    } else if (status === 507) {
        errorMessage += `\nError 507: Insufficient storage - Operation would exceed storage limits.`;
    } else if (status && status >= 500) {
        errorMessage += `\nError ${status}: Server error - Dropbox is experiencing issues.\n\nTry:\n- Waiting a moment and trying again\n- The issue is likely temporary`;
    } else if (status) {
        errorMessage += `\nError ${status}: ${error.message || error.error_summary || 'Unknown error'}`;
    }

    return errorMessage;
}
