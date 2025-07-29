import { z } from "zod";

export const ShareFileSchema = z.object({
    path: z.string().describe("Path of the file or folder to share"),
    settings: z.object({
        requested_visibility: z.enum(['public', 'team_only', 'password']).optional().describe("Link visibility. 'public' works for all accounts. 'team_only' and 'password' require team membership or paid accounts (Plus/Professional). If you're unsure about your account type, use 'get_current_account' first to check - look for account_type.tag and team fields"),
        link_password: z.string().optional().describe("Password for password-protected links. PAID FEATURE: Requires Dropbox Plus/Professional or team account. Will cause 'settings_error/not_authorized' on basic/free accounts. Check account type with 'get_current_account' before using"),
        expires: z.string().optional().describe("Expiration date (ISO 8601 format). PAID FEATURE: Requires Dropbox Plus/Professional or team account. Will cause 'settings_error/not_authorized' on basic/free accounts. Check account type with 'get_current_account' before using"),
    }).optional().describe("Share settings. For basic/free accounts: leave empty or use only 'requested_visibility': 'public'. Advanced settings require paid accounts - use 'get_current_account' to verify capabilities before setting password/expiration"),
});

export const GetSharedLinksSchema = z.object({
    path: z.string().optional().describe("Path to get shared links for (omit for all links)"),
    cursor: z.string().optional().describe("Cursor for pagination"),
});

export const AddFileMemberSchema = z.object({
    file: z.string().describe("File ID (format: 'id:...') or path of the file to add member to. Note: Dropbox API requires file ID, but path will be automatically converted."),
    members: z.array(z.object({
        email: z.string().describe("Email address of the member"),
        access_level: z.enum(['viewer', 'editor']).optional().default('viewer').describe("Access level for the member"),
    })).describe("List of members to add"),
    quiet: z.boolean().optional().default(false).describe("Whether to suppress notifications"),
    custom_message: z.string().optional().describe("Custom message to include in the invitation"),
});

export const ListFileMembersSchema = z.object({
    file: z.string().describe("Path of the file to list members for"),
    include_inherited: z.boolean().optional().default(true).describe("Include inherited permissions"),
    limit: z.number().optional().default(100).describe("Maximum number of members to return"),
});

export const RemoveFileMemberSchema = z.object({
    file: z.string().describe("Path of the file to remove member from"),
    member: z.string().describe("Email address of the member to remove"),
});

export const ShareFolderSchema = z.object({
    path: z.string().describe("Path of the folder to share"),
    member_policy: z.enum(['team', 'anyone']).optional().default('anyone').describe("Who can be a member of this shared folder. Only applicable if the current user is on a team"),
    acl_update_policy: z.enum(['owner', 'editors']).optional().default('owner').describe("Who can add and remove members"),
    shared_link_policy: z.enum(['anyone', 'members']).optional().default('anyone').describe("The policy to apply to shared links created for content inside this shared folder. The current user must be on a team to set this policy to 'members'"),
    force_async: z.boolean().optional().default(false).describe("Whether to force the share to happen asynchronously"),
    access_inheritance: z.enum(['inherit', 'no_inherit']).optional().default('inherit').describe("The access inheritance settings for the folder"),
});

export const ListFolderMembersSchema = z.object({
    shared_folder_id: z.string().describe("ID of the shared folder"),
    limit: z.number().optional().default(100).describe("Maximum number of members to return"),
});

export const AddFolderMemberSchema = z.object({
    shared_folder_id: z.string().describe("ID of the shared folder"),
    members: z.array(z.object({
        email: z.string().describe("Email address of the member"),
        access_level: z.enum(['viewer', 'editor', 'owner']).optional().default('viewer').describe("Access level for the member"),
    })).describe("List of members to add"),
    quiet: z.boolean().optional().default(false).describe("Whether to suppress notifications"),
    custom_message: z.string().optional().describe("Custom message to include in the invitation"),
});

export const UnshareFileSchema = z.object({
    file: z.string().min(1).describe("The file to unshare. Can be a file ID (format: 'id:...') or path."),
});

export const UnshareFolderSchema = z.object({
    shared_folder_id: z.string().describe("The ID for the shared folder"),
    leave_a_copy: z.boolean().optional().default(false).describe("If true, members of this shared folder will get a copy of this folder after it's unshared. Otherwise, it will be removed from their Dropbox."),
});

export const ListSharedFoldersSchema = z.object({
    limit: z.number().optional().default(100).describe("Maximum number of shared folders to return"),
    cursor: z.string().optional().describe("Cursor from previous list_shared_folders call to continue listing - use this to get the next page of results"),
});

export const ListReceivedFilesSchema = z.object({
    limit: z.number().optional().default(100).describe("Maximum number of received files to return"),
    cursor: z.string().optional().describe("Cursor from previous list_received_files call to continue listing - use this to get the next page of results"),
});

export const CheckJobStatusSchema = z.object({
    async_job_id: z.string().min(1).describe("The async job ID returned from a sharing operation"),
});

export const RemoveFolderMemberSchema = z.object({
    shared_folder_id: z.string().describe("The ID for the shared folder."),
    member: z.string().describe("Email address of the member to remove"),
    leave_a_copy: z.boolean().describe("If true, the removed user will keep their copy of the folder after it's unshared."),
});
