import { zodToJsonSchema } from "zod-to-json-schema";
import * as schemas from './schemas/index.js';

export const toolDefinitions = [
    {
        name: "list_folder",
        description: "Lists the contents of a folder",
        inputSchema: zodToJsonSchema(schemas.ListFolderSchema),
    },
    {
        name: "list_folder_continue",
        description: "Continues listing folder contents using a cursor from previous list_folder operation",
        inputSchema: zodToJsonSchema(schemas.ListFolderContinueSchema),
    },
    {
        name: "create_folder",
        description: "Creates a new folder",
        inputSchema: zodToJsonSchema(schemas.CreateFolderSchema),
    },
    {
        name: "delete_file",
        description: "Deletes a file or folder",
        inputSchema: zodToJsonSchema(schemas.DeleteFileSchema),
    },
    {
        name: "move_file",
        description: "Moves or renames a file or folder",
        inputSchema: zodToJsonSchema(schemas.MoveFileSchema),
    },
    {
        name: "copy_file",
        description: "Creates a copy of a file or folder",
        inputSchema: zodToJsonSchema(schemas.CopyFileSchema),
    },
    {
        name: "search_files",
        description: "Searches for files and folders",
        inputSchema: zodToJsonSchema(schemas.SearchFilesSchema),
    },
    {
        name: "get_file_info",
        description: "Gets metadata information about a file or folder",
        inputSchema: zodToJsonSchema(schemas.GetFileInfoSchema),
    },
    {
        name: "share_file",
        description: "Creates a shared link for a file or folder",
        inputSchema: zodToJsonSchema(schemas.ShareFileSchema),
    },
    {
        name: "get_shared_links",
        description: "Lists shared links for files and folders",
        inputSchema: zodToJsonSchema(schemas.GetSharedLinksSchema),
    },
    {
        name: "upload_file",
        description: "Uploads a local file to Dropbox using file:// URI. Reads the file directly from the local filesystem and uploads it as binary data.",
        inputSchema: zodToJsonSchema(schemas.UploadFileSchema),
    },
    {
        name: "download_file",
        description: "Downloads a file from Dropbox",
        inputSchema: zodToJsonSchema(schemas.DownloadFileSchema),
    },
    {
        name: "list_revisions",
        description: "Lists the revisions of a file",
        inputSchema: zodToJsonSchema(schemas.ListRevisionsSchema),
    },
    {
        name: "restore_file",
        description: "Restores a file to a previous revision",
        inputSchema: zodToJsonSchema(schemas.RestoreFileSchema),
    },
    {
        name: "get_current_account",
        description: "Gets information about the current account",
        inputSchema: zodToJsonSchema(schemas.GetCurrentAccountSchema),
    },
    {
        name: "get_space_usage",
        description: "Gets the current space usage information",
        inputSchema: zodToJsonSchema(schemas.GetSpaceUsageSchema),
    },
    {
        name: "get_temporary_link",
        description: "Gets a temporary link to a file",
        inputSchema: zodToJsonSchema(schemas.GetTemporaryLinkSchema),
    },
    {
        name: "get_preview",
        description: "Gets a preview of a file. Returns image content type for image files, text content for HTML previews, and base64 data for PDF/document previews. PDF previews are generated for files with the following extensions: .ai, .doc, .docm, .docx, .eps, .gdoc, .gslides, .odp, .odt, .pps, .ppsm, .ppsx, .ppt, .pptm, .pptx, .rtf. HTML previews are generated for files with the following extensions: .csv, .ods, .xls, .xlsm, .gsheet, .xlsx.",
        inputSchema: zodToJsonSchema(schemas.GetPreviewSchema),
    },
    {
        name: "add_file_member",
        description: "Adds a member to a file",
        inputSchema: zodToJsonSchema(schemas.AddFileMemberSchema),
    },
    {
        name: "list_file_members",
        description: "Lists the members of a file",
        inputSchema: zodToJsonSchema(schemas.ListFileMembersSchema),
    },
    {
        name: "remove_file_member",
        description: "Removes a member from a file",
        inputSchema: zodToJsonSchema(schemas.RemoveFileMemberSchema),
    },
    {
        name: "share_folder",
        description: "Shares a folder",
        inputSchema: zodToJsonSchema(schemas.ShareFolderSchema),
    },
    {
        name: "list_folder_members",
        description: "Lists the members of a shared folder",
        inputSchema: zodToJsonSchema(schemas.ListFolderMembersSchema),
    },
    {
        name: "add_folder_member",
        description: "Adds a member to a shared folder",
        inputSchema: zodToJsonSchema(schemas.AddFolderMemberSchema),
    },
    {
        name: "list_shared_folders",
        description: "Lists all shared folders that the current user has access to",
        inputSchema: zodToJsonSchema(schemas.ListSharedFoldersSchema),
    },
    {
        name: "unshare_file",
        description: "Remove all members from this file. Does not remove inherited members.",
        inputSchema: zodToJsonSchema(schemas.UnshareFileSchema),
    },
    {
        name: "unshare_folder", 
        description: "Allows a shared folder owner to unshare the folder. You'll need to call check_job_status to determine if the action has completed successfully.",
        inputSchema: zodToJsonSchema(schemas.UnshareFolderSchema),
    },
    {
        name: "create_file_request",
        description: "Creates a file request",
        inputSchema: zodToJsonSchema(schemas.CreateFileRequestSchema),
    },
    {
        name: "get_file_request",
        description: "Gets a file request by ID",
        inputSchema: zodToJsonSchema(schemas.GetFileRequestSchema),
    },
    {
        name: "list_file_requests",
        description: "Lists all file requests",
        inputSchema: zodToJsonSchema(schemas.ListFileRequestsSchema),
    },
    {
        name: "delete_file_request",
        description: "Deletes file requests",
        inputSchema: zodToJsonSchema(schemas.DeleteFileRequestSchema),
    },
    {
        name: "update_file_request",
        description: "Updates a file request (title, destination, description, open/close status)",
        inputSchema: zodToJsonSchema(schemas.UpdateFileRequestSchema),
    },
    {
        name: "batch_delete",
        description: "Deletes multiple files and folders in a single operation. This is an efficient way to delete many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry only needs a 'path' field.",
        inputSchema: zodToJsonSchema(schemas.BatchDeleteSchema),
    },
    {
        name: "batch_move",
        description: "Moves or renames multiple files and folders in a single operation. This is an efficient way to move many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' and 'allow_ownership_transfer' apply to all entries.",
        inputSchema: zodToJsonSchema(schemas.BatchMoveSchema),
    },
    {
        name: "batch_copy",
        description: "Copies multiple files and folders in a single operation. This is an efficient way to copy many items at once. NOTE: This may be an async operation that returns a job ID for status checking. Each entry needs 'from_path' and 'to_path' fields. Optional top-level 'autorename' applies to all entries.",
        inputSchema: zodToJsonSchema(schemas.BatchCopySchema),
    },
    {
        name: "check_batch_job_status",
        description: "Checks the status of a batch operation using the async job ID returned from batch operations. Use this to monitor progress and get final results of batch_copy, batch_move, or batch_delete operations. The tool automatically detects the operation type.",
        inputSchema: zodToJsonSchema(schemas.BatchJobStatusSchema),
    },
    {
        name: "get_thumbnail",
        description: "Gets a thumbnail image for a file and returns it as binary image data with proper MIME type. The response contains the actual image that can be displayed directly by compatible clients.",
        inputSchema: zodToJsonSchema(schemas.GetThumbnailSchema),
    },
    {
        name: "add_file_properties",
        description: "Adds custom properties to a file. Properties are key-value pairs that can be used to store custom metadata about files.",
        inputSchema: zodToJsonSchema(schemas.AddFilePropertiesSchema),
    },
    {
        name: "overwrite_file_properties",
        description: "Overwrites custom properties on a file. This replaces all existing properties for the specified templates.",
        inputSchema: zodToJsonSchema(schemas.OverwriteFilePropertiesSchema),
    },
    {
        name: "update_file_properties",
        description: "Updates custom properties on a file. This allows you to add, update, or remove specific property fields.",
        inputSchema: zodToJsonSchema(schemas.UpdateFilePropertiesSchema),
    },
    {
        name: "remove_file_properties",
        description: "Removes custom properties from a file by removing entire property templates.",
        inputSchema: zodToJsonSchema(schemas.RemoveFilePropertiesSchema),
    },
    {
        name: "search_file_properties",
        description: "Searches for files based on their custom properties. You can search by property field names or values.",
        inputSchema: zodToJsonSchema(schemas.SearchFilePropertiesSchema),
    },
    {
        name: "list_property_templates",
        description: "Lists all available property templates for your account. Templates define the structure of custom properties.",
        inputSchema: zodToJsonSchema(schemas.ListPropertyTemplatesSchema),
    },
    {
        name: "get_property_template",
        description: "Gets detailed information about a specific property template, including its fields and types.",
        inputSchema: zodToJsonSchema(schemas.GetPropertyTemplateSchema),
    },
    {
        name: "save_url",
        description: "Downloads content from a URL and saves it as a file in Dropbox. This is useful for saving web content, images, documents, etc. directly from URLs.",
        inputSchema: zodToJsonSchema(schemas.SaveUrlSchema),
    },
    {
        name: "save_url_check_job_status",
        description: "Checks the status of a save URL operation using the async job ID. Use this to monitor the progress of URL downloads.",
        inputSchema: zodToJsonSchema(schemas.SaveUrlCheckJobStatusSchema),
    },
    {
        name: "lock_file_batch",
        description: "Temporarily locks files to prevent them from being edited by others. This is useful during collaborative work to avoid editing conflicts. NOTE: This may be an async operation that returns a job ID for status checking.",
        inputSchema: zodToJsonSchema(schemas.LockFileBatchSchema),
    },
    {
        name: "unlock_file_batch",
        description: "Unlocks previously locked files, allowing others to edit them again. NOTE: This may be an async operation that returns a job ID for status checking.",
        inputSchema: zodToJsonSchema(schemas.UnlockFileBatchSchema),
    },
    {
        name: "list_received_files",
        description: "Lists files that have been shared with the current user by others",
        inputSchema: zodToJsonSchema(schemas.ListReceivedFilesSchema),
    },
    {
        name: "check_job_status",
        description: "Checks the status of an asynchronous operation (like unshare_folder, share_folder, etc.)",
        inputSchema: zodToJsonSchema(schemas.CheckJobStatusSchema),
    },
];
