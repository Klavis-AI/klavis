import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handler for file request operations
 */
export async function handleFileRequestOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;
    const dropbox = getDropboxClient();

    switch (name) {
        case "create_file_request": {
            const validatedArgs = schemas.CreateFileRequestSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = `Failed to create file request: "${validatedArgs.title}"\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You may not have permission to create file requests or access the destination folder.\n\n💡 This could mean:\n• Your account type doesn't support file requests\n• You don't have write access to the destination folder\n• File requests are disabled for your account`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: Destination folder not found - The path "${validatedArgs.destination}" doesn't exist.\n\n💡 Make sure:\n• The destination folder exists in your Dropbox\n• The path is correct and starts with '/'\n• You have access to the destination folder`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Please check the title and destination path format.\n\n💡 Requirements:\n• Title must be non-empty and unique\n• Destination must be a valid folder path\n• Title should be descriptive and not too long`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - A file request with this title may already exist.\n\n💡 Try:\n• Using a different, unique title\n• Checking existing file requests with 'list_file_requests'\n• Updating an existing file request instead of creating a new one`;
                } else if (error.status === 429) {
                    errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Try:\n• Waiting a moment before creating another file request\n• You may have reached the maximum number of active file requests`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\n💡 Common issues:\n• Check your internet connection\n• Verify your account has file request permissions\n• Ensure the destination folder exists and is accessible`;
                }

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

        case "get_file_request": {
            const validatedArgs = schemas.GetFileRequestSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = `Failed to get file request: ${validatedArgs.id}\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File request not found - The ID "${validatedArgs.id}" doesn't exist or may have been deleted.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to view this file request.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

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

        case "list_file_requests": {
            try {
                schemas.ListFileRequestsSchema.parse(args);
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
            } catch (error: any) {
                let errorMessage = `Failed to list file requests\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to list file requests.`;
                } else if (error.status === 401) {
                    errorMessage += `\nError 401: Unauthorized - Your access token may have expired or be invalid.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

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

        case "delete_file_request": {
            const validatedArgs = schemas.DeleteFileRequestSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = `Failed to delete file request(s): ${validatedArgs.ids.join(', ')}\n`;

                if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - This is usually means:\n` +
                        `• The file request must be closed before it can be deleted\n` +
                        `• The file request may have active uploads\n` +
                        `• You may not have permission to delete this file request\n` +
                        `\nTip: Try closing the file request first, then delete it.`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: File request not found - The ID may be invalid or already deleted.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to delete this file request.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

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

        case "update_file_request": {
            const validatedArgs = schemas.UpdateFileRequestSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = `Failed to update file request: ${validatedArgs.id}\n`;

                if (error.status === 404) {
                    errorMessage += `\nError 404: File request not found - The ID may be invalid.`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to update this file request.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Check that the destination path exists and parameters are valid.`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
                }

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

        default:
            throw new Error(`Unknown file request operation: ${name}`);
    }
}
