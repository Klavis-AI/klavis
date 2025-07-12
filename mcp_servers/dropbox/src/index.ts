#!/usr/bin/env node

import express, { Request, Response } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { zodToJsonSchema } from "zod-to-json-schema";
import { AsyncLocalStorage } from 'async_hooks';
import { Dropbox } from 'dropbox';

// Polyfill for fetch Response.buffer() method - fixes compatibility with modern Node.js/Bun
// This addresses the same issue fixed in https://github.com/dropbox/dropbox-sdk-js/pull/1138
function patchFetchResponse() {
    const originalFetch = global.fetch;
    if (originalFetch) {
        global.fetch = async function(...args: Parameters<typeof fetch>) {
            const response = await originalFetch.apply(this, args);
            
            // Add buffer() method if it doesn't exist (for compatibility with Dropbox SDK)
            if (!('buffer' in response) && typeof response.arrayBuffer === 'function') {
                (response as any).buffer = function() {
                    return this.arrayBuffer().then((data: ArrayBuffer) => Buffer.from(data));
                };
            }
            
            return response;
        };
    }
}

// Apply the patch immediately
patchFetchResponse();

// Create AsyncLocalStorage for request context
const asyncLocalStorage = new AsyncLocalStorage<{
    dropboxClient: Dropbox;
}>();

// Helper function to get Dropbox client from context
function getDropboxClient() {
    return asyncLocalStorage.getStore()!.dropboxClient;
}

// Schema definitions
const ListFolderSchema = z.object({
    path: z.string().optional().default("").describe("Path of the folder to list (empty string for root)"),
    recursive: z.boolean().optional().default(false).describe("Whether to list contents recursively"),
    include_media_info: z.boolean().optional().default(false).describe("Include media info for photos and videos"),
    include_deleted: z.boolean().optional().default(false).describe("Include deleted files"),
    include_has_explicit_shared_members: z.boolean().optional().default(false).describe("Include shared member info"),
    limit: z.number().optional().describe("Maximum number of results to return"),
});

const ListFolderContinueSchema = z.object({
    cursor: z.string().describe("Cursor from previous list_folder operation to continue listing"),
});

const CreateFolderSchema = z.object({
    path: z.string().describe("Path of the folder to create"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename folder if it already exists"),
});

const DeleteFileSchema = z.object({
    path: z.string().describe("Path of the file or folder to delete"),
});

const MoveFileSchema = z.object({
    from_path: z.string().describe("Current path of the file or folder"),
    to_path: z.string().describe("New path for the file or folder"),
    allow_shared_folder: z.boolean().optional().default(false).describe("Allow moving shared folders"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

const CopyFileSchema = z.object({
    from_path: z.string().describe("Path of the file or folder to copy"),
    to_path: z.string().describe("Destination path for the copy"),
    allow_shared_folder: z.boolean().optional().default(false).describe("Allow copying shared folders"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

const SearchFilesSchema = z.object({
    query: z.string().describe("Search query for finding files"),
    path: z.string().optional().default("").describe("Path to search within (empty for entire Dropbox)"),
    max_results: z.number().optional().default(100).describe("Maximum number of search results"),
    file_status: z.enum(['active', 'deleted']).optional().default('active').describe("File status to search for"),
    filename_only: z.boolean().optional().default(false).describe("Search only in filenames"),
});

const GetFileInfoSchema = z.object({
    path: z.string().describe("Path of the file to get information about"),
    include_media_info: z.boolean().optional().default(false).describe("Include media info for photos and videos"),
    include_deleted: z.boolean().optional().default(false).describe("Include deleted files"),
    include_has_explicit_shared_members: z.boolean().optional().default(false).describe("Include shared member info"),
});

const ShareFileSchema = z.object({
    path: z.string().describe("Path of the file or folder to share"),
    settings: z.object({
        requested_visibility: z.enum(['public', 'team_only', 'password']).optional().describe("Link visibility"),
        link_password: z.string().optional().describe("Password for password-protected links"),
        expires: z.string().optional().describe("Expiration date (ISO 8601 format)"),
    }).optional().describe("Share settings"),
});

const GetSharedLinksSchema = z.object({
    path: z.string().optional().describe("Path to get shared links for (omit for all links)"),
    cursor: z.string().optional().describe("Cursor for pagination"),
});

const UploadFileSchema = z.object({
    path: z.string().describe("Path where the file should be uploaded (e.g., '/folder/filename.txt')"),
    text_content: z.string().optional().describe("File content as plain text (for text files)"),
    base64_content: z.string().optional().describe("File content as base64 encoded data (for binary files or when content is already base64 encoded)"),
    mode: z.enum(['add', 'overwrite', 'update']).optional().default('add').describe("Upload mode"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename file if it already exists"),
    mute: z.boolean().optional().default(false).describe("Suppress notifications"),
}).refine(
    (data) => !!(data.text_content || data.base64_content),
    {
        message: "Either text_content or base64_content must be provided",
        path: ["content"],
    }
).refine(
    (data) => !(data.text_content && data.base64_content),
    {
        message: "Only one of text_content or base64_content should be provided, not both",
        path: ["content"],
    }
);

const DownloadFileSchema = z.object({
    path: z.string().describe("Path of the file to download"),
});

const ListRevisionsSchema = z.object({
    path: z.string().describe("Path of the file to get revisions for"),
    mode: z.enum(['path', 'id']).optional().default('path').describe("How to interpret the path"),
    limit: z.number().optional().default(10).describe("Maximum number of revisions to return"),
});

const RestoreFileSchema = z.object({
    path: z.string().describe("Path of the file to restore"),
    rev: z.string().describe("Revision ID to restore to"),
});

const GetCurrentAccountSchema = z.object({});

const GetSpaceUsageSchema = z.object({});

const GetTemporaryLinkSchema = z.object({
    path: z.string().describe("Path of the file to get temporary link for"),
});

const GetPreviewSchema = z.object({
    path: z.string().describe("Path of the file to get preview for"),
});

const AddFileMemberSchema = z.object({
    file: z.string().describe("Path of the file to add member to"),
    members: z.array(z.object({
        email: z.string().describe("Email address of the member"),
        access_level: z.enum(['viewer', 'editor']).optional().default('viewer').describe("Access level for the member"),
    })).describe("List of members to add"),
    quiet: z.boolean().optional().default(false).describe("Whether to suppress notifications"),
    custom_message: z.string().optional().describe("Custom message to include in the invitation"),
});

const ListFileMembersSchema = z.object({
    file: z.string().describe("Path of the file to list members for"),
    include_inherited: z.boolean().optional().default(true).describe("Include inherited permissions"),
    limit: z.number().optional().default(100).describe("Maximum number of members to return"),
});

const RemoveFileMemberSchema = z.object({
    file: z.string().describe("Path of the file to remove member from"),
    member: z.string().describe("Email address of the member to remove"),
});

const ShareFolderSchema = z.object({
    path: z.string().describe("Path of the folder to share"),
    member_policy: z.enum(['team', 'anyone']).optional().default('anyone').describe("Who can be a member of this shared folder"),
    acl_update_policy: z.enum(['owner', 'editors']).optional().default('owner').describe("Who can add and remove members"),
    shared_link_policy: z.enum(['anyone', 'members']).optional().default('anyone').describe("Who can access the shared link"),
    force_async: z.boolean().optional().default(false).describe("Force asynchronous processing"),
});

const ListFolderMembersSchema = z.object({
    shared_folder_id: z.string().describe("ID of the shared folder"),
    limit: z.number().optional().default(100).describe("Maximum number of members to return"),
});

const AddFolderMemberSchema = z.object({
    shared_folder_id: z.string().describe("ID of the shared folder"),
    members: z.array(z.object({
        email: z.string().describe("Email address of the member"),
        access_level: z.enum(['viewer', 'editor', 'owner']).optional().default('viewer').describe("Access level for the member"),
    })).describe("List of members to add"),
    quiet: z.boolean().optional().default(false).describe("Whether to suppress notifications"),
    custom_message: z.string().optional().describe("Custom message to include in the invitation"),
});

// File Requests Schemas
const CreateFileRequestSchema = z.object({
    title: z.string().describe("The title of the file request"),
    destination: z.string().describe("The path of the folder where uploaded files will be sent"),
    description: z.string().optional().describe("Description of the file request"),
});

const GetFileRequestSchema = z.object({
    id: z.string().describe("The ID of the file request"),
});

const ListFileRequestsSchema = z.object({});

const DeleteFileRequestSchema = z.object({
    ids: z.array(z.string()).describe("List of file request IDs to delete"),
});

const UpdateFileRequestSchema = z.object({
    id: z.string().describe("The ID of the file request to update"),
    title: z.string().optional().describe("New title for the file request"),
    destination: z.string().optional().describe("New destination path for the file request"),
    description: z.string().optional().describe("New description for the file request"),
    open: z.boolean().optional().describe("Whether to open (true) or close (false) the file request"),
});

// Batch Operations Schemas
const BatchDeleteSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file or folder to delete"),
    })).describe("List of files/folders to delete (up to 1000 entries)"),
});

const BatchMoveSchema = z.object({
    entries: z.array(z.object({
        from_path: z.string().describe("Current path of the file or folder"),
        to_path: z.string().describe("New path for the file or folder"),
    })).describe("List of move operations to perform (up to 1000 entries)"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

const BatchCopySchema = z.object({
    entries: z.array(z.object({
        from_path: z.string().describe("Path of the file or folder to copy"),
        to_path: z.string().describe("Destination path for the copy"),
    })).describe("List of copy operations to perform (up to 1000 entries)"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
});

// Batch Job Status Check Schema
const BatchJobStatusSchema = z.object({
    async_job_id: z.string().describe("The async job ID returned from a batch operation"),
});

// Thumbnail Schema
const GetThumbnailSchema = z.object({
    path: z.string().describe("Path of the file to get thumbnail for"),
    format: z.enum(["jpeg", "png"]).optional().default("jpeg").describe("Image format for the thumbnail"),
    size: z.enum(["w32h32", "w64h64", "w128h128", "w256h256", "w480h320", "w640h480", "w960h640", "w1024h768", "w2048h1536"]).optional().default("w256h256").describe("Size of the thumbnail"),
});

// File Properties Schemas
const AddFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to add properties to"),
    property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).describe("List of property fields"),
    })).describe("List of property groups to add"),
});

const OverwriteFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to overwrite properties for"),
    property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).describe("List of property fields"),
    })).describe("List of property groups to overwrite"),
});

const UpdateFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to update properties for"),
    update_property_groups: z.array(z.object({
        template_id: z.string().describe("Template ID for the property group"),
        add_or_update_fields: z.array(z.object({
            name: z.string().describe("Property field name"),
            value: z.string().describe("Property field value"),
        })).optional().describe("Fields to add or update"),
        remove_fields: z.array(z.string()).optional().describe("Field names to remove"),
    })).describe("List of property group updates"),
});

const RemoveFilePropertiesSchema = z.object({
    path: z.string().describe("Path of the file to remove properties from"),
    property_template_ids: z.array(z.string()).describe("List of property template IDs to remove"),
});

const SearchFilePropertiesSchema = z.object({
    queries: z.array(z.object({
        query: z.string().describe("Search query for property values"),
        mode: z.enum(['field_name', 'field_value']).describe("Whether to search in field names or values"),
        logical_operator: z.enum(['or_operator']).optional().describe("Logical operator for multiple queries"),
    })).describe("List of search queries"),
    template_filter: z.enum(['filter_none', 'filter_some']).optional().default('filter_none').describe("Template filter mode"),
});

// Property Template Management Schemas
const ListPropertyTemplatesSchema = z.object({});

const GetPropertyTemplateSchema = z.object({
    template_id: z.string().describe("ID of the property template to retrieve"),
});

// Save URL Schemas  
const SaveUrlSchema = z.object({
    path: z.string().describe("Path where the file should be saved (e.g., '/folder/filename.ext')"),
    url: z.string().describe("URL to download and save to Dropbox"),
});

const SaveUrlCheckJobStatusSchema = z.object({
    async_job_id: z.string().describe("The async job ID returned from save_url operation"),
});

// File Locking Schemas
const LockFileBatchSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file to lock"),
    })).describe("List of files to lock (up to 1000 entries)"),
});

const UnlockFileBatchSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file to unlock"),
    })).describe("List of files to unlock (up to 1000 entries)"),
});

// Get Dropbox MCP Server
const getDropboxMcpServer = () => {
    // Server implementation
    const server = new Server({
        name: "dropbox",
        version: "1.0.0",
    }, {
        capabilities: {
            tools: {},
        },
    });

    // Tool handlers
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
        tools: [
            {
                name: "list_folder",
                description: "Lists the contents of a folder",
                inputSchema: zodToJsonSchema(ListFolderSchema),
            },
            {
                name: "list_folder_continue",
                description: "Continues listing folder contents using a cursor from previous list_folder operation",
                inputSchema: zodToJsonSchema(ListFolderContinueSchema),
            },
            {
                name: "create_folder",
                description: "Creates a new folder",
                inputSchema: zodToJsonSchema(CreateFolderSchema),
            },
            {
                name: "delete_file",
                description: "Deletes a file or folder",
                inputSchema: zodToJsonSchema(DeleteFileSchema),
            },
            {
                name: "move_file",
                description: "Moves or renames a file or folder",
                inputSchema: zodToJsonSchema(MoveFileSchema),
            },
            {
                name: "copy_file",
                description: "Creates a copy of a file or folder",
                inputSchema: zodToJsonSchema(CopyFileSchema),
            },
            {
                name: "search_files",
                description: "Searches for files and folders",
                inputSchema: zodToJsonSchema(SearchFilesSchema),
            },
            {
                name: "get_file_info",
                description: "Gets metadata information about a file or folder",
                inputSchema: zodToJsonSchema(GetFileInfoSchema),
            },
            {
                name: "share_file",
                description: "Creates a shared link for a file or folder",
                inputSchema: zodToJsonSchema(ShareFileSchema),
            },
            {
                name: "get_shared_links",
                description: "Lists shared links for files and folders",
                inputSchema: zodToJsonSchema(GetSharedLinksSchema),
            },
            {
                name: "upload_file",
                description: "Uploads a file to Dropbox",
                inputSchema: zodToJsonSchema(UploadFileSchema),
            },
            {
                name: "download_file",
                description: "Downloads a file from Dropbox",
                inputSchema: zodToJsonSchema(DownloadFileSchema),
            },
            {
                name: "list_revisions",
                description: "Lists the revisions of a file",
                inputSchema: zodToJsonSchema(ListRevisionsSchema),
            },
            {
                name: "restore_file",
                description: "Restores a file to a previous revision",
                inputSchema: zodToJsonSchema(RestoreFileSchema),
            },
            {
                name: "get_current_account",
                description: "Gets information about the current account",
                inputSchema: zodToJsonSchema(GetCurrentAccountSchema),
            },
            {
                name: "get_space_usage",
                description: "Gets the current space usage information",
                inputSchema: zodToJsonSchema(GetSpaceUsageSchema),
            },
            {
                name: "get_temporary_link",
                description: "Gets a temporary link to a file",
                inputSchema: zodToJsonSchema(GetTemporaryLinkSchema),
            },
            {
                name: "get_preview",
                description: "Gets a preview of a file",
                inputSchema: zodToJsonSchema(GetPreviewSchema),
            },
            {
                name: "add_file_member",
                description: "Adds a member to a file",
                inputSchema: zodToJsonSchema(AddFileMemberSchema),
            },
            {
                name: "list_file_members",
                description: "Lists the members of a file",
                inputSchema: zodToJsonSchema(ListFileMembersSchema),
            },
            {
                name: "remove_file_member",
                description: "Removes a member from a file",
                inputSchema: zodToJsonSchema(RemoveFileMemberSchema),
            },
            {
                name: "share_folder",
                description: "Shares a folder",
                inputSchema: zodToJsonSchema(ShareFolderSchema),
            },
            {
                name: "list_folder_members",
                description: "Lists the members of a shared folder",
                inputSchema: zodToJsonSchema(ListFolderMembersSchema),
            },
            {
                name: "add_folder_member",
                description: "Adds a member to a shared folder",
                inputSchema: zodToJsonSchema(AddFolderMemberSchema),
            },
            {
                name: "create_file_request",
                description: "Creates a file request",
                inputSchema: zodToJsonSchema(CreateFileRequestSchema),
            },
            {
                name: "get_file_request",
                description: "Gets a file request by ID",
                inputSchema: zodToJsonSchema(GetFileRequestSchema),
            },
            {
                name: "list_file_requests",
                description: "Lists all file requests",
                inputSchema: zodToJsonSchema(ListFileRequestsSchema),
            },
            {
                name: "delete_file_request",
                description: "Deletes file requests",
                inputSchema: zodToJsonSchema(DeleteFileRequestSchema),
            },
            {
                name: "update_file_request",
                description: "Updates a file request (title, destination, description, open/close status)",
                inputSchema: zodToJsonSchema(UpdateFileRequestSchema),
            },
            {
                name: "batch_delete",
                description: "Deletes multiple files and folders in a single operation. This is an efficient way to delete many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry only needs a 'path' field.",
                inputSchema: zodToJsonSchema(BatchDeleteSchema),
            },
            {
                name: "batch_move",
                description: "Moves or renames multiple files and folders in a single operation. This is an efficient way to move many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' and 'allow_ownership_transfer' apply to all entries.",
                inputSchema: zodToJsonSchema(BatchMoveSchema),
            },
            {
                name: "batch_copy",
                description: "Copies multiple files and folders in a single operation. This is an efficient way to copy many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' applies to all entries.",
                inputSchema: zodToJsonSchema(BatchCopySchema),
            },
            {
                name: "check_batch_job_status",
                description: "Checks the status of a batch operation using the async job ID returned from batch operations. Use this to monitor progress and get final results of batch_copy, batch_move, or batch_delete operations. The tool automatically detects the operation type.",
                inputSchema: zodToJsonSchema(BatchJobStatusSchema),
            },
            {
                name: "get_thumbnail",
                description: "Gets a thumbnail image for a file",
                inputSchema: zodToJsonSchema(GetThumbnailSchema),
            },
            {
                name: "add_file_properties",
                description: "Adds custom properties to a file. Properties are key-value pairs that can be used to store custom metadata about files.",
                inputSchema: zodToJsonSchema(AddFilePropertiesSchema),
            },
            {
                name: "overwrite_file_properties",
                description: "Overwrites custom properties on a file. This replaces all existing properties for the specified templates.",
                inputSchema: zodToJsonSchema(OverwriteFilePropertiesSchema),
            },
            {
                name: "update_file_properties",
                description: "Updates custom properties on a file. This allows you to add, update, or remove specific property fields.",
                inputSchema: zodToJsonSchema(UpdateFilePropertiesSchema),
            },
            {
                name: "remove_file_properties",
                description: "Removes custom properties from a file by removing entire property templates.",
                inputSchema: zodToJsonSchema(RemoveFilePropertiesSchema),
            },
            {
                name: "search_file_properties",
                description: "Searches for files based on their custom properties. You can search by property field names or values.",
                inputSchema: zodToJsonSchema(SearchFilePropertiesSchema),
            },
            {
                name: "list_property_templates",
                description: "Lists all available property templates for your account. Templates define the structure of custom properties.",
                inputSchema: zodToJsonSchema(ListPropertyTemplatesSchema),
            },
            {
                name: "get_property_template",
                description: "Gets detailed information about a specific property template, including its fields and types.",
                inputSchema: zodToJsonSchema(GetPropertyTemplateSchema),
            },
            {
                name: "save_url",
                description: "Downloads content from a URL and saves it as a file in Dropbox. This is useful for saving web content, images, documents, etc. directly from URLs.",
                inputSchema: zodToJsonSchema(SaveUrlSchema),
            },
            {
                name: "save_url_check_job_status",
                description: "Checks the status of a save URL operation using the async job ID. Use this to monitor the progress of URL downloads.",
                inputSchema: zodToJsonSchema(SaveUrlCheckJobStatusSchema),
            },
            {
                name: "lock_file_batch",
                description: "Temporarily locks files to prevent them from being edited by others. This is useful during collaborative work to avoid editing conflicts. NOTE: This may be an async operation that returns a job ID for status checking.",
                inputSchema: zodToJsonSchema(LockFileBatchSchema),
            },
            {
                name: "unlock_file_batch",
                description: "Unlocks previously locked files, allowing others to edit them again. NOTE: This may be an async operation that returns a job ID for status checking.",
                inputSchema: zodToJsonSchema(UnlockFileBatchSchema),
            },
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        const dropbox = getDropboxClient();

        try {
            switch (name) {
                case "list_folder": {
                    const validatedArgs = ListFolderSchema.parse(args);

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

                case "list_folder_continue": {
                    const validatedArgs = ListFolderContinueSchema.parse(args);

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

                case "create_folder": {
                    const validatedArgs = CreateFolderSchema.parse(args);
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

                case "delete_file": {
                    const validatedArgs = DeleteFileSchema.parse(args);
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

                case "move_file": {
                    const validatedArgs = MoveFileSchema.parse(args);
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
                                text: `File/folder moved successfully from ${validatedArgs.from_path} to ${response.result.metadata.path_display}`,
                            },
                        ],
                    };
                }

                case "copy_file": {
                    const validatedArgs = CopyFileSchema.parse(args);
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
                                text: `File/folder copied successfully from ${validatedArgs.from_path} to ${response.result.metadata.path_display}`,
                            },
                        ],
                    };
                }

                case "search_files": {
                    const validatedArgs = SearchFilesSchema.parse(args);

                    try {
                        const response = await dropbox.filesSearchV2({
                            query: validatedArgs.query,
                            options: {
                                path: validatedArgs.path,
                                max_results: validatedArgs.max_results,
                                file_status: validatedArgs.file_status as any,
                                filename_only: validatedArgs.filename_only,
                            },
                        });

                        const results = response.result.matches.map((match: any) => {
                            const metadata = match.metadata.metadata;
                            if (metadata['.tag'] === 'file') {
                                return `File: ${metadata.name} (${metadata.path_display}) - Size: ${metadata.size} bytes`;
                            } else if (metadata['.tag'] === 'folder') {
                                return `Folder: ${metadata.name} (${metadata.path_display})`;
                            } else {
                                return `${metadata['.tag']}: ${metadata.name} (${metadata.path_display})`;
                            }
                        });

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `Search results for "${validatedArgs.query}":\n\n${results.join('\n') || 'No results found'}`,
                                },
                            ],
                        };
                    } catch (error: any) {
                        let errorMessage = `Failed to search for: "${validatedArgs.query}"\n`;

                        if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid search query or parameters.\n\n💡 Search tips:\n• Use simple keywords without special characters\n• Try shorter, more common terms\n• Check that the search path exists (if specified)\n• Avoid very long queries (max 256 characters)`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: Search path not found - The specified path doesn't exist.\n\n💡 Make sure:\n• The path parameter is a valid folder path\n• The folder exists in your Dropbox\n• Use empty string to search entire Dropbox`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to search this location.\n\n💡 This could mean:\n• You don't have access to the specified path\n• Your access token lacks search permissions\n• The folder is in a restricted shared space`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting search rate limits.\n\n💡 Try:\n• Waiting a moment before searching again\n• Using more specific search terms\n• Reducing the max_results parameter\n• Searching in specific folders instead of entire Dropbox`;
                        } else {
                            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\n💡 Search troubleshooting:\n• Try simpler keywords\n• Check your internet connection\n• Verify you have search permissions\n• Consider searching in smaller scopes`;
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

                case "get_file_info": {
                    const validatedArgs = GetFileInfoSchema.parse(args);

                    try {
                        const response = await dropbox.filesGetMetadata({
                            path: validatedArgs.path,
                            include_media_info: validatedArgs.include_media_info,
                            include_deleted: validatedArgs.include_deleted,
                            include_has_explicit_shared_members: validatedArgs.include_has_explicit_shared_members,
                        });

                        const metadata = response.result;
                        let info = `Name: ${metadata.name}\nPath: ${metadata.path_display}\nType: ${metadata['.tag']}`;

                        if (metadata['.tag'] === 'file') {
                            info += `\nSize: ${metadata.size} bytes\nLast Modified: ${metadata.server_modified}`;
                            if (metadata.content_hash) {
                                info += `\nContent Hash: ${metadata.content_hash}`;
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
                        let errorMessage = `Failed to get file info for: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File or folder not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The path starts with '/' (e.g., '/myfile.txt')\n• The file/folder exists in your Dropbox\n• Check spelling and case sensitivity\n• The file hasn't been moved or deleted`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to access this file/folder.\n\n💡 This could mean:\n• The file is in a shared folder you don't have access to\n• The file requires special permissions\n• Your access token may have insufficient scope`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check the file path format.\n\n💡 Path requirements:\n• Must start with '/' (e.g., '/Documents/file.txt')\n• Use forward slashes (/) not backslashes (\\)\n• Avoid invalid characters in file names\n• Maximum path length is 260 characters`;
                        } else if (error.status === 401) {
                            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.metadata.read' permission\n• You're authenticated with the correct Dropbox account`;
                        } else {
                            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\n💡 General troubleshooting:\n• Check your internet connection\n• Verify the file/folder path exists\n• Ensure proper authentication`;
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

                case "share_file": {
                    const validatedArgs = ShareFileSchema.parse(args);
                    const response = await dropbox.sharingCreateSharedLinkWithSettings({
                        path: validatedArgs.path,
                        settings: validatedArgs.settings as any,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Shared link created: ${response.result.url}`,
                            },
                        ],
                    };
                }

                case "get_shared_links": {
                    const validatedArgs = GetSharedLinksSchema.parse(args);
                    const response = await dropbox.sharingListSharedLinks({
                        path: validatedArgs.path,
                        cursor: validatedArgs.cursor,
                    });

                    const links = response.result.links.map((link: any) =>
                        `${link.name}: ${link.url} (${link.path_lower})`
                    );

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Shared links:\n\n${links.join('\n') || 'No shared links found'}`,
                            },
                        ],
                    };
                }

                case "upload_file": {
                    const validatedArgs = UploadFileSchema.parse(args);

                    // Convert content to buffer based on provided content type
                    let fileContent: Buffer;
                    
                    if (validatedArgs.text_content) {
                        // Handle plain text content
                        fileContent = Buffer.from(validatedArgs.text_content, 'utf8');
                    } else if (validatedArgs.base64_content) {
                        // Handle base64 encoded content
                        try {
                            fileContent = Buffer.from(validatedArgs.base64_content, 'base64');
                        } catch (error) {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `❌ Invalid base64 content provided. Please ensure the base64_content is properly encoded.`,
                                    },
                                ],
                            };
                        }
                    } else {
                        // This should not happen due to schema validation, but just in case
                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `❌ No content provided. Please specify either text_content or base64_content.`,
                                },
                            ],
                        };
                    }

                    const response = await dropbox.filesUpload({
                        path: validatedArgs.path,
                        contents: fileContent,
                        mode: validatedArgs.mode as any,
                        autorename: validatedArgs.autorename,
                        mute: validatedArgs.mute,
                    });

                    const contentType = validatedArgs.text_content ? 'text' : 'base64';
                    const contentLength = validatedArgs.text_content ? validatedArgs.text_content.length : validatedArgs.base64_content!.length;

                    return {
                        content: [
                            {
                                type: "text",
                                text: `✅ File uploaded successfully!\n\n📄 File: ${response.result.path_display}\n📏 Size: ${response.result.size} bytes\n📝 Content type: ${contentType}\n📊 Input length: ${contentLength} characters`,
                            },
                        ],
                    };
                } case "download_file": {
                    const validatedArgs = DownloadFileSchema.parse(args);

                    try {
                        const response = await dropbox.filesDownload({
                            path: validatedArgs.path,
                        });

                        // The response from filesDownload contains the file data directly
                        const result = response.result as any;

                        // Extract metadata - it should be available directly on the result
                        const fileName = result.name || 'Unknown file';
                        const fileSize = result.size || 'Unknown size';
                        const filePath = result.path_display || validatedArgs.path;

                        // Based on the official Dropbox SDK TypeScript example, the file binary content
                        // is available as result.fileBinary (injected by the SDK, not part of the type definition)
                        let fileBuffer: Buffer | undefined;

                        // Extract file content - according to official SDK examples, it's in result.fileBinary
                        if (result.fileBinary) {
                            // The SDK injects fileBinary as the file content
                            if (Buffer.isBuffer(result.fileBinary)) {
                                fileBuffer = result.fileBinary;
                            } else {
                                // Convert to Buffer if it's not already
                                try {
                                    fileBuffer = Buffer.from(result.fileBinary);
                                } catch (e) {
                                    // Try other approaches if direct conversion fails
                                    if (typeof result.fileBinary === 'string') {
                                        fileBuffer = Buffer.from(result.fileBinary, 'binary');
                                    } else if (result.fileBinary.constructor === Uint8Array) {
                                        fileBuffer = Buffer.from(result.fileBinary);
                                    }
                                }
                            }
                        } else {
                            // Fallback: Try different possible locations for the file content
                            if (Buffer.isBuffer(result)) {
                                // Sometimes the entire result is the buffer
                                fileBuffer = result;
                            } else if (result.file_binary && Buffer.isBuffer(result.file_binary)) {
                                fileBuffer = result.file_binary;
                            } else if (result.content && Buffer.isBuffer(result.content)) {
                                fileBuffer = result.content;
                            } else {
                                // Check if response has a buffer method or property
                                if (typeof response.result === 'object' && response.result !== null) {
                                    // Try to find any buffer-like property
                                    for (const [key, value] of Object.entries(response.result)) {
                                        if (Buffer.isBuffer(value)) {
                                            fileBuffer = value;
                                            break;
                                        }
                                    }
                                }

                                // If still no buffer found, check if it's a ReadableStream or similar
                                if (!fileBuffer && response.result && typeof response.result === 'object') {
                                    // Try to convert to buffer if it's a stream or array-like
                                    try {
                                        if (Array.isArray(response.result) || response.result.constructor === Uint8Array) {
                                            fileBuffer = Buffer.from(response.result);
                                        }
                                    } catch (e) {
                                        // Ignore conversion errors
                                    }
                                }
                            }
                        }

                        if (fileBuffer && Buffer.isBuffer(fileBuffer)) {
                            const base64Content = fileBuffer.toString('base64');

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `✅ File downloaded successfully!\n\n📄 File: ${fileName}\n📏 Size: ${fileSize} bytes\n📁 Path: ${filePath}\n\n� Content (base64):\n${base64Content}`,
                                    },
                                ],
                            };
                        } else {
                            // If no buffer content found, provide detailed debug information
                            const responseInfo = {
                                resultType: typeof response.result,
                                resultConstructor: response.result?.constructor?.name,
                                resultKeys: response.result && typeof response.result === 'object'
                                    ? Object.keys(response.result)
                                    : [],
                                hasFileBinary: 'fileBinary' in (response.result || {}),
                                fileBinaryType: result.fileBinary ? typeof result.fileBinary : 'undefined',
                                fileBinaryConstructor: result.fileBinary?.constructor?.name,
                                isFileBinaryBuffer: Buffer.isBuffer(result.fileBinary),
                                hasFileContent: 'content' in (response.result || {}),
                            };

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `❌ Failed to extract file content from download response\n\n📄 File: ${fileName}\n📏 Size: ${fileSize} bytes\n📁 Path: ${filePath}\n\n🔍 Response analysis:\n${JSON.stringify(responseInfo, null, 2)}\n\n� The file metadata was retrieved but the binary content could not be extracted. This may be a Dropbox SDK version compatibility issue.`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to download file: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The file path is correct and starts with '/'\n• The file exists in your Dropbox\n• You have access to the file`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to download this file.\n\n💡 This could mean:\n• The file is in a shared space you don't have access to\n• Your access token may have insufficient scope (needs 'files.content.read')`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check the file path format.\n\n💡 Path requirements:\n• Must start with '/' (e.g., '/Documents/file.txt')\n• Use forward slashes (/) not backslashes (\\)\n• File must exist and be accessible`;
                        } else if (error.status === 401) {
                            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.content.read' permission\n• You're authenticated with the correct Dropbox account`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Tips:\n• Wait a moment before trying again\n• Reduce the frequency of download requests\n• Consider downloading files in smaller batches`;
                        } else if (error.status === 507) {
                            errorMessage += `\nError 507: Insufficient storage - The download would exceed your quota.`;
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

                case "get_thumbnail": {
                    const validatedArgs = GetThumbnailSchema.parse(args);

                    try {
                        const response = await dropbox.filesGetThumbnail({
                            path: validatedArgs.path,
                            format: validatedArgs.format as any,
                            size: validatedArgs.size as any,
                        });

                        // The response from filesGetThumbnail contains the thumbnail data
                        const result = response.result as any;

                        // Extract metadata
                        const fileName = result.name || 'Unknown file';
                        const fileSize = result.size || 'Unknown size';
                        const filePath = result.path_display || validatedArgs.path;

                        // Extract thumbnail content using the same logic as download_file
                        let thumbnailBuffer: Buffer | undefined;

                        // Extract thumbnail content - similar to download_file, check result.fileBinary first
                        if (result.fileBinary) {
                            // The SDK injects fileBinary as the thumbnail content
                            if (Buffer.isBuffer(result.fileBinary)) {
                                thumbnailBuffer = result.fileBinary;
                            } else {
                                // Convert to Buffer if it's not already
                                try {
                                    thumbnailBuffer = Buffer.from(result.fileBinary);
                                } catch (e) {
                                    // Try other approaches if direct conversion fails
                                    if (typeof result.fileBinary === 'string') {
                                        thumbnailBuffer = Buffer.from(result.fileBinary, 'binary');
                                    } else if (result.fileBinary.constructor === Uint8Array) {
                                        thumbnailBuffer = Buffer.from(result.fileBinary);
                                    }
                                }
                            }
                        } else {
                            // Fallback: Try different possible locations for the thumbnail content
                            if (Buffer.isBuffer(result)) {
                                // Sometimes the entire result is the buffer
                                thumbnailBuffer = result;
                            } else if (result.file_binary && Buffer.isBuffer(result.file_binary)) {
                                thumbnailBuffer = result.file_binary;
                            } else if (result.content && Buffer.isBuffer(result.content)) {
                                thumbnailBuffer = result.content;
                            } else {
                                // Check if response has a buffer method or property
                                if (typeof response.result === 'object' && response.result !== null) {
                                    // Try to find any buffer-like property
                                    for (const [key, value] of Object.entries(response.result)) {
                                        if (Buffer.isBuffer(value)) {
                                            thumbnailBuffer = value;
                                            break;
                                        }
                                    }
                                }

                                // If still no buffer found, check if it's a ReadableStream or similar
                                if (!thumbnailBuffer && response.result && typeof response.result === 'object') {
                                    // Try to convert to buffer if it's a stream or array-like
                                    try {
                                        if (Array.isArray(response.result) || response.result.constructor === Uint8Array) {
                                            thumbnailBuffer = Buffer.from(response.result);
                                        }
                                    } catch (e) {
                                        // Ignore conversion errors
                                    }
                                }
                            }
                        }

                        if (thumbnailBuffer && Buffer.isBuffer(thumbnailBuffer)) {
                            const base64Content = thumbnailBuffer.toString('base64');

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `✅ Thumbnail generated successfully!\n\n📄 File: ${fileName}\n📏 Size: ${fileSize} bytes\n📁 Path: ${filePath}\n🖼️ Format: ${validatedArgs.format || "jpeg"}\n📐 Size: ${validatedArgs.size || "w256h256"}\n\n🖼️ Thumbnail (base64):\n${base64Content}`,
                                    },
                                ],
                            };
                        } else {
                            // If no buffer content found, provide detailed debug information
                            const responseInfo = {
                                resultType: typeof response.result,
                                resultConstructor: response.result?.constructor?.name,
                                resultKeys: response.result && typeof response.result === 'object'
                                    ? Object.keys(response.result)
                                    : [],
                                hasFileBinary: 'fileBinary' in (response.result || {}),
                                fileBinaryType: result.fileBinary ? typeof result.fileBinary : 'undefined',
                                fileBinaryConstructor: result.fileBinary?.constructor?.name,
                                isFileBinaryBuffer: Buffer.isBuffer(result.fileBinary),
                                hasFileContent: 'content' in (response.result || {}),
                            };

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `❌ Failed to extract thumbnail content from response\n\n📄 File: ${fileName}\n📏 Size: ${fileSize} bytes\n📁 Path: ${filePath}\n\n🔍 Response analysis:\n${JSON.stringify(responseInfo, null, 2)}\n\n🖼️ The file metadata was retrieved but the thumbnail binary content could not be extracted. This may be a Dropbox SDK version compatibility issue.`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to generate thumbnail for: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The file path is correct and starts with '/'\n• The file exists in your Dropbox\n• You have access to the file`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to access this file.\n\n💡 This could mean:\n• The file is in a shared space you don't have access to\n• Your access token may have insufficient scope (needs 'files.content.read')`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check the file path format or file type.\n\n💡 Requirements:\n• Path must start with '/' (e.g., '/Photos/image.jpg')\n• File must be an image (JPEG, PNG, GIF, BMP, etc.)\n• File must exist and be accessible`;
                        } else if (error.status === 415) {
                            errorMessage += `\nError 415: Unsupported file type - Thumbnails can only be generated for images.\n\n💡 Supported formats:\n• JPEG, JPG\n• PNG\n• GIF\n• BMP\n• TIFF\n• And other common image formats`;
                        } else if (error.status === 401) {
                            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.content.read' permission\n• You're authenticated with the correct Dropbox account`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Tips:\n• Wait a moment before trying again\n• Reduce the frequency of thumbnail requests\n• Consider generating thumbnails in smaller batches`;
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

                case "list_revisions": {
                    const validatedArgs = ListRevisionsSchema.parse(args);
                    const response = await dropbox.filesListRevisions({
                        path: validatedArgs.path,
                        mode: validatedArgs.mode as any,
                        limit: validatedArgs.limit,
                    });

                    const revisions = (response.result as any).entries?.map((rev: any) =>
                        `Revision ID: ${rev.rev} - Modified: ${rev.server_modified} - Size: ${rev.size} bytes`
                    ) || [];

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Revisions for file "${validatedArgs.path}":\n\n${revisions.join('\n') || 'No revisions found'}`,
                            },
                        ],
                    };
                }

                case "restore_file": {
                    const validatedArgs = RestoreFileSchema.parse(args);
                    const response = await dropbox.filesRestore({
                        path: validatedArgs.path,
                        rev: validatedArgs.rev,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `File restored to revision ${validatedArgs.rev}: ${(response.result as any).path_display}`,
                            },
                        ],
                    };
                }

                case "get_current_account": {
                    GetCurrentAccountSchema.parse(args);
                    const response = await dropbox.usersGetCurrentAccount();

                    const accountInfo = response.result as any;
                    let info = `Account ID: ${accountInfo.account_id}\nEmail: ${accountInfo.email}`;
                    if (accountInfo.name) {
                        info += `\nName: ${accountInfo.name.display_name || accountInfo.name.given_name || 'N/A'}`;
                    }
                    if (accountInfo.account_type) {
                        info += `\nType: ${accountInfo.account_type['.tag'] || 'N/A'}`;
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

                case "get_space_usage": {
                    GetSpaceUsageSchema.parse(args);
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

                case "get_temporary_link": {
                    const validatedArgs = GetTemporaryLinkSchema.parse(args);
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

                case "get_preview": {
                    const validatedArgs = GetPreviewSchema.parse(args);
                    const response = await dropbox.filesGetPreview({
                        path: validatedArgs.path,
                    });

                    // Convert preview buffer to base64 for safe transmission
                    const previewBuffer = (response.result as any).fileBinary as Buffer;
                    const base64Preview = previewBuffer ? previewBuffer.toString('base64') : 'No preview available';

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Preview (base64): ${base64Preview}`,
                            },
                        ],
                    };
                }

                case "add_file_member": {
                    const validatedArgs = AddFileMemberSchema.parse(args);
                    const members = validatedArgs.members.map(member => ({
                        member: { ".tag": "email", email: member.email },
                        access_level: { ".tag": member.access_level }
                    }));

                    const response = await dropbox.sharingAddFileMember({
                        file: validatedArgs.file,
                        members: members as any,
                        quiet: validatedArgs.quiet,
                        custom_message: validatedArgs.custom_message,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Member(s) added to file: ${validatedArgs.file}`,
                            },
                        ],
                    };
                }

                case "list_file_members": {
                    const validatedArgs = ListFileMembersSchema.parse(args);
                    const response = await dropbox.sharingListFileMembers({
                        file: validatedArgs.file,
                        include_inherited: validatedArgs.include_inherited,
                        limit: validatedArgs.limit,
                    });

                    const members = (response.result as any).users?.map((member: any) =>
                        `${member.user?.email || 'N/A'} (${member.access_type?.['.tag'] || 'N/A'})`
                    ) || [];

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Members of file "${validatedArgs.file}":\n\n${members.join('\n') || 'No members found'}`,
                            },
                        ],
                    };
                }

                case "remove_file_member": {
                    const validatedArgs = RemoveFileMemberSchema.parse(args);
                    const response = await dropbox.sharingRemoveFileMember2({
                        file: validatedArgs.file,
                        member: { ".tag": "email", email: validatedArgs.member } as any,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Member removed from file: ${validatedArgs.file}`,
                            },
                        ],
                    };
                }

                case "share_folder": {
                    const validatedArgs = ShareFolderSchema.parse(args);
                    const response = await dropbox.sharingShareFolder({
                        path: validatedArgs.path,
                        member_policy: { ".tag": validatedArgs.member_policy } as any,
                        acl_update_policy: { ".tag": validatedArgs.acl_update_policy } as any,
                        shared_link_policy: { ".tag": validatedArgs.shared_link_policy } as any,
                        force_async: validatedArgs.force_async,
                    });

                    const result = response.result as any;
                    const sharedFolderId = result.shared_folder_id || result.async_job_id || 'Unknown';

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Folder shared: ${validatedArgs.path}\nShared Folder ID: ${sharedFolderId}`,
                            },
                        ],
                    };
                }

                case "list_folder_members": {
                    const validatedArgs = ListFolderMembersSchema.parse(args);
                    const response = await dropbox.sharingListFolderMembers({
                        shared_folder_id: validatedArgs.shared_folder_id,
                        limit: validatedArgs.limit,
                    });

                    const members = (response.result as any).users?.map((member: any) =>
                        `${member.user?.email || 'N/A'} (${member.access_type?.['.tag'] || 'N/A'})`
                    ) || [];

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Members of shared folder "${validatedArgs.shared_folder_id}":\n\n${members.join('\n') || 'No members found'}`,
                            },
                        ],
                    };
                }

                case "add_folder_member": {
                    const validatedArgs = AddFolderMemberSchema.parse(args);
                    const members = validatedArgs.members.map(member => ({
                        member: { ".tag": "email", email: member.email },
                        access_level: { ".tag": member.access_level }
                    }));

                    const response = await dropbox.sharingAddFolderMember({
                        shared_folder_id: validatedArgs.shared_folder_id,
                        members: members as any,
                        quiet: validatedArgs.quiet,
                        custom_message: validatedArgs.custom_message,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Member(s) added to shared folder: ${validatedArgs.shared_folder_id}`,
                            },
                        ],
                    };
                }

                case "create_file_request": {
                    const validatedArgs = CreateFileRequestSchema.parse(args);

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
                            errorMessage += `\nError 403: Permission denied - You may not have permission to create file requests or access the destination folder.`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: Destination folder not found - The path "${validatedArgs.destination}" doesn't exist.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Bad request - Please check the title and destination path format.`;
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

                case "get_file_request": {
                    const validatedArgs = GetFileRequestSchema.parse(args);

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
                        ListFileRequestsSchema.parse(args);
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
                    const validatedArgs = DeleteFileRequestSchema.parse(args);

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
                    const validatedArgs = UpdateFileRequestSchema.parse(args);

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

                case "batch_delete": {
                    const validatedArgs = BatchDeleteSchema.parse(args);

                    try {
                        const response = await dropbox.filesDeleteBatch({
                            entries: validatedArgs.entries,
                        });

                        const result = response.result as any;

                        // Handle both sync and async responses
                        if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                            let resultMessage = `Batch delete completed:\n`;
                            resultMessage += `✅ Successful: ${successful}\n`;
                            resultMessage += `❌ Failed: ${failed}`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any) => `  • ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'async_job_id') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch delete started (async operation)\nJob ID: ${result.async_job_id}\n\n⏳ The operation is processing in the background.\n💡 Use 'check_batch_job_status' with this Job ID to monitor progress and get final results.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch delete initiated. Processing ${validatedArgs.entries.length} entries.`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to perform batch delete on ${validatedArgs.entries.length} items\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You may not have permission to delete some of these files/folders.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Bad request - Check that all paths are valid and properly formatted.`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting rate limits. Try with fewer files or wait a moment.`;
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

                case "batch_move": {
                    const validatedArgs = BatchMoveSchema.parse(args);

                    try {
                        const response = await dropbox.filesMoveBatchV2({
                            entries: validatedArgs.entries,
                            autorename: validatedArgs.autorename,
                            allow_ownership_transfer: validatedArgs.allow_ownership_transfer,
                        });

                        const result = response.result as any;

                        // Handle both sync and async responses
                        if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                            let resultMessage = `Batch move completed:\n`;
                            resultMessage += `✅ Successful: ${successful}\n`;
                            resultMessage += `❌ Failed: ${failed}`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any) => `  • ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'async_job_id') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch move started (async operation)\nJob ID: ${result.async_job_id}\nThe operation is processing in the background. Use the job ID to check status.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch move initiated. Processing ${validatedArgs.entries.length} entries.`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to perform batch move on ${validatedArgs.entries.length} items\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You may not have permission to move some of these files/folders.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Bad request - Check that all source and destination paths are valid.`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - Some destination paths may already exist or there are path conflicts.`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting rate limits. Try with fewer files or wait a moment.`;
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

                case "batch_copy": {
                    const validatedArgs = BatchCopySchema.parse(args);

                    try {
                        const response = await dropbox.filesCopyBatchV2({
                            entries: validatedArgs.entries,
                        });

                        const result = response.result as any;

                        // Handle both sync and async responses
                        if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                            let resultMessage = `Batch copy completed:\n`;
                            resultMessage += `✅ Successful: ${successful}\n`;
                            resultMessage += `❌ Failed: ${failed}`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any) => `  • ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'async_job_id') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch copy started (async operation)\nJob ID: ${result.async_job_id}\n\n⏳ The operation is processing in the background.\n💡 Next Steps:\n1. Use 'check_batch_job_status' tool with this Job ID\n2. Monitor progress until completion\n3. The tool will show final results (✅ successful / ❌ failed counts)\n\nTip: Large batches or many files typically trigger async processing.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch copy initiated. Processing ${validatedArgs.entries.length} entries.`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to perform batch copy on ${validatedArgs.entries.length} items\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You may not have permission to copy some of these files/folders.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Bad request - Check that all source and destination paths are valid.\n\n💡 Batch Copy Parameter Guide:\n• Use simple entries: [{"from_path": "/source", "to_path": "/dest"}]\n• Set top-level 'autorename: true' to auto-rename conflicts\n• Don't include per-entry options like 'allow_shared_folder'\n• Ensure all paths start with '/' and files/folders exist`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - Some destination paths may already exist or there are path conflicts.\n\n💡 Tips:\n• Set top-level 'autorename: true' to automatically rename conflicting files\n• Check for duplicate destination paths in your batch\n• Verify destination folders exist`;
                        } else if (error.status === 429) {
                            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\n💡 Tips:\n• Try with fewer files (batches of 100-500)\n• Wait a few seconds between requests\n• Consider using smaller batch sizes\n• Batch operations are more efficient than individual calls`;
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

                case "check_batch_job_status": {
                    const validatedArgs = BatchJobStatusSchema.parse(args);

                    try {
                        // Try checking different types of batch operations
                        let statusResponse;
                        let operationType = "operation";

                        // First try copy batch check
                        try {
                            statusResponse = await dropbox.filesCopyBatchCheckV2({
                                async_job_id: validatedArgs.async_job_id,
                            });
                            operationType = "copy";
                        } catch (copyError: any) {
                            // If copy check fails, try move batch check
                            try {
                                statusResponse = await dropbox.filesMoveBatchCheckV2({
                                    async_job_id: validatedArgs.async_job_id,
                                });
                                operationType = "move";
                            } catch (moveError: any) {
                                // If move check fails, try delete batch check
                                try {
                                    statusResponse = await dropbox.filesDeleteBatchCheck({
                                        async_job_id: validatedArgs.async_job_id,
                                    });
                                    operationType = "delete";
                                } catch (deleteError: any) {
                                    throw new Error(`Unable to check job status. Job ID may be invalid or expired: ${validatedArgs.async_job_id}`);
                                }
                            }
                        }

                        const result = statusResponse.result as any;

                        if (result['.tag'] === 'in_progress') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch ${operationType} operation is still in progress.\nJob ID: ${validatedArgs.async_job_id}\nStatus: Processing...`,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                            let resultMessage = `Batch ${operationType} operation completed!\n`;
                            resultMessage += `Job ID: ${validatedArgs.async_job_id}\n`;
                            resultMessage += `✅ Successful: ${successful}\n`;
                            resultMessage += `❌ Failed: ${failed}`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'failed') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch ${operationType} operation failed.\nJob ID: ${validatedArgs.async_job_id}\nError: ${result.reason || 'Unknown error'}`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `Batch ${operationType} operation status: ${result['.tag'] || 'Unknown'}\nJob ID: ${validatedArgs.async_job_id}`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to check batch job status for ID: ${validatedArgs.async_job_id}\n`;

                        if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid job ID - The job ID may be malformed or expired.`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: Job not found - The job ID may be invalid or the job may have been cleaned up.`;
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

                case "add_file_properties": {
                    const validatedArgs = AddFilePropertiesSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesPropertiesAdd({
                            path: validatedArgs.path,
                            property_groups: validatedArgs.property_groups,
                        });

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `✅ Properties added successfully to file: ${validatedArgs.path}\n\nAdded ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
                                },
                            ],
                        };
                    } catch (error: any) {
                        let errorMessage = `Failed to add properties to file: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The file path is correct and starts with '/'\n• The file exists in your Dropbox\n• You have access to the file`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.\n\n💡 This could mean:\n• The file is in a shared space you don't have edit access to\n• Your access token may have insufficient scope (needs 'files.metadata.write')`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check your property template ID and field values.\n\n💡 Common issues:\n• Invalid template ID format\n• Field names don't match the template schema\n• Field values exceed length limits\n• Missing required fields`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - Properties may already exist for this template.\n\n💡 Try using:\n• 'overwrite_file_properties' to replace existing properties\n• 'update_file_properties' to modify specific fields`;
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

                case "overwrite_file_properties": {
                    const validatedArgs = OverwriteFilePropertiesSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesPropertiesOverwrite({
                            path: validatedArgs.path,
                            property_groups: validatedArgs.property_groups,
                        });

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `✅ Properties overwritten successfully for file: ${validatedArgs.path}\n\nOverwrote ${validatedArgs.property_groups.length} property group(s):\n${validatedArgs.property_groups.map(group => `- Template ID: ${group.template_id} (${group.fields.length} fields)`).join('\n')}`,
                                },
                            ],
                        };
                    } catch (error: any) {
                        let errorMessage = `Failed to overwrite properties for file: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check your property template ID and field values.`;
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

                case "update_file_properties": {
                    const validatedArgs = UpdateFilePropertiesSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesPropertiesUpdate({
                            path: validatedArgs.path,
                            update_property_groups: validatedArgs.update_property_groups,
                        });

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `✅ Properties updated successfully for file: ${validatedArgs.path}\n\nUpdated ${validatedArgs.update_property_groups.length} property group(s):\n${validatedArgs.update_property_groups.map(group => {
                                        const addCount = group.add_or_update_fields?.length || 0;
                                        const removeCount = group.remove_fields?.length || 0;
                                        return `- Template ID: ${group.template_id} (+${addCount} fields, -${removeCount} fields)`;
                                    }).join('\n')}`,
                                },
                            ],
                        };
                    } catch (error: any) {
                        let errorMessage = `Failed to update properties for file: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check your property template ID and field operations.`;
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

                case "remove_file_properties": {
                    const validatedArgs = RemoveFilePropertiesSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesPropertiesRemove({
                            path: validatedArgs.path,
                            property_template_ids: validatedArgs.property_template_ids,
                        });

                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `✅ Properties removed successfully from file: ${validatedArgs.path}\n\nRemoved ${validatedArgs.property_template_ids.length} property template(s):\n${validatedArgs.property_template_ids.map(id => `- ${id}`).join('\n')}`,
                                },
                            ],
                        };
                    } catch (error: any) {
                        let errorMessage = `Failed to remove properties from file: "${validatedArgs.path}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: File not found - The path "${validatedArgs.path}" doesn't exist.`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to modify properties for this file.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check your property template IDs.`;
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

                case "search_file_properties": {
                    const validatedArgs = SearchFilePropertiesSchema.parse(args);

                    try {
                        // Create properly typed queries for Dropbox API
                        const dropboxQueries = validatedArgs.queries.map(query => {
                            if (query.mode === 'field_name') {
                                return {
                                    query: query.query,
                                    mode: { '.tag': 'field_name' as const },
                                    logical_operator: query.logical_operator ? { '.tag': 'or_operator' as const } : undefined,
                                };
                            } else {
                                return {
                                    query: query.query,
                                    mode: { '.tag': 'field_value' as const },
                                    logical_operator: query.logical_operator ? { '.tag': 'or_operator' as const } : undefined,
                                };
                            }
                        });

                        const templateFilter = validatedArgs.template_filter === 'filter_none'
                            ? { '.tag': 'filter_none' as const }
                            : { '.tag': 'filter_some' as const, filter_some: [] };

                        const response = await dropbox.filePropertiesPropertiesSearch({
                            queries: dropboxQueries as any, // Type assertion due to SDK complexity
                            template_filter: templateFilter as any,
                        });

                        const matches = response.result.matches || [];
                        let resultText = `🔍 Property search results: ${matches.length} file(s) found\n\n`;

                        if (matches.length === 0) {
                            resultText += `No files found matching the search criteria.\n\n💡 Search tips:\n• Check the spelling of property values\n• Make sure the template has been used on some files\n• Try searching in both field names and values\n• Use more general search terms`;
                        } else {
                            resultText += matches.map((match: any, index: number) => {
                                const metadata = match.metadata;
                                const properties = match.property_groups || [];

                                return `${index + 1}. 📄 ${metadata.name}\n   Path: ${metadata.path_display}\n   Properties: ${properties.length} group(s)\n   ${properties.map((group: any) => `   - Template: ${group.template_id} (${group.fields?.length || 0} fields)`).join('\n   ')}`;
                            }).join('\n\n');
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
                        let errorMessage = `Failed to search file properties\n`;

                        if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid search query - Check your search parameters.\n\n💡 Make sure:\n• Query strings are not empty\n• Mode is either 'field_name' or 'field_value'\n• Template filter is valid`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to search properties.\n\n💡 Your access token may need 'files.metadata.read' permission.`;
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

                case "list_property_templates": {
                    const validatedArgs = ListPropertyTemplatesSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesTemplatesListForUser();

                        const templates = response.result.template_ids || [];
                        let resultText = `📋 Property Templates: ${templates.length} template(s) available\n\n`;

                        if (templates.length === 0) {
                            resultText += `No property templates found for your account.\n\n💡 To use file properties:\n• Create property templates through Dropbox Business Admin Console\n• Or use the Dropbox API to create templates programmatically\n• Templates define the structure (fields and types) for custom properties`;
                        } else {
                            resultText += `Template IDs:\n${templates.map((id: string, index: number) => `${index + 1}. ${id}`).join('\n')}\n\n💡 Use 'get_property_template' to see detailed information about each template.`;
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
                        let errorMessage = `Failed to list property templates\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to access property templates.\n\n💡 This feature may require:\n• A Dropbox Business account\n• Admin permissions\n• 'files.metadata.read' scope in your access token`;
                        } else if (error.status === 401) {
                            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.`;
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

                case "get_property_template": {
                    const validatedArgs = GetPropertyTemplateSchema.parse(args);

                    try {
                        const response = await dropbox.filePropertiesTemplatesGetForUser({
                            template_id: validatedArgs.template_id,
                        });

                        const template = response.result;
                        let resultText = `📋 Property Template Details\n\n`;
                        resultText += `Template ID: ${validatedArgs.template_id}\n`;
                        resultText += `Name: ${(template as any).name || 'Unknown'}\n`;
                        resultText += `Description: ${(template as any).description || 'No description'}\n\n`;

                        const fields = (template as any).fields;
                        if (fields && fields.length > 0) {
                            resultText += `Fields (${fields.length}):\n`;
                            fields.forEach((field: any, index: number) => {
                                resultText += `${index + 1}. ${field.name || 'Unknown field'}\n`;
                                resultText += `   Type: ${field.type || 'Unknown type'}\n`;
                                resultText += `   Description: ${field.description || 'No description'}\n`;
                            });
                        } else {
                            resultText += `No fields defined for this template.`;
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
                        let errorMessage = `Failed to get property template: "${validatedArgs.template_id}"\n`;

                        if (error.status === 404) {
                            errorMessage += `\nError 404: Template not found - The template ID "${validatedArgs.template_id}" doesn't exist.\n\n💡 Make sure:\n• The template ID is correct\n• You have access to this template\n• Use 'list_property_templates' to see available templates`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to access this template.`;
                        } else if (error.status === 401) {
                            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.`;
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

                case "save_url": {
                    const validatedArgs = SaveUrlSchema.parse(args);

                    try {
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
                                        text: `✅ URL content saved successfully!\n\n📄 File: ${metadata.name}\n📁 Path: ${metadata.path_display}\n📏 Size: ${metadata.size} bytes\n🕒 Modified: ${metadata.client_modified}\n\n🌐 Source URL: ${validatedArgs.url}`,
                                    },
                                ],
                            };
                        } else if (response.result['.tag'] === 'async_job_id') {
                            const jobId = (response.result as any).async_job_id;
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `🔄 URL download started (large file detected)\n\n📄 Target: ${validatedArgs.path}\n🌐 Source: ${validatedArgs.url}\n🆔 Job ID: ${jobId}\n\n💡 Use 'save_url_check_job_status' with this job ID to monitor progress.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `⚠️ Unexpected response from save URL operation\n\nTarget: ${validatedArgs.path}\nSource: ${validatedArgs.url}\nResponse: ${JSON.stringify(response.result, null, 2)}`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to save URL content to: "${validatedArgs.path}"\nSource URL: ${validatedArgs.url}\n`;

                        if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check the URL and file path.\n\n💡 Common issues:\n• Invalid URL format\n• URL is not accessible\n• File path format is incorrect (should start with '/')\n• File name contains invalid characters`;
                        } else if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied\n\n💡 This could mean:\n• You don't have permission to write to this folder\n• Your access token needs 'files.content.write' scope\n• The URL content is blocked by content policy`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - File already exists at this path.\n\n💡 Try:\n• Using a different file name\n• Enabling autorename in your upload settings\n• Deleting the existing file first`;
                        } else if (error.status === 507) {
                            errorMessage += `\nError 507: Insufficient storage - Your Dropbox is full.\n\n💡 To fix this:\n• Delete some files to free up space\n• Upgrade your Dropbox plan for more storage`;
                        } else if (error.status === 415) {
                            errorMessage += `\nError 415: Unsupported media type - The URL content type is not supported.\n\n💡 Dropbox may not support:\n• Certain file types\n• Very large files\n• Streaming content`;
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

                case "save_url_check_job_status": {
                    const validatedArgs = SaveUrlCheckJobStatusSchema.parse(args);

                    try {
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
                                        text: `✅ URL download completed successfully!\n\n📄 File: ${fileName}\n📁 Path: ${filePath}\n📏 Size: ${fileSize} bytes\n🕒 Modified: ${modified}\n\n🆔 Job ID: ${validatedArgs.async_job_id}`,
                                    },
                                ],
                            };
                        } else if (response.result['.tag'] === 'in_progress') {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `🔄 URL download is still in progress...\n\n🆔 Job ID: ${validatedArgs.async_job_id}\n\n💡 Please wait and check again in a few moments.`,
                                    },
                                ],
                            };
                        } else if (response.result['.tag'] === 'failed') {
                            const failureReason = (response.result as any).reason || 'Unknown error';
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `❌ URL download failed\n\n🆔 Job ID: ${validatedArgs.async_job_id}\n🚫 Reason: ${failureReason}\n\n💡 Common failure reasons:\n• URL became inaccessible\n• Network timeout\n• File size too large\n• Content type not supported`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `⚠️ Unknown job status: ${response.result['.tag']}\n\n🆔 Job ID: ${validatedArgs.async_job_id}`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to check save URL job status\nJob ID: ${validatedArgs.async_job_id}\n`;

                        if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid job ID - The job ID may be malformed or expired.`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: Job not found - The job ID may be invalid or the job may have been cleaned up.`;
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

                case "lock_file_batch": {
                    const validatedArgs = LockFileBatchSchema.parse(args);

                    try {
                        const response = await dropbox.filesLockFileBatch({
                            entries: validatedArgs.entries,
                        });

                        const result = response.result as any;

                        // Check if response has entries directly (sync response)
                        if (result.entries) {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.length - successful;

                            let resultMessage = `🔒 File locking batch operation completed!\n\n`;
                            resultMessage += `✅ Successfully locked: ${successful} file(s)\n`;
                            resultMessage += `❌ Failed to lock: ${failed} file(s)`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        }
                        // Check if response is immediate or async (with .tag)
                        else if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.length - successful;

                            let resultMessage = `🔒 File locking batch operation completed!\n\n`;
                            resultMessage += `✅ Successfully locked: ${successful} file(s)\n`;
                            resultMessage += `❌ Failed to lock: ${failed} file(s)`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'async_job_id') {
                            const jobId = result.async_job_id;
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `🔄 File locking batch operation started (large batch detected)\n\n🆔 Job ID: ${jobId}\n\n💡 Use 'check_batch_job_status' with this job ID to monitor progress.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `⚠️ Unknown response from file locking operation: ${result['.tag'] || 'undefined'}\nFull response: ${JSON.stringify(result, null, 2)}`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to lock files\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to lock these files.\n\n💡 File locking may require:\n• Edit permissions on the files\n• Files to be in shared folders you manage\n• Dropbox Business account features`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: One or more files not found - Check that all file paths exist.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check file paths and batch size (max 1000 files).`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - Some files may already be locked or in use.`;
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

                case "unlock_file_batch": {
                    const validatedArgs = UnlockFileBatchSchema.parse(args);

                    try {
                        const response = await dropbox.filesUnlockFileBatch({
                            entries: validatedArgs.entries,
                        });

                        const result = response.result as any;

                        // Check if response has entries directly (sync response)
                        if (result.entries) {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.length - successful;

                            let resultMessage = `🔓 File unlocking batch operation completed!\n\n`;
                            resultMessage += `✅ Successfully unlocked: ${successful} file(s)\n`;
                            resultMessage += `❌ Failed to unlock: ${failed} file(s)`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        }
                        // Check if response is immediate or async (with .tag)
                        else if (result['.tag'] === 'complete') {
                            const entries = result.entries || [];
                            const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                            const failed = entries.length - successful;

                            let resultMessage = `🔓 File unlocking batch operation completed!\n\n`;
                            resultMessage += `✅ Successfully unlocked: ${successful} file(s)\n`;
                            resultMessage += `❌ Failed to unlock: ${failed} file(s)`;

                            if (failed > 0) {
                                const failureDetails = entries
                                    .filter((entry: any) => entry['.tag'] === 'failure')
                                    .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                                    .join('\n');
                                resultMessage += `\n\nFailure details:\n${failureDetails}`;
                            }

                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: resultMessage,
                                    },
                                ],
                            };
                        } else if (result['.tag'] === 'async_job_id') {
                            const jobId = result.async_job_id;
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `🔄 File unlocking batch operation started (large batch detected)\n\n🆔 Job ID: ${jobId}\n\n💡 Use 'check_batch_job_status' with this job ID to monitor progress.`,
                                    },
                                ],
                            };
                        } else {
                            return {
                                content: [
                                    {
                                        type: "text",
                                        text: `⚠️ Unknown response from file unlocking operation: ${result['.tag'] || 'undefined'}\nFull response: ${JSON.stringify(result, null, 2)}`,
                                    },
                                ],
                            };
                        }
                    } catch (error: any) {
                        let errorMessage = `Failed to unlock files\n`;

                        if (error.status === 403) {
                            errorMessage += `\nError 403: Permission denied - You don't have permission to unlock these files.\n\n💡 You can only unlock:\n• Files you previously locked\n• Files in shared folders you manage\n• Files you have edit permissions for`;
                        } else if (error.status === 404) {
                            errorMessage += `\nError 404: One or more files not found - Check that all file paths exist.`;
                        } else if (error.status === 400) {
                            errorMessage += `\nError 400: Invalid request - Check file paths and batch size (max 1000 files).`;
                        } else if (error.status === 409) {
                            errorMessage += `\nError 409: Conflict - Some files may not be locked or may be locked by others.`;
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

                // Note: get_thumbnail functionality removed due to incomplete Dropbox API documentation
                // and inconsistent SDK behavior with binary data handling

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            // Enhanced general error handling with detailed context
            let errorMessage = `❌ Operation failed: ${name}\n`;

            // Add error details based on type
            if (error.status) {
                errorMessage += `\n🔍 HTTP Status: ${error.status}`;

                // Common Dropbox API error patterns
                if (error.status === 400) {
                    errorMessage += `\n📝 Error 400: Bad Request - The request was malformed or invalid`;
                    errorMessage += `\n\n💡 Common causes:\n• Invalid file paths (must start with '/')\n• Malformed JSON parameters\n• Missing required fields\n• Invalid parameter values`;
                } else if (error.status === 401) {
                    errorMessage += `\n🔐 Error 401: Unauthorized - Authentication failed`;
                    errorMessage += `\n\n💡 Common causes:\n• Access token is invalid or expired\n• Insufficient permissions/scope\n• Token not provided in request header\n• Account access restrictions`;
                } else if (error.status === 403) {
                    errorMessage += `\n🚫 Error 403: Forbidden - Permission denied`;
                    errorMessage += `\n\n💡 Common causes:\n• Insufficient permissions for this operation\n• File/folder access restrictions\n• Team policy limitations\n• Read-only access token`;
                } else if (error.status === 404) {
                    errorMessage += `\n🔍 Error 404: Not Found - Resource doesn't exist`;
                    errorMessage += `\n\n💡 Common causes:\n• File or folder path doesn't exist\n• Incorrect file/folder name\n• Item was deleted or moved\n• Typo in the path`;
                } else if (error.status === 409) {
                    errorMessage += `\n⚠️ Error 409: Conflict - Resource conflict occurred`;
                    errorMessage += `\n\n💡 Common causes:\n• File already exists at destination\n• Concurrent modifications\n• Name conflicts\n• Path conflicts`;
                } else if (error.status === 429) {
                    errorMessage += `\n⏰ Error 429: Rate Limited - Too many requests`;
                    errorMessage += `\n\n💡 Solutions:\n• Wait a few seconds before retrying\n• Reduce request frequency\n• Use batch operations for multiple items\n• Consider implementing exponential backoff`;
                } else if (error.status === 500) {
                    errorMessage += `\n🔧 Error 500: Internal Server Error - Dropbox server issue`;
                    errorMessage += `\n\n💡 Solutions:\n• Retry the request after a short delay\n• Check Dropbox status page\n• Try again later\n• Contact support if persistent`;
                } else if (error.status === 503) {
                    errorMessage += `\n🚧 Error 503: Service Unavailable - Dropbox temporarily unavailable`;
                    errorMessage += `\n\n💡 Solutions:\n• Retry after the suggested delay\n• Check Dropbox status page\n• Implement retry logic with exponential backoff`;
                } else {
                    errorMessage += `\n❓ Uncommon HTTP status code`;
                }
            }

            // Add Dropbox-specific error details
            if (error.error_summary) {
                errorMessage += `\n\n📋 Dropbox Error: ${error.error_summary}`;
            }

            if (error.error && error.error['.tag']) {
                errorMessage += `\n🏷️ Error Type: ${error.error['.tag']}`;
            }

            // Add the original error message
            if (error.message) {
                errorMessage += `\n\n💬 Details: ${error.message}`;
            }

            // Add general troubleshooting tips
            errorMessage += `\n\n🛠️ General Troubleshooting:\n`;
            errorMessage += `• Check your internet connection\n`;
            errorMessage += `• Verify your Dropbox access token is valid\n`;
            errorMessage += `• Ensure file/folder paths are correct (start with '/')\n`;
            errorMessage += `• Check Dropbox account permissions\n`;
            errorMessage += `• Try the operation again in a few moments`;

            // Add operation-specific context
            errorMessage += `\n\n🎯 Operation attempted: ${name}`;
            if (args && Object.keys(args).length > 0) {
                const sanitizedArgs = { ...args };
                // Don't expose sensitive data
                if (sanitizedArgs.content && typeof sanitizedArgs.content === 'string') {
                    sanitizedArgs.content = `[${sanitizedArgs.content.length} characters]`;
                } else if (sanitizedArgs.content) {
                    sanitizedArgs.content = `[content hidden]`;
                }
                errorMessage += `\n📄 Parameters: ${JSON.stringify(sanitizedArgs, null, 2)}`;
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
    });

    return server;
};

// Create Express App
const app = express();

//=============================================================================
// STREAMABLE HTTP TRANSPORT (PROTOCOL VERSION 2025-03-26)
//=============================================================================

app.post('/mcp', (req: Request, res: Response) => {
    handleMcpRequest(req, res);
});

async function handleMcpRequest(req: Request, res: Response) {
    const accessToken = req.headers['x-auth-token'] as string;
    if (!accessToken) {
        console.error('Error: Access token is missing. Provide it via x-auth-token header.');
        return res.status(401).json({
            jsonrpc: '2.0',
            error: {
                code: -32000,
                message: 'Access token is missing. Provide it via x-auth-token header.',
            },
            id: null,
        });
    }

    // Initialize Dropbox client with the access token
    const dropboxClient = new Dropbox({
        fetch: fetch,
        accessToken
    });

    const server = getDropboxMcpServer();
    try {
        const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
        });
        await server.connect(transport);
        asyncLocalStorage.run({ dropboxClient }, async () => {
            await transport.handleRequest(req, res, req.body);
        });
        res.on('close', () => {
            transport.close();
            server.close();
        });
    } catch (error) {
        console.error('Error handling MCP request:', error);
        if (!res.headersSent) {
            res.status(500).json({
                jsonrpc: '2.0',
                error: {
                    code: -32603,
                    message: 'Internal server error',
                },
                id: null,
            });
        }
    }
}

app.get('/mcp', async (req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

app.delete('/mcp', async (req: Request, res: Response) => {
    res.writeHead(405).end(JSON.stringify({
        jsonrpc: "2.0",
        error: {
            code: -32000,
            message: "Method not allowed."
        },
        id: null
    }));
});

//=============================================================================
// DEPRECATED HTTP+SSE TRANSPORT (PROTOCOL VERSION 2024-11-05)
//=============================================================================

// Map to store SSE transports
const transports = new Map<string, SSEServerTransport>();

app.get("/sse", (req: Request, res: Response) => {
    handleSseRequest(req, res);
});

async function handleSseRequest(req: Request, res: Response) {
    const accessToken = req.headers['x-auth-token'] as string;
    if (!accessToken) {
        console.error('Error: Access token is missing. Provide it via x-auth-token header.');
        return res.status(401).json({
            error: 'Access token is missing. Provide it via x-auth-token header.',
        });
    }

    const transport = new SSEServerTransport(`/messages`, res);

    // Set up cleanup when connection closes
    res.on('close', async () => {
        try {
            transports.delete(transport.sessionId);
        } finally {
        }
    });

    transports.set(transport.sessionId, transport);

    const server = getDropboxMcpServer();
    await server.connect(transport);

    console.log(`SSE connection established with transport: ${transport.sessionId}`);
}

app.post("/messages", (req: Request, res: Response) => {
    handleMessagesRequest(req, res);
});

async function handleMessagesRequest(req: Request, res: Response) {
    const sessionId = req.query.sessionId as string;
    const accessToken = req.headers['x-auth-token'] as string;
    if (!accessToken) {
        console.error('Error: Access token is missing. Provide it via x-auth-token header.');
        return res.status(401).json({
            error: 'Access token is missing. Provide it via x-auth-token header.',
        });
    }

    let transport: SSEServerTransport | undefined;
    transport = sessionId ? transports.get(sessionId) : undefined;
    if (transport) {
        // Initialize Dropbox client with the access token
        const dropboxClient = new Dropbox({
            fetch: fetch,
            accessToken
        });

        asyncLocalStorage.run({ dropboxClient }, async () => {
            await transport!.handlePostMessage(req, res);
        });
    } else {
        console.error(`Transport not found for session ID: ${sessionId}`);
        res.status(404).send({ error: "Transport not found" });
    }
}

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Dropbox MCP server running on port ${PORT}`);
});
