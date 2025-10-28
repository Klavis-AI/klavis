import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handle add file member operation
 */
async function handleAddFileMember(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.AddFileMemberSchema.parse(args);
    const dropbox = getDropboxClient();

    // First, get the file ID if a path was provided
    let fileId = validatedArgs.file;

    // If the file parameter doesn't start with "id:", treat it as a path and get the file ID
    if (!fileId.startsWith('id:')) {
        const fileInfo = await dropbox.filesGetMetadata({
            path: fileId,
        });
        fileId = (fileInfo.result as any).id;
        if (!fileId) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to get file ID for path: "${validatedArgs.file}"\n\nThe file exists but no ID was returned. This may be due to file type or permission limitations.`,
                    },
                ],
            };
        }
    }

    const members = validatedArgs.members.map(member => ({
        ".tag": "email",
        email: member.email
    }));

    const response = await dropbox.sharingAddFileMember({
        file: fileId,
        members: members as any,
        access_level: { ".tag": validatedArgs.members[0].access_level },
        quiet: validatedArgs.quiet,
        custom_message: validatedArgs.custom_message,
    });

    return {
        content: [
            {
                type: "text",
                text: `Member(s) added to file successfully!\n\nFile: ${validatedArgs.file}\nMembers added: ${validatedArgs.members.map(m => `${m.email} (${m.access_level})`).join(', ')}\nFile ID: ${fileId}`,
            },
        ],
    };
}

/**
 * Handle list file members operation
 */
async function handleListFileMembers(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ListFileMembersSchema.parse(args);
    const dropbox = getDropboxClient();

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

/**
 * Handle remove file member operation
 */
async function handleRemoveFileMember(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.RemoveFileMemberSchema.parse(args);
    const dropbox = getDropboxClient();

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

/**
 * Handle share folder operation
 */
async function handleShareFolder(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ShareFolderSchema.parse(args);
    const dropbox = getDropboxClient();

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
                text: `Folder shared successfully!\n\nFolder: ${validatedArgs.path}\nShared Folder ID: ${sharedFolderId}\nMember Policy: ${validatedArgs.member_policy}\nACL Update Policy: ${validatedArgs.acl_update_policy}\nShared Link Policy: ${validatedArgs.shared_link_policy}`,
            },
        ],
    };
}

/**
 * Handle list folder members operation
 */
async function handleListFolderMembers(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ListFolderMembersSchema.parse(args);
    const dropbox = getDropboxClient();

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

/**
 * Handle add folder member operation
 */
async function handleAddFolderMember(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.AddFolderMemberSchema.parse(args);
    const dropbox = getDropboxClient();

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

/**
 * Handle remove folder member operation
 */
async function handleRemoveFolderMember(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.RemoveFolderMemberSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.sharingRemoveFolderMember({
        shared_folder_id: validatedArgs.shared_folder_id,
        member: { ".tag": "email", email: validatedArgs.member },
        leave_a_copy: validatedArgs.leave_a_copy,
    });

    const result = response.result as any;
    let resultText = `Remove folder member operation initiated for shared folder ID: ${validatedArgs.shared_folder_id}\n\n`;

    if (result['.tag'] === 'async_job_id') {
        resultText += `Operation is being processed asynchronously.\n\nJob ID: ${result.async_job_id}\n\nUse "check_job_status" with this ID to monitor the progress.`;
    } else {
        resultText += `Unexpected result: ${JSON.stringify(result)}`;
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
 * Handle share file operation
 */
async function handleShareFile(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ShareFileSchema.parse(args);
    const dropbox = getDropboxClient();

    const shareSettings: any = {};
    if (validatedArgs.settings) {
        if (validatedArgs.settings.requested_visibility) {
            shareSettings.requested_visibility = { ".tag": validatedArgs.settings.requested_visibility };
        }
        if (validatedArgs.settings.link_password) {
            shareSettings.link_password = validatedArgs.settings.link_password;
        }
        if (validatedArgs.settings.expires) {
            shareSettings.expires = validatedArgs.settings.expires;
        }
    }

    const response = await dropbox.sharingCreateSharedLinkWithSettings({
        path: validatedArgs.path,
        settings: Object.keys(shareSettings).length > 0 ? shareSettings : undefined,
    });

    const result = response.result;
    return {
        content: [
            {
                type: "text",
                text: `File shared successfully!\n\nFile: ${(result as any).name}\nShared Link: ${(result as any).url}\nPath: ${(result as any).path_display}\nVisibility: ${(result as any).link_permissions?.resolved_visibility?.['.tag'] || 'Unknown'}`,
            },
        ],
    };
}

/**
 * Handle get shared links operation
 */
async function handleGetSharedLinks(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.GetSharedLinksSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.sharingListSharedLinks({
        path: validatedArgs.path,
        cursor: validatedArgs.cursor,
    });

    const links = (response.result as any).links || [];
    let resultText = `Shared Links${validatedArgs.path ? ` for "${validatedArgs.path}"` : ''}: ${links.length} link(s) found\n\n`;

    if (links.length === 0) {
        resultText += 'No shared links found.';
    } else {
        resultText += links.map((link: any, index: number) => {
            return `${index + 1}. ${link.name}\n   URL: ${link.url}\n   Path: ${link.path_display}\n   Visibility: ${link.link_permissions?.resolved_visibility?.['.tag'] || 'Unknown'}\n   Expires: ${link.expires || 'Never'}`;
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
}

/**
 * Handle unshare file operation
 */
async function handleUnshareFile(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.UnshareFileSchema.parse(args);
    const dropbox = getDropboxClient();

    await dropbox.sharingUnshareFile({
        file: validatedArgs.file,
    });

    return {
        content: [
            {
                type: "text",
                text: `Successfully unshared file: ${validatedArgs.file}\n\nAll members have been removed from this file (inherited members are not affected).`,
            },
        ],
    };
}

/**
 * Handle unshare folder operation
 */
async function handleUnshareFolder(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.UnshareFolderSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.sharingUnshareFolder({
        shared_folder_id: validatedArgs.shared_folder_id,
        leave_a_copy: validatedArgs.leave_a_copy,
    });

    const result = response.result as any;
    let resultText = `Unshare folder operation initiated for shared folder ID: ${validatedArgs.shared_folder_id}\n\n`;

    if (result['.tag'] === 'complete') {
        resultText += `Operation completed successfully. The folder has been unshared.`;
        if (validatedArgs.leave_a_copy) {
            resultText += `\nMembers will keep a copy of the folder in their Dropbox.`;
        } else {
            resultText += `\nThe folder has been removed from members' Dropbox accounts.`;
        }
    } else if (result['.tag'] === 'async_job_id') {
        resultText += `Operation is being processed asynchronously.\n\nJob ID: ${result.async_job_id}\n\nUse "check_job_status" with this ID to monitor the progress.`;
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
 * Handle list shared folders operation
 */
async function handleListSharedFolders(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ListSharedFoldersSchema.parse(args);
    const dropbox = getDropboxClient();

    const requestArgs: any = {
        limit: validatedArgs.limit,
    };

    if (validatedArgs.cursor) {
        requestArgs.cursor = validatedArgs.cursor;
    }

    const response = await dropbox.sharingListFolders(requestArgs);

    const result = response.result as any;
    let resultText = `Shared Folders:\n\n`;

    if (result.entries && result.entries.length > 0) {
        result.entries.forEach((folder: any, index: number) => {
            resultText += `${index + 1}. **${folder.name}**\n`;
            resultText += `   ID: ${folder.shared_folder_id}\n`;
            resultText += `   Path: ${folder.path_lower || 'N/A'}\n`;
            resultText += `   Access Type: ${folder.access_type?.['.tag'] || 'Unknown'}\n`;
            if (folder.is_team_folder) {
                resultText += `   Team Folder: Yes\n`;
            }
            if (folder.policy) {
                resultText += `   Policy: ${folder.policy.acl_update_policy?.['.tag'] || 'N/A'}\n`;
            }
            resultText += `\n`;
        });
    } else {
        resultText += `No shared folders found.\n`;
    }

    if (result.has_more) {
        resultText += `\nMore results available. Use 'list_shared_folders' with cursor: ${result.cursor}`;
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
 * Handle list received files operation
 */
async function handleListReceivedFiles(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.ListReceivedFilesSchema.parse(args);
    const dropbox = getDropboxClient();

    const requestArgs: any = {
        limit: validatedArgs.limit,
    };

    if (validatedArgs.cursor) {
        requestArgs.cursor = validatedArgs.cursor;
    }

    const response = await dropbox.sharingListReceivedFiles(requestArgs);
    const result = response.result as any;
    let resultText = `Files Shared With You:\n\n`;

    if (result.entries && result.entries.length > 0) {
        result.entries.forEach((file: any, index: number) => {
            resultText += `${index + 1}. **${file.name}**\n`;
            resultText += `   ID: ${file.id}\n`;
            resultText += `   Path: ${file.path_display || file.path_lower || 'N/A'}\n`;
            resultText += `   Shared by: ${file.owner_display_names?.[0] || 'Unknown'}\n`;
            resultText += `   Access Level: ${file.access_type?.['.tag'] || 'Unknown'}\n`;
            if (file.time_invited) {
                resultText += `   Invited: ${new Date(file.time_invited).toLocaleString()}\n`;
            }
            if (file.preview_url) {
                resultText += `   Preview: Available\n`;
            }
            resultText += `\n`;
        });
    } else {
        resultText += `No files have been shared with you.\n`;
    }

    if (result.has_more) {
        resultText += `\nMore results available. Use 'list_received_files' with cursor: ${result.cursor}`;
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
 * Handle check job status operation
 */
async function handleCheckJobStatus(args: any): Promise<CallToolResult> {
    const validatedArgs = schemas.CheckJobStatusSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.sharingCheckJobStatus({
        async_job_id: validatedArgs.async_job_id,
    });

    const result = response.result as any;
    let resultText = `Job Status for ID: ${validatedArgs.async_job_id}\n\n`;

    if (result['.tag'] === 'in_progress') {
        resultText += `Status: In Progress\n\nThe operation is still being processed. Please check again in a moment.`;
    } else if (result['.tag'] === 'complete') {
        resultText += `Status: Complete\n\nThe operation has finished successfully.`;
    } else if (result['.tag'] === 'failed') {
        resultText += `Status: Failed\n\nThe operation has failed. Please check the operation parameters and try again.`;
        if (result.failed) {
            resultText += `\n\nFailure Details: ${JSON.stringify(result.failed, null, 2)}`;
        }
    } else {
        resultText += `Status: ${result['.tag'] || 'Unknown'}\n\nUnexpected status returned.`;
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
 * Handler for sharing-related operations
 */
export async function handleSharingOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "dropbox_add_file_member":
            return await handleAddFileMember(args);
        case "dropbox_list_file_members":
            return await handleListFileMembers(args);
        case "dropbox_remove_file_member":
            return await handleRemoveFileMember(args);
        case "dropbox_share_folder":
            return await handleShareFolder(args);
        case "dropbox_list_folder_members":
            return await handleListFolderMembers(args);
        case "dropbox_add_folder_member":
            return await handleAddFolderMember(args);
        case "dropbox_remove_folder_member":
            return await handleRemoveFolderMember(args);
        case "dropbox_share_file":
            return await handleShareFile(args);
        case "dropbox_get_shared_links":
            return await handleGetSharedLinks(args);
        case "dropbox_unshare_file":
            return await handleUnshareFile(args);
        case "dropbox_unshare_folder":
            return await handleUnshareFolder(args);
        case "dropbox_list_shared_folders":
            return await handleListSharedFolders(args);
        case "dropbox_list_received_files":
            return await handleListReceivedFiles(args);
        case "dropbox_check_job_status":
            return await handleCheckJobStatus(args);
        default:
            throw new Error(`Unknown sharing operation: ${name}`);
    }
}
