import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handle create file request operation
 */
async function handleCreateFileRequest(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.CreateFileRequestSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.fileRequestsCreate({
        title: validatedArgs.title,
        destination: validatedArgs.destination,
        description: validatedArgs.description,
    });

    const fileRequest = response.result;
    return {
        content: [
            {
                type: "text",
                text: `File request created successfully!\nID: ${fileRequest.id}\nTitle: ${fileRequest.title}\nURL: ${fileRequest.url}\nDestination: ${fileRequest.destination}${fileRequest.description ? `\nDescription: ${fileRequest.description}` : ''}`,
            },
        ],
    };
}

/**
 * Handle get file request operation
 */
async function handleGetFileRequest(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.GetFileRequestSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.fileRequestsGet({
        id: validatedArgs.id,
    });

    const fileRequest = response.result;
    let info = `ID: ${fileRequest.id}\nTitle: ${fileRequest.title}\nDestination: ${fileRequest.destination}\nFile Count: ${fileRequest.file_count}\nURL: ${fileRequest.url}`;

    if (fileRequest.deadline) {
        info += `\nDeadline: ${fileRequest.deadline.deadline}`;
    }
    if (fileRequest.description) {
        info += `\nDescription: ${fileRequest.description}`;
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
 * Handle list file requests operation
 */
async function handleListFileRequests(args: any): Promise<CallToolResult> {
    schemas.ListFileRequestsSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.fileRequestsList();

    const fileRequests = response.result.file_requests.map((request: any) =>
        `ID: ${request.id} - Title: ${request.title} - Destination: ${request.destination} - File Count: ${request.file_count} - Status: ${request.is_open ? 'Open' : 'Closed'}`
    );

    return {
        content: [
            {
                type: "text",
                text: `File requests:\n\n${fileRequests.join('\n') || 'No file requests found'}`,
            },
        ],
    };
}

/**
 * Handle delete file request operation
 */
async function handleDeleteFileRequest(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.DeleteFileRequestSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.fileRequestsDelete({
        ids: validatedArgs.ids,
    });

    return {
        content: [
            {
                type: "text",
                text: `File request(s) deleted successfully: ${validatedArgs.ids.join(', ')}`,
            },
        ],
    };
}

/**
 * Handle update file request operation
 */
async function handleUpdateFileRequest(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.UpdateFileRequestSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.fileRequestsUpdate({
        id: validatedArgs.id,
        title: validatedArgs.title,
        destination: validatedArgs.destination,
        description: validatedArgs.description,
        open: validatedArgs.open,
    });

    const request = response.result;
    let statusMessage = `File request updated successfully:\n`;
    statusMessage += `ID: ${request.id}\n`;
    statusMessage += `Title: ${request.title}\n`;
    statusMessage += `Destination: ${request.destination}\n`;
    if (request.description) {
        statusMessage += `Description: ${request.description}\n`;
    }
    statusMessage += `Status: ${request.is_open ? 'Open' : 'Closed'}\n`;
    statusMessage += `File Count: ${request.file_count}`;

    return {
        content: [
            {
                type: "text",
                text: statusMessage,
            },
        ],
    };
}

/**
 * Handler for file request operations
 */
export async function handleFileRequestOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "dropbox_create_file_request":
            return await handleCreateFileRequest(args);

        case "dropbox_get_file_request":
            return await handleGetFileRequest(args);

        case "dropbox_list_file_requests":
            return await handleListFileRequests(args);

        case "dropbox_delete_file_request":
            return await handleDeleteFileRequest(args);

        case "dropbox_update_file_request":
            return await handleUpdateFileRequest(args);

        default:
            throw new Error(`Unknown file request operation: ${name}`);
    }
}
