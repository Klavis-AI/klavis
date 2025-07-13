import { getDropboxClient } from '../utils/context.js';
import {
    ListFolderSchema,
    ListFolderContinueSchema,
    CreateFolderSchema,
    DeleteFileSchema,
    MoveFileSchema,
    CopyFileSchema,
    GetFileInfoSchema,
    SearchFilesSchema
} from '../schemas/index.js';
import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export async function handleListFolder(args: any) {
    const validatedArgs = ListFolderSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesListFolder({
            path: validatedArgs.path,
            recursive: validatedArgs.recursive,
            include_media_info: validatedArgs.include_media_info,
            include_deleted: validatedArgs.include_deleted,
            include_has_explicit_shared_members: validatedArgs.include_has_explicit_shared_members,
            limit: validatedArgs.limit,
        });

        const entries = response.result.entries.map((entry: any) => {
            if (entry['.tag'] === 'file') {
                return `File: ${entry.name} (${entry.path_display}) - Size: ${entry.size} bytes, Modified: ${entry.server_modified}`;
            } else if (entry['.tag'] === 'folder') {
                return `Folder: ${entry.name} (${entry.path_display})`;
            } else {
                return `${entry['.tag']}: ${entry.name} (${entry.path_display})`;
            }
        });

        let resultText = `Contents of folder "${validatedArgs.path || '/'}":\n\n${entries.join('\n') || 'Empty folder'}`;

        // Add pagination info if there are more results
        if (response.result.has_more) {
            resultText += `\n\n📄 More results available. Use 'list_folder_continue' with cursor: ${response.result.cursor}`;
        }

        return {
            content: [
                {
                    type: "text",
                    text: resultText,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to list folder: "${validatedArgs.path || '/'}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: Folder not found - The path "${validatedArgs.path || '/'}" doesn't exist.\n\n💡 Make sure:\n• The folder path starts with '/'\n• The folder exists in your Dropbox\n• You have access to the folder\n• Check spelling and case sensitivity`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied - You don't have permission to access this folder.\n\n💡 This could mean:\n• The folder is in a shared space you don't have access to\n• The folder requires special permissions\n• Your access token may have insufficient scope`;
        } else if (error.status === 400) {
            errorMessage += `\nError 400: Invalid request - Check the folder path format.\n\n💡 Path requirements:\n• Must start with '/' (e.g., '/Documents')\n• Use forward slashes (/) not backslashes (\\)\n• Avoid special characters that aren't URL-safe\n• Empty string or '/' for root folder`;
        } else if (error.status === 401) {
            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.metadata.read' permission\n• You're authenticated with the correct Dropbox account`;
        } else if (error.status === 429) {
            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Try:\n• Waiting a moment before retrying\n• Reducing the frequency of requests\n• Using recursive=false for large folders`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\n💡 General troubleshooting:\n• Check your internet connection\n• Verify the folder path exists\n• Ensure proper authentication`;
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

export async function handleListFolderContinue(args: any) {
    const validatedArgs = ListFolderContinueSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesListFolderContinue({
            cursor: validatedArgs.cursor,
        });

        const entries = response.result.entries.map((entry: any) => {
            if (entry['.tag'] === 'file') {
                return `File: ${entry.name} (${entry.path_display}) - Size: ${entry.size} bytes, Modified: ${entry.server_modified}`;
            } else if (entry['.tag'] === 'folder') {
                return `Folder: ${entry.name} (${entry.path_display})`;
            } else {
                return `${entry['.tag']}: ${entry.name} (${entry.path_display})`;
            }
        });

        let resultText = `Continued folder contents:\n\n${entries.join('\n') || 'No more items'}`;

        // Add pagination info if there are more results
        if (response.result.has_more) {
            resultText += `\n\n📄 More results available. Use 'list_folder_continue' with cursor: ${response.result.cursor}`;
        } else {
            resultText += `\n\n✅ End of folder contents reached.`;
        }

        return {
            content: [
                {
                    type: "text",
                    text: resultText,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to continue listing folder contents\n`;

        if (error.status === 400) {
            errorMessage += `\nError 400: Invalid cursor - The cursor may be expired or malformed.\n\n💡 Tips:\n• Use a fresh cursor from a recent list_folder call\n• Cursors have a limited lifetime\n• Don't modify cursor strings`;
        } else if (error.status === 401) {
            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.metadata.read' permission`;
        } else if (error.status === 429) {
            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Try:\n• Waiting a moment before retrying\n• Reducing the frequency of requests`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\n💡 General troubleshooting:\n• Check your internet connection\n• Use a valid cursor from list_folder\n• Ensure proper authentication`;
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

export async function handleCreateFolder(args: any) {
    const validatedArgs = CreateFolderSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesCreateFolderV2({
            path: validatedArgs.path,
            autorename: validatedArgs.autorename,
        });

        return {
            content: [
                {
                    type: "text",
                    text: `Folder created successfully: ${response.result.metadata.path_display}`,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to create folder: "${validatedArgs.path}"\n`;

        if (error.status === 409) {
            errorMessage += `\nError 409: Folder already exists or conflict.\n\n💡 Solutions:\n• Set 'autorename: true' to automatically rename if folder exists\n• Choose a different folder name\n• Check if a file with the same name exists`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied - You don't have permission to create folders here.\n\n💡 This could mean:\n• You don't have write access to the parent folder\n• The parent folder is read-only\n• Your access token lacks 'files.content.write' permission`;
        } else if (error.status === 400) {
            errorMessage += `\nError 400: Invalid path - Check the folder path format.\n\n💡 Path requirements:\n• Must start with '/' (e.g., '/Documents/NewFolder')\n• Cannot end with '/'\n• Use forward slashes (/) not backslashes (\\)\n• Avoid invalid characters: < > : " | ? * \\`;
        } else if (error.status === 401) {
            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.content.write' permission`;
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

export async function handleDeleteFile(args: any) {
    const validatedArgs = DeleteFileSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesDeleteV2({
            path: validatedArgs.path,
        });

        return {
            content: [
                {
                    type: "text",
                    text: `File/folder deleted successfully: ${response.result.metadata.path_display}`,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to delete: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File or folder not found.\n\n💡 Make sure:\n• The path is correct and starts with '/'\n• The file/folder exists\n• Check spelling and case sensitivity`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 This could mean:\n• You don't own the file/folder\n• The file is shared and you don't have delete permissions\n• Your access token lacks sufficient permissions`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: Cannot delete - File may be in use or there's a conflict.\n\n💡 Try:\n• Closing any applications using the file\n• Waiting a moment and trying again\n• Checking if the file is locked`;
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

export async function handleMoveFile(args: any) {
    const validatedArgs = MoveFileSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesMoveV2({
        from_path: validatedArgs.from_path,
        to_path: validatedArgs.to_path,
        allow_shared_folder: validatedArgs.allow_shared_folder,
        autorename: validatedArgs.autorename,
        allow_ownership_transfer: validatedArgs.allow_ownership_transfer,
    });

    return {
        content: [
            {
                type: "text",
                text: `File/folder moved from "${validatedArgs.from_path}" to "${response.result.metadata.path_display}"`,
            },
        ],
    };
}

export async function handleCopyFile(args: any) {
    const validatedArgs = CopyFileSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesCopyV2({
        from_path: validatedArgs.from_path,
        to_path: validatedArgs.to_path,
        allow_shared_folder: validatedArgs.allow_shared_folder,
        autorename: validatedArgs.autorename,
        allow_ownership_transfer: validatedArgs.allow_ownership_transfer,
    });

    return {
        content: [
            {
                type: "text",
                text: `File/folder copied from "${validatedArgs.from_path}" to "${response.result.metadata.path_display}"`,
            },
        ],
    };
}

export async function handleSearchFiles(args: any) {
    const validatedArgs = SearchFilesSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesSearchV2({
            query: validatedArgs.query,
            options: {
                path: validatedArgs.path,
                max_results: validatedArgs.max_results,
                file_status: validatedArgs.file_status as any, // Type assertion for compatibility
                filename_only: validatedArgs.filename_only,
            },
        });

        const matches = response.result.matches?.map((match: any) => {
            const metadata = match.metadata.metadata;
            if (metadata['.tag'] === 'file') {
                return `File: ${metadata.name} (${metadata.path_display}) - Size: ${metadata.size} bytes`;
            } else if (metadata['.tag'] === 'folder') {
                return `Folder: ${metadata.name} (${metadata.path_display})`;
            } else {
                return `${metadata['.tag']}: ${metadata.name} (${metadata.path_display})`;
            }
        }) || [];

        let resultText = `Search results for "${validatedArgs.query}"`;
        if (validatedArgs.path) {
            resultText += ` in "${validatedArgs.path}"`;
        }
        resultText += `:\n\n${matches.join('\n') || 'No results found'}`;

        // Add more results info
        if (response.result.has_more) {
            resultText += `\n\n📄 More results available. Showing first ${matches.length} results.`;
        }

        return {
            content: [
                {
                    type: "text",
                    text: resultText,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to search for: "${validatedArgs.query}"\n`;

        if (error.status === 400) {
            errorMessage += `\nError 400: Invalid search query.\n\n💡 Tips:\n• Use simple keywords or phrases\n• Avoid very short search terms (less than 3 characters)\n• Check the search path format`;
        } else if (error.status === 429) {
            errorMessage += `\nError 429: Too many requests.\n\n💡 Try:\n• Waiting a moment before searching again\n• Using more specific search terms\n• Reducing search frequency`;
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

export async function handleGetFileInfo(args: any) {
    const validatedArgs = GetFileInfoSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesGetMetadata({
            path: validatedArgs.path,
            include_media_info: validatedArgs.include_media_info,
            include_deleted: validatedArgs.include_deleted,
            include_has_explicit_shared_members: validatedArgs.include_has_explicit_shared_members,
        });

        const metadata = response.result;
        let info = `Name: ${metadata.name}\nPath: ${metadata.path_display}`;

        if (metadata['.tag'] === 'file') {
            info += `\nType: File\nSize: ${(metadata as any).size} bytes\nLast Modified: ${(metadata as any).server_modified}`;
            if ((metadata as any).content_hash) {
                info += `\nContent Hash: ${(metadata as any).content_hash}`;
            }
        } else if (metadata['.tag'] === 'folder') {
            info += `\nType: Folder`;
            if ((metadata as any).shared_folder_id) {
                info += `\nShared Folder ID: ${(metadata as any).shared_folder_id}`;
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
    } catch (error: any) {
        let errorMessage = `Failed to get information for: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File or folder not found.\n\n💡 Make sure:\n• The path is correct and starts with '/'\n• The file/folder exists\n• You have access to the file/folder`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 You may not have access to this file/folder`;
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

/**
 * Main handler for file management operations
 */
export async function handleFilesOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "list_folder":
            return await handleListFolder(args) as CallToolResult;
        case "list_folder_continue":
            return await handleListFolderContinue(args) as CallToolResult;
        case "create_folder":
            return await handleCreateFolder(args) as CallToolResult;
        case "delete_file":
            return await handleDeleteFile(args) as CallToolResult;
        case "move_file":
            return await handleMoveFile(args) as CallToolResult;
        case "copy_file":
            return await handleCopyFile(args) as CallToolResult;
        case "search_files":
            return await handleSearchFiles(args) as CallToolResult;
        case "get_file_info":
            return await handleGetFileInfo(args) as CallToolResult;
        default:
            throw new Error(`Unknown files operation: ${name}`);
    }
}
