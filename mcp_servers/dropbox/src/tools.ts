import { zodToJsonSchema } from "zod-to-json-schema";
import * as schemas from './schemas/index.js';

export const toolDefinitions = [
    {
        name: "list_folder",
        title: "Folder Listing",
        description: "Lists the contents of a folder",
        inputSchema: zodToJsonSchema(schemas.ListFolderSchema),
    },
    {
        name: "list_folder_continue",
        title: "Continue Folder Listing",
        description: "Continues listing folder contents using a cursor from previous list_folder operation",
        inputSchema: zodToJsonSchema(schemas.ListFolderContinueSchema),
    },
    {
        name: "create_folder",
        title: "Create New Folder",
        description: "Creates a new folder",
        inputSchema: zodToJsonSchema(schemas.CreateFolderSchema),
    },
    {
        name: "delete_file",
        title: "Delete File or Folder",
        description: "Deletes a file or folder",
        inputSchema: zodToJsonSchema(schemas.DeleteFileSchema),
    },
    {
        name: "move_file",
        title: "Move or Rename",
        description: "Moves or renames a file or folder",
        inputSchema: zodToJsonSchema(schemas.MoveFileSchema),
    },
    {
        name: "copy_file",
        title: "Copy File or Folder",
        description: "Creates a copy of a file or folder",
        inputSchema: zodToJsonSchema(schemas.CopyFileSchema),
    },
    {
        name: "search_files",
        title: "Search Files",
        description: "Searches for files and folders",
        inputSchema: zodToJsonSchema(schemas.SearchFilesSchema),
    },
    {
        name: "search_files_continue",
        title: "Continue File Search",
        description: "Continues searching files using a cursor from previous search_files operation",
        inputSchema: zodToJsonSchema(schemas.SearchFilesContinueSchema),
    },
    {
        name: "get_file_info",
        title: "Get File Info",
        description: "Gets metadata information about a file or folder",
        inputSchema: zodToJsonSchema(schemas.GetFileInfoSchema),
    },
    {
        name: "share_file",
        title: "Create Shared Link",
        description: "Creates a shared link for a file or folder. Advanced settings (password protection, expiration dates) require paid Dropbox accounts (Plus/Professional) or team membership. Basic accounts can only use 'public' visibility. If unsure about account capabilities, use 'get_current_account' first to check account type before setting advanced options.",
        inputSchema: zodToJsonSchema(schemas.ShareFileSchema),
    },
    {
        name: "get_shared_links",
        title: "List Shared Links",
        description: "Lists shared links for files and folders",
        inputSchema: zodToJsonSchema(schemas.GetSharedLinksSchema),
    },
    {
        name: "upload_file",
        title: "Upload File",
        description: "Uploads a local file to Dropbox using file:// URI. Reads the file directly from the local filesystem and uploads it as binary data.",
        inputSchema: zodToJsonSchema(schemas.UploadFileSchema),
    },
    {
        name: "download_file",
        title: "Download File",
        description: "Downloads a file from Dropbox",
        inputSchema: zodToJsonSchema(schemas.DownloadFileSchema),
    },
    {
        name: "list_revisions",
        title: "List File Revisions",
        description: "Lists the revisions of a file",
        inputSchema: zodToJsonSchema(schemas.ListRevisionsSchema),
    },
    {
        name: "restore_file",
        title: "Restore File Version",
        description: "Restores a file to a previous revision",
        inputSchema: zodToJsonSchema(schemas.RestoreFileSchema),
    },
    {
        name: "get_current_account",
        title: "Get Account Info",
        description: "Gets information about the current account. Returns account details including display name, email, and account ID in the format: 'Account: {display_name}\\nEmail: {email}\\nAccount ID: {account_id}'",
        inputSchema: zodToJsonSchema(schemas.GetCurrentAccountSchema),
    },
    {
        name: "get_space_usage",
        title: "Get Storage Usage",
        description: "Gets the current space usage information. Returns storage usage details including used bytes and allocated space in the format: 'Used: {used_bytes} bytes\\nAllocated: {allocated_bytes} bytes' for individual accounts, or 'Used: {used_bytes} bytes\\nAllocation Type: {type}' for other account types",
        inputSchema: zodToJsonSchema(schemas.GetSpaceUsageSchema),
    },
    {
        name: "get_temporary_link",
        title: "Get Temporary Link",
        description: "Gets a temporary link to a file",
        inputSchema: zodToJsonSchema(schemas.GetTemporaryLinkSchema),
    },
    {
        name: "add_file_member",
        title: "Add File Member",
        description: "Adds a member to a file",
        inputSchema: zodToJsonSchema(schemas.AddFileMemberSchema),
    },
    {
        name: "list_file_members",
        title: "List File Members",
        description: "Lists the members of a file",
        inputSchema: zodToJsonSchema(schemas.ListFileMembersSchema),
    },
    {
        name: "remove_file_member",
        title: "Remove File Member",
        description: "Removes a member from a file",
        inputSchema: zodToJsonSchema(schemas.RemoveFileMemberSchema),
    },
    {
        name: "share_folder",
        title: "Share Folder",
        description: "Shares a folder",
        inputSchema: zodToJsonSchema(schemas.ShareFolderSchema),
    },
    {
        name: "list_folder_members",
        title: "List Folder Members",
        description: "Lists the members of a shared folder",
        inputSchema: zodToJsonSchema(schemas.ListFolderMembersSchema),
    },
    {
        name: "add_folder_member",
        title: "Add Folder Member",
        description: "Adds a member to a shared folder",
        inputSchema: zodToJsonSchema(schemas.AddFolderMemberSchema),
    },
    {
        name: "list_shared_folders",
        title: "List Shared Folders",
        description: "Lists all shared folders that the current user has access to",
        inputSchema: zodToJsonSchema(schemas.ListSharedFoldersSchema),
    },
    {
        name: "unshare_file",
        title: "Unshare File",
        description: "Remove all members from this file. Does not remove inherited members.",
        inputSchema: zodToJsonSchema(schemas.UnshareFileSchema),
    },
    {
        name: "unshare_folder", 
        title: "Unshare Folder",
        description: "Allows a shared folder owner to unshare the folder. You'll need to call check_job_status to determine if the action has completed successfully.",
        inputSchema: zodToJsonSchema(schemas.UnshareFolderSchema),
    },
    {
        name: "create_file_request",
        title: "Create File Request",
        description: "Creates a file request",
        inputSchema: zodToJsonSchema(schemas.CreateFileRequestSchema),
    },
    {
        name: "get_file_request",
        title: "Get File Request",
        description: "Gets a file request by ID",
        inputSchema: zodToJsonSchema(schemas.GetFileRequestSchema),
    },
    {
        name: "list_file_requests",
        title: "List File Requests",
        description: "Lists all file requests",
        inputSchema: zodToJsonSchema(schemas.ListFileRequestsSchema),
    },
    {
        name: "delete_file_request",
        title: "Delete File Request",
        description: "Deletes file requests",
        inputSchema: zodToJsonSchema(schemas.DeleteFileRequestSchema),
    },
    {
        name: "update_file_request",
        title: "Update File Request",
        description: "Updates a file request (title, destination, description, open/close status)",
        inputSchema: zodToJsonSchema(schemas.UpdateFileRequestSchema),
    },
    {
        name: "batch_delete",
        title: "Batch Delete Files",
        description: "Deletes multiple files and folders in a single operation. This is an efficient way to delete many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry only needs a 'path' field.",
        inputSchema: zodToJsonSchema(schemas.BatchDeleteSchema),
    },
    {
        name: "batch_move",
        title: "Batch Move Files",
        description: "Moves or renames multiple files and folders in a single operation. This is an efficient way to move many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' and 'allow_ownership_transfer' apply to all entries.",
        inputSchema: zodToJsonSchema(schemas.BatchMoveSchema),
    },
    {
        name: "batch_copy",
        title: "Batch Copy Files",
        description: "Copies multiple files and folders in a single operation. This is an efficient way to copy many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' applies to all entries.",
        inputSchema: zodToJsonSchema(schemas.BatchCopySchema),
    },
    {
        name: "check_batch_job_status",
        title: "Check Batch Job Status",
        description: "Checks the status of a batch operation using the async job ID returned from batch operations. Use this to monitor progress and get final results of batch_copy, batch_move, or batch_delete operations. The tool automatically detects the operation type.",
        inputSchema: zodToJsonSchema(schemas.BatchJobStatusSchema),
    },
    {
        name: "get_thumbnail",
        title: "Get File Thumbnail",
        description: "Gets a thumbnail image for a file and returns it as binary image data with proper MIME type. The response contains the actual image that can be displayed directly by compatible clients.",
        inputSchema: zodToJsonSchema(schemas.GetThumbnailSchema),
    },
    {
        name: "save_url",
        title: "Save URL to Dropbox",
        description: "Downloads content from a URL and saves it as a file in Dropbox. This is useful for saving web content, images, documents, etc. directly from URLs.",
        inputSchema: zodToJsonSchema(schemas.SaveUrlSchema),
    },
    {
        name: "save_url_check_job_status",
        title: "Check URL Save Status",
        description: "Checks the status of a save URL operation using the async job ID. Use this to monitor the progress of URL downloads.",
        inputSchema: zodToJsonSchema(schemas.SaveUrlCheckJobStatusSchema),
    },
    {
        name: "lock_file_batch",
        title: "Lock Files (Batch)",
        description: "Temporarily locks files to prevent them from being edited by others. This is useful during collaborative work to avoid editing conflicts. NOTE: This may be an async operation that returns a job ID for status checking.",
        inputSchema: zodToJsonSchema(schemas.LockFileBatchSchema),
    },
    {
        name: "unlock_file_batch",
        title: "Unlock Files (Batch)",
        description: "Unlocks previously locked files, allowing others to edit them again. NOTE: This may be an async operation that returns a job ID for status checking.",
        inputSchema: zodToJsonSchema(schemas.UnlockFileBatchSchema),
    },
    {
        name: "list_received_files",
        title: "List Received Files",
        description: "Lists files that have been shared with the current user by others",
        inputSchema: zodToJsonSchema(schemas.ListReceivedFilesSchema),
    },
    {
        name: "check_job_status",
        title: "Check Job Status",
        description: "Checks the status of an asynchronous operation (like unshare_folder, share_folder, etc.)",
        inputSchema: zodToJsonSchema(schemas.CheckJobStatusSchema),
    },
    {
        name: "remove_folder_member",
        title: "Remove Folder Member",
        description: "Removes a member from a shared folder.",
        inputSchema: zodToJsonSchema(schemas.RemoveFolderMemberSchema),
    },
];
