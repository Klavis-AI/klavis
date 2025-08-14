import { getDropboxClient } from '../utils/context.js';
import {
    ListFolderSchema,
    ListFolderContinueSchema,
    CreateFolderSchema,
    DeleteFileSchema,
    MoveFileSchema,
    CopyFileSchema,
    GetFileInfoSchema,
    SearchFilesSchema,
    SearchFilesContinueSchema
} from '../schemas/index.js';
import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";

/**
 * Handle list folder operation
 */
async function handleListFolder(args: any): Promise<CallToolResult> {
    const validatedArgs = ListFolderSchema.parse(args);
    const dropbox = getDropboxClient();

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
        resultText += `\n\nMore results available. Use 'list_folder_continue' with cursor: ${response.result.cursor}`;
    }

    return {
        content: [
            {
                type: "text",
                text: resultText,
            },
        ],
    };
}

/**
 * Handle list folder continue operation
 */
async function handleListFolderContinue(args: any): Promise<CallToolResult> {
    const validatedArgs = ListFolderContinueSchema.parse(args);
    const dropbox = getDropboxClient();

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
        resultText += `\n\nMore results available. Use 'list_folder_continue' with cursor: ${response.result.cursor}`;
    } else {
        resultText += `\n\nEnd of folder contents reached.`;
    }

    return {
        content: [
            {
                type: "text",
                text: resultText,
            },
        ],
    };
}

/**
 * Handle create folder operation
 */
async function handleCreateFolder(args: any): Promise<CallToolResult> {
    const validatedArgs = CreateFolderSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

/**
 * Handle delete file operation
 */
async function handleDeleteFile(args: any): Promise<CallToolResult> {
    const validatedArgs = DeleteFileSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

/**
 * Handle move file operation
 */
async function handleMoveFile(args: any): Promise<CallToolResult> {
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

/**
 * Handle copy file operation
 */
async function handleCopyFile(args: any): Promise<CallToolResult> {
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

/**
 * Handle search files operation
 */
async function handleSearchFiles(args: any): Promise<CallToolResult> {
    const validatedArgs = SearchFilesSchema.parse(args);
    const dropbox = getDropboxClient();

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
        resultText += `\n\nMore results available. Showing first ${matches.length} results.`;
        resultText += `\nUse 'search_files_continue' with cursor: ${response.result.cursor}`;
    }

    return {
        content: [
            {
                type: "text",
                text: resultText,
            },
        ],
    };
}

/**
 * Handle search files continue operation
 */
async function handleSearchFilesContinue(args: any): Promise<CallToolResult> {
    const validatedArgs = SearchFilesContinueSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesSearchContinueV2({
        cursor: validatedArgs.cursor,
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

    let resultText = `Search results (continued):\n\n${matches.join('\n') || 'No more results found'}`;

    // Add more results info
    if (response.result.has_more) {
        resultText += `\n\nMore results available. Use 'search_files_continue' with cursor: ${response.result.cursor}`;
    }

    return {
        content: [
            {
                type: "text",
                text: resultText,
            },
        ],
    };
}

/**
 * Handle get file info operation
 */
async function handleGetFileInfo(args: any): Promise<CallToolResult> {
    const validatedArgs = GetFileInfoSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

/**
 * Main handler for file management operations
 */
export async function handleFilesOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "dropbox_list_folder":
            return await handleListFolder(args);
        case "dropbox_list_folder_continue":
            return await handleListFolderContinue(args);
        case "dropbox_create_folder":
            return await handleCreateFolder(args);
        case "dropbox_delete_file":
            return await handleDeleteFile(args);
        case "dropbox_move_file":
            return await handleMoveFile(args);
        case "dropbox_copy_file":
            return await handleCopyFile(args);
        case "dropbox_search_files":
            return await handleSearchFiles(args);
        case "dropbox_search_files_continue":
            return await handleSearchFilesContinue(args);
        case "dropbox_get_file_info":
            return await handleGetFileInfo(args);
        default:
            throw new Error(`Unknown files operation: ${name}`);
    }
}
