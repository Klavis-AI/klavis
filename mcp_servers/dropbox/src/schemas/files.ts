import { z } from "zod";

// Basic file and folder operations
export const ListFolderSchema = z.object({
    path: z.string().optional().default("").describe("A unique identifier for the file. Can be a path (/(.|[\\r\\n])*)?), file ID (id:.*), or namespace ID (ns:[0-9]+(/.*)?). Empty string for root folder."),
    recursive: z.boolean().optional().default(false).describe("If true, the list folder operation will be applied recursively to all subfolders and the response will contain contents of all subfolders. Note: In some cases, setting recursive to true may lead to performance issues or errors, especially when traversing folder structures with a large number of items. A workaround is to set recursive to false and traverse subfolders one at a time."),
    include_media_info: z.boolean().optional().default(false).describe("DEPRECATED: Field is deprecated. If true, FileMetadata.media_info is set for photo and video. This parameter will no longer have an effect starting December 2, 2019."),
    include_deleted: z.boolean().optional().default(false).describe("If true, the results will include entries for files and folders that used to exist but were deleted."),
    include_has_explicit_shared_members: z.boolean().optional().default(false).describe("If true, the results will include a flag for each file indicating whether or not that file has any explicit members."),
    include_mounted_folders: z.boolean().optional().default(true).describe("If true, the results will include entries under mounted folders which includes app folder, shared folder and team folder."),
    limit: z.number().min(1).max(2000).optional().describe("The maximum number of results to return per request. Note: This is an approximate number and there can be slightly more entries returned in some cases."),
    include_non_downloadable_files: z.boolean().optional().default(true).describe("If true, include files that are not downloadable, i.e. Google Docs."),
});

export const ListFolderContinueSchema = z.object({
    cursor: z.string().describe("\"Cursor\" from previous list_folder/_continue operation to continue listing"),
});

export const CreateFolderSchema = z.object({
    path: z.string().describe("Path of the folder to create"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename folder if it already exists"),
});

export const DeleteFileSchema = z.object({
    path: z.string().describe("Path of the file or folder to delete"),
});

export const MoveFileSchema = z.object({
    from_path: z.string().describe("Current path of the file or folder"),
    to_path: z.string().describe("New path for the file or folder"),
    allow_shared_folder: z.boolean().optional().default(false).describe("Allow moving shared folders"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

export const CopyFileSchema = z.object({
    from_path: z.string().describe("Path of the file or folder to copy"),
    to_path: z.string().describe("Destination path for the copy"),
    allow_shared_folder: z.boolean().optional().default(false).describe("Allow copying shared folders"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

export const GetFileInfoSchema = z.object({
    path: z.string().describe("Path of the file to get information about"),
    include_media_info: z.boolean().optional().default(false).describe("Include media info for photos and videos"),
    include_deleted: z.boolean().optional().default(false).describe("Include deleted files"),
    include_has_explicit_shared_members: z.boolean().optional().default(false).describe("Include shared member info"),
});

export const SearchFilesSchema = z.object({
    query: z.string().describe("Search query for finding files"),
    path: z.string().optional().default("").describe("Path to search within (empty for entire Dropbox)"),
    max_results: z.number().optional().default(100).describe("Maximum number of search results"),
    file_status: z.enum(['active', 'deleted']).optional().default('active').describe("File status to search for"),
    filename_only: z.boolean().optional().default(false).describe("Search only in filenames"),
});

export const SearchFilesContinueSchema = z.object({
    cursor: z.string().min(1).describe("Cursor from previous search files operation to continue listing"),
});
