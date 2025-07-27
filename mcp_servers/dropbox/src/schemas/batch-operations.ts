import { z } from "zod";

// Batch Operations Schemas
export const BatchDeleteSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file or folder to delete"),
    })).describe("List of files/folders to delete (up to 1000 entries)"),
});

export const BatchMoveSchema = z.object({
    entries: z.array(z.object({
        from_path: z.string().describe("Current path of the file or folder"),
        to_path: z.string().describe("New path for the file or folder"),
    })).describe("List of move operations to perform (up to 1000 entries)"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
    allow_ownership_transfer: z.boolean().optional().default(false).describe("Allow ownership transfer"),
});

export const BatchCopySchema = z.object({
    entries: z.array(z.object({
        from_path: z.string().describe("Path of the file or folder to copy"),
        to_path: z.string().describe("Destination path for the copy"),
    })).describe("List of copy operations to perform (up to 1000 entries)"),
    autorename: z.boolean().optional().default(false).describe("Automatically rename if destination already exists"),
});

// Batch Job Status Check Schema
export const BatchJobStatusSchema = z.object({
    async_job_id: z.string().describe("The async job ID returned from a batch operation"),
});

// File Locking Schemas
export const LockFileBatchSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file to lock"),
    })).describe("List of files to lock (up to 1000 entries)"),
});

export const UnlockFileBatchSchema = z.object({
    entries: z.array(z.object({
        path: z.string().describe("Path of the file to unlock"),
    })).describe("List of files to unlock (up to 1000 entries)"),
});
