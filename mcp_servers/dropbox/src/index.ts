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
    content: z.string().describe("File content as string or base64 encoded data"),
    mode: z.enum(['add', 'overwrite', 'update']).optional().default('add').describe("Upload mode"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename file if it already exists"),
    mute: z.boolean().optional().default(false).describe("Suppress notifications"),
});

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
        ],
    }));

    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name, arguments: args } = request.params;
        const dropbox = getDropboxClient();

        try {
            switch (name) {
                case "list_folder": {
                    const validatedArgs = ListFolderSchema.parse(args);
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

                    return {
                        content: [
                            {
                                type: "text",
                                text: `Contents of folder "${validatedArgs.path || '/'}":\n\n${entries.join('\n')}`,
                            },
                        ],
                    };
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
                }

                case "get_file_info": {
                    const validatedArgs = GetFileInfoSchema.parse(args);
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
                    
                    // Convert content to buffer
                    let fileContent: Buffer;
                    try {
                        // Try to decode as base64 first
                        fileContent = Buffer.from(validatedArgs.content, 'base64');
                    } catch {
                        // If base64 fails, treat as plain text
                        fileContent = Buffer.from(validatedArgs.content, 'utf8');
                    }

                    const response = await dropbox.filesUpload({
                        path: validatedArgs.path,
                        contents: fileContent,
                        mode: validatedArgs.mode as any,
                        autorename: validatedArgs.autorename,
                        mute: validatedArgs.mute,
                    });

                    return {
                        content: [
                            {
                                type: "text",
                                text: `File uploaded successfully: ${response.result.path_display} (${response.result.size} bytes)`,
                            },
                        ],
                    };
                }

                case "download_file": {
                    const validatedArgs = DownloadFileSchema.parse(args);
                    const response = await dropbox.filesDownload({
                        path: validatedArgs.path,
                    });

                    // Convert file buffer to base64 for safe transmission
                    const fileBuffer = (response.result as any).fileBinary as Buffer;
                    const base64Content = fileBuffer.toString('base64');
                    const metadata = response.result;

                    return {
                        content: [
                            {
                                type: "text",
                                text: `File downloaded: ${metadata.name}\nSize: ${metadata.size} bytes\nContent (base64): ${base64Content}`,
                            },
                        ],
                    };
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
                            errorMessage += `\nError 409: Conflict - This usually means:\n` +
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

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (error: any) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error: ${error.message}`,
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
