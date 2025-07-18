import { z } from "zod";

// Basic file and folder operations
export const ListFolderSchema = z.object({
    path: z.string().optional().default("").describe("Path of the folder to list (empty string for root)"),
    recursive: z.boolean().optional().default(false).describe("Whether to list contents recursively"),
    include_media_info: z.boolean().optional().default(false).describe("Include media info for photos and videos"),
    include_deleted: z.boolean().optional().default(false).describe("Include deleted files"),
    include_has_explicit_shared_members: z.boolean().optional().default(false).describe("Include shared member info"),
    limit: z.number().optional().describe("Maximum number of results to return"),
});

export const ListFolderContinueSchema = z.object({
    cursor: z.string().describe("Cursor from previous list_folder operation to continue listing"),
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
