import { z } from "zod";

// File Requests Schemas
export const CreateFileRequestSchema = z.object({
    title: z.string().describe("The title of the file request"),
    destination: z.string().describe("The path of the folder where uploaded files will be sent"),
    description: z.string().optional().describe("Description of the file request"),
});

export const GetFileRequestSchema = z.object({
    id: z.string().describe("The ID of the file request"),
});

export const ListFileRequestsSchema = z.object({});

export const DeleteFileRequestSchema = z.object({
    ids: z.array(z.string()).describe("List of file request IDs to delete"),
});

export const UpdateFileRequestSchema = z.object({
    id: z.string().describe("The ID of the file request to update"),
    title: z.string().optional().describe("New title for the file request"),
    destination: z.string().optional().describe("New destination path for the file request"),
    description: z.string().optional().describe("New description for the file request"),
    open: z.boolean().optional().describe("Whether to open (true) or close (false) the file request"),
});
