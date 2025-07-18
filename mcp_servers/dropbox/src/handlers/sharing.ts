import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";
import { formatDropboxError, addCommonErrorGuidance } from "../utils/error-handling.js";

/**
 * Handler for sharing-related operations
 */
export async function handleSharingOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;
    const dropbox = getDropboxClient();

    switch (name) {
        case "add_file_member": {
            const validatedArgs = schemas.AddFileMemberSchema.parse(args);

            try {
                // First, get the file ID if a path was provided
                let fileId = validatedArgs.file;

                // If the file parameter doesn't start with "id:", treat it as a path and get the file ID
                if (!fileId.startsWith('id:')) {
                    try {
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
                    } catch (pathError: any) {
                        return {
                            content: [
                                {
                                    type: "text",
                                    text: `Failed to resolve file path to ID: "${validatedArgs.file}"\n\nError: ${pathError.status} - ${pathError.message || pathError.error_summary || 'Unknown error'}\n\nMake sure:\n- The file path is correct and starts with '/'\n- The file exists in your Dropbox\n- You have access to the file`,
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
            } catch (error: any) {
                let errorMessage = `Failed to add member(s) to file: "${validatedArgs.file}"\n`;

                // Add detailed error information from Dropbox API
                errorMessage += `\nDetailed Error Information:\n`;
                errorMessage += `- HTTP Status: ${error.status || 'Unknown'}\n`;
                errorMessage += `- Error Summary: ${error.error_summary || 'Not provided'}\n`;
                errorMessage += `- Error Message: ${error.message || 'Not provided'}\n`;

                // Add the full error object for debugging
                if (error.error) {
                    errorMessage += `- API Error Details: ${JSON.stringify(error.error, null, 2)}\n`;
                }

                if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Invalid parameters or file not shareable.\n\nCommon causes:\n- File ID is invalid or malformed\n- File doesn't exist or isn't accessible\n- Invalid email address format\n- File is not shareable (e.g., system files)\n- File must be owned by you to add members\n\nTry:\n- Verify the file exists and you own it\n- Check email address format\n- Ensure the file supports member sharing`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: File not found - The file "${validatedArgs.file}" doesn't exist.\n\nMake sure:\n- The file path/ID is correct\n- The file exists in your Dropbox\n- You have access to the file\n- The file hasn't been moved or deleted`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to add members to this file.\n\nThis could mean:\n- You're not the owner of the file\n- The file is in a shared folder with restricted permissions\n- Your access token lacks sharing permissions\n- The file sharing settings don't allow member additions`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Member addition failed due to a conflict.\n\nCommon causes:\n- Member is already added to this file\n- Email address is associated with the file owner\n- Concurrent member modifications\n- File sharing limit reached\n\nTry:\n- Check if the member is already added with 'list_file_members'\n- Use a different email address\n- Try again in a moment`;
                } else if (error.status === 401) {
                    errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\nCheck:\n- Access token is valid and not expired\n- Token has 'sharing.write' permission\n- You're authenticated with the correct Dropbox account`;
                } else if (error.status === 429) {
                    errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\nTips:\n- Wait a moment before trying again\n- Reduce the frequency of sharing requests\n- Add members in smaller batches`;
                } else {
                    errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\nGeneral tips:\n- Make sure the file is owned by you\n- Verify email addresses are valid\n- Check file permissions and ownership\n- Ensure the file supports member sharing`;
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

        case "list_file_members": {
            const validatedArgs = schemas.ListFileMembersSchema.parse(args);
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
            const validatedArgs = schemas.RemoveFileMemberSchema.parse(args);
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
            const validatedArgs = schemas.ShareFolderSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = formatDropboxError(error, "share folder", validatedArgs.path);

                // Add specific guidance for share_folder operation
                if (error.status === 409) {
                    errorMessage += `\nFolder sharing conflict - This folder is already shared or conflicts with existing sharing.\n\nCommon causes:\n- Folder is already shared (check with 'get_file_info')\n- Parent folder is already shared (can't share subfolder)\n- Folder contains shared subfolders\n- Another sharing operation is in progress\n- Folder name conflicts with existing shared folder\n\nTry:\n- Check if folder is already shared: use 'get_file_info' to see sharing status\n- Wait a moment and try again if operation is in progress\n- Use 'list_folder_members' if folder is already shared\n- Unshare the folder first, then reshare with new settings`;
                } else if (error.status === 400) {
                    errorMessage += `\nInvalid folder path or sharing parameters.\n\nCheck:\n- Folder path format (must start with '/' and be a valid folder)\n- Member policy: 'team' or 'anyone'\n- ACL update policy: 'owner' or 'editors'\n- Shared link policy: 'members' or 'anyone'\n- Path points to a folder, not a file`;
                } else {
                    // Use common error guidance for other status codes
                    errorMessage = addCommonErrorGuidance(errorMessage, error, {
                        resource: "folder",
                        operation: "share folder",
                        requiresOwnership: true
                    });
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

        case "list_folder_members": {
            const validatedArgs = schemas.ListFolderMembersSchema.parse(args);
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
            const validatedArgs = schemas.AddFolderMemberSchema.parse(args);
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

        case "share_file": {
            const validatedArgs = schemas.ShareFileSchema.parse(args);

            try {
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
            } catch (error: any) {
                let errorMessage = formatDropboxError(error, "share file", validatedArgs.path);

                if (error.status === 409) {
                    errorMessage += `\nSharing conflict - This file may already have a shared link.\n\nCommon causes:\n- File already has a shared link (use 'get_shared_links' to check)\n- Concurrent sharing operations\n- Sharing settings conflict\n\nTry:\n- Check existing shared links with 'get_shared_links'\n- Use existing shared link instead of creating a new one\n- Modify existing shared link settings`;
                } else {
                    errorMessage = addCommonErrorGuidance(errorMessage, error, {
                        resource: "file",
                        operation: "share file",
                        requiresOwnership: false
                    });
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

        case "get_shared_links": {
            const validatedArgs = schemas.GetSharedLinksSchema.parse(args);
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

        case "unshare_file": {
            const validatedArgs = schemas.UnshareFileSchema.parse(args);

            try {
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
            } catch (error: any) {
                const errorMessage = addCommonErrorGuidance(
                    formatDropboxError(error, "unshare_file", "unsharing the file"),
                    error
                );

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

        case "unshare_folder": {
            const validatedArgs = schemas.UnshareFolderSchema.parse(args);

            try {
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
            } catch (error: any) {
                const errorMessage = addCommonErrorGuidance(
                    formatDropboxError(error, "unshare_folder", "unsharing the folder"),
                    error
                );

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

        case "list_shared_folders": {
            const validatedArgs = schemas.ListSharedFoldersSchema.parse(args);

            try {
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
                    resultText += `\nMore results available. Use cursor: ${result.cursor}`;
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
                const errorMessage = addCommonErrorGuidance(
                    formatDropboxError(error, "list_shared_folders", "listing shared folders"),
                    error
                );

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

        case "list_received_files": {
            const validatedArgs = schemas.ListReceivedFilesSchema.parse(args);

            try {
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
                    resultText += `\nMore results available. Use cursor: ${result.cursor}`;
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
                const errorMessage = addCommonErrorGuidance(
                    formatDropboxError(error, "list_received_files", "listing received files"),
                    error
                );

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

        case "check_job_status": {
            const validatedArgs = schemas.CheckJobStatusSchema.parse(args);

            try {
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
            } catch (error: any) {
                const errorMessage = addCommonErrorGuidance(
                    formatDropboxError(error, "check_job_status", "checking job status"),
                    error
                );

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
            throw new Error(`Unknown sharing operation: ${name}`);
    }
}
