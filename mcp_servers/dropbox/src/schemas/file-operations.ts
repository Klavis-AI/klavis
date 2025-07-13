import { z } from "zod";

export const UploadFileSchema = z.object({
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

export const DownloadFileSchema = z.object({
    path: z.string().describe("Path of the file to download"),
});

export const GetThumbnailSchema = z.object({
    path: z.string().describe("Path of the file to get thumbnail for"),
    format: z.enum(["jpeg", "png"]).optional().default("jpeg").describe("Image format for the thumbnail"),
    size: z.enum(["w32h32", "w64h64", "w128h128", "w256h256", "w480h320", "w640h480", "w960h640", "w1024h768", "w2048h1536"]).optional().default("w256h256").describe("Size of the thumbnail"),
});

export const GetPreviewSchema = z.object({
    path: z.string().describe("Path of the file to get preview for"),
});

export const GetTemporaryLinkSchema = z.object({
    path: z.string().describe("Path of the file to get temporary link for"),
});

export const ListRevisionsSchema = z.object({
    path: z.string().describe("Path of the file to get revisions for"),
    mode: z.enum(['path', 'id']).optional().default('path').describe("How to interpret the path"),
    limit: z.number().optional().default(10).describe("Maximum number of revisions to return"),
});

export const RestoreFileSchema = z.object({
    path: z.string().describe("Path of the file to restore"),
    rev: z.string().describe("Revision ID to restore to"),
});

// Save URL Schemas  
export const SaveUrlSchema = z.object({
    path: z.string().describe("Path where the file should be saved (e.g., '/folder/filename.ext')"),
    url: z.string().describe("URL to download and save to Dropbox"),
});

export const SaveUrlCheckJobStatusSchema = z.object({
    async_job_id: z.string().describe("The async job ID returned from save_url operation"),
});
