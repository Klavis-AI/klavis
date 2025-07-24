import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";
import { wrapDropboxError } from '../utils/error-msg.js';

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
            default:
                throw new Error(`Unknown account operation: ${name}`);
        }
    } catch (error: unknown) {
        // Handle Dropbox API errors by wrapping them first if needed
        const operationMessage = `Failed to perform account operation: ${name}`;
        wrapDropboxError(error, operationMessage);
    }
}
