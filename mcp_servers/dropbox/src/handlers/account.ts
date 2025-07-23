import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";
import { wrapDropboxError, formatErrorForUser } from '../utils/error-msg.js';
import { DropboxMCPError } from '../error.js';

export async function handleGetCurrentAccount(args: any) {
    schemas.GetCurrentAccountSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.usersGetCurrentAccount();
    const account = response.result;

    return {
        content: [
            {
                type: "text",
                text: `Account: ${(account as any).name?.display_name || 'Unknown'}\nEmail: ${(account as any).email || 'Unknown'}\nAccount ID: ${(account as any).account_id || 'Unknown'}`,
            },
        ],
    };
}

export async function handleGetSpaceUsage(args: any) {
    schemas.GetSpaceUsageSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.usersGetSpaceUsage();
    const spaceInfo = response.result as any;
    let info = `Used: ${spaceInfo.used} bytes`;
    if (spaceInfo.allocation) {
        if (spaceInfo.allocation['.tag'] === 'individual') {
            info += `\nAllocated: ${spaceInfo.allocation.allocated} bytes`;
        } else {
            info += `\nAllocation Type: ${spaceInfo.allocation['.tag']}`;
        }
    }

    return {
        content: [
            {
                type: "text",
                text: info,
            },
        ],
    };
}

export async function handleGetTemporaryLink(args: any) {
    const validatedArgs = schemas.GetTemporaryLinkSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesGetTemporaryLink({
        path: validatedArgs.path,
    });

    return {
        content: [
            {
                type: "text",
                text: `Temporary link: ${response.result.link}`,
            },
        ],
    };
}

export async function handleSaveUrl(args: any) {
    const validatedArgs = schemas.SaveUrlSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesSaveUrl({
        path: validatedArgs.path,
        url: validatedArgs.url,
    });

    if (response.result['.tag'] === 'complete') {
        const metadata = (response.result as any).metadata;
        return {
            content: [
                {
                    type: "text",
                    text: `URL content saved successfully!\n\nFile: ${metadata.name}\nPath: ${metadata.path_display}\nSize: ${metadata.size} bytes\nModified: ${metadata.client_modified}\n\nSource URL: ${validatedArgs.url}`,
                },
            ],
        };
    } else if (response.result['.tag'] === 'async_job_id') {
        const jobId = (response.result as any).async_job_id;
        return {
            content: [
                {
                    type: "text",
                    text: `URL download started (large file detected)\n\nTarget: ${validatedArgs.path}\nSource: ${validatedArgs.url}\nJob ID: ${jobId}\n\nUse 'save_url_check_job_status' with this job ID to monitor progress.`,
                },
            ],
        };
    } else {
        return {
            content: [
                {
                    type: "text",
                    text: `Unexpected response from save URL operation\n\nTarget: ${validatedArgs.path}\nSource: ${validatedArgs.url}\nResponse: ${JSON.stringify(response.result, null, 2)}`,
                },
            ],
        };
    }
}

export async function handleSaveUrlCheckJobStatus(args: any) {
    const validatedArgs = schemas.SaveUrlCheckJobStatusSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesSaveUrlCheckJobStatus({
        async_job_id: validatedArgs.async_job_id,
    });

    if (response.result['.tag'] === 'complete') {
        const metadata = (response.result as any).metadata;
        const fileName = metadata?.name || 'Unknown file';
        const filePath = metadata?.path_display || 'Unknown path';
        const fileSize = metadata?.size || 'Unknown size';
        const modified = metadata?.client_modified || metadata?.server_modified || 'Unknown date';

        return {
            content: [
                {
                    type: "text",
                    text: `URL download completed successfully!

File: ${fileName}
Path: ${filePath}
Size: ${fileSize} bytes
Modified: ${modified}

Job ID: ${validatedArgs.async_job_id}`,
                },
            ],
        };
    } else if (response.result['.tag'] === 'in_progress') {
        return {
            content: [
                {
                    type: "text",
                    text: `URL download is still in progress...

Job ID: ${validatedArgs.async_job_id}

Please wait and check again in a few moments.`,
                },
            ],
        };
    } else if (response.result['.tag'] === 'failed') {
        const failureReason = (response.result as any).reason || 'Unknown error';
        return {
            content: [
                {
                    type: "text",
                    text: `URL download failed

Job ID: ${validatedArgs.async_job_id}
Reason: ${failureReason}

Common failure reasons:
- URL became inaccessible
- Network timeout
- File size too large
- Content type not supported`,
                },
            ],
        };
    } else {
        return {
            content: [
                {
                    type: "text",
                    text: `Unknown job status: ${response.result['.tag']}

Job ID: ${validatedArgs.async_job_id}`,
                },
            ],
        };
    }
}

/**
 * Main handler for account operations
 */
export async function handleAccountOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case "get_current_account":
                return await handleGetCurrentAccount(args) as CallToolResult;
            case "get_space_usage":
                return await handleGetSpaceUsage(args) as CallToolResult;
            case "get_temporary_link":
                return await handleGetTemporaryLink(args) as CallToolResult;
            case "save_url":
                return await handleSaveUrl(args) as CallToolResult;
            case "save_url_check_job_status":
                return await handleSaveUrlCheckJobStatus(args) as CallToolResult;
            default:
                throw new Error(`Unknown account operation: ${name}`);
        }
    } catch (error: unknown) {
        // Handle Dropbox API errors by wrapping them first if needed
        if (!(error instanceof DropboxMCPError)) {
            // If it's not already a wrapped error, wrap it
            const operationMessage = `Failed to perform account operation: ${name}`;
            wrapDropboxError(error, operationMessage);
        }

        // Format the error for user display
        const errorMessage = formatErrorForUser(error);
        return {
            content: [
                {
                    type: "text",
                    text: errorMessage,
                },
            ],
        };
    }
}
