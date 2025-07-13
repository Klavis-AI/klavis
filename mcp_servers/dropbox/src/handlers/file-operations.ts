import { getDropboxClient } from '../utils/context.js';
import {
    UploadFileSchema,
    DownloadFileSchema,
    GetThumbnailSchema,
    GetPreviewSchema,
    GetTemporaryLinkSchema,
    ListRevisionsSchema,
    RestoreFileSchema,
    SaveUrlSchema,
    SaveUrlCheckJobStatusSchema
} from '../schemas/index.js';
import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";

export async function handleUploadFile(args: any) {
    const validatedArgs = UploadFileSchema.parse(args);
    const dropbox = getDropboxClient();

    // Convert content to buffer based on provided content type
    let fileContent: Buffer;

    if (validatedArgs.text_content) {
        // Handle plain text content
        fileContent = Buffer.from(validatedArgs.text_content, 'utf8');
    } else if (validatedArgs.base64_content) {
        // Handle base64 encoded content
        try {
            fileContent = Buffer.from(validatedArgs.base64_content, 'base64');
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `❌ Invalid base64 content provided. Please ensure the base64_content is properly encoded.`,
                    },
                ],
            };
        }
    } else {
        // This should not happen due to schema validation, but just in case
        return {
            content: [
                {
                    type: "text",
                    text: `❌ No content provided. Please specify either text_content or base64_content.`,
                },
            ],
        };
    }

    const response = await dropbox.filesUpload({
        path: validatedArgs.path,
        contents: fileContent,
        mode: validatedArgs.mode as any,
        autorename: validatedArgs.autorename,
        mute: validatedArgs.mute,
    });

    const contentType = validatedArgs.text_content ? 'text' : 'base64';
    const contentLength = validatedArgs.text_content ? validatedArgs.text_content.length : validatedArgs.base64_content!.length;

    return {
        content: [
            {
                type: "text",
                text: `✅ File uploaded successfully!\n\n📄 File: ${response.result.path_display}\n📏 Size: ${response.result.size} bytes\n📝 Content type: ${contentType}\n📊 Input length: ${contentLength} characters`,
            },
        ],
    };
}

export async function handleDownloadFile(args: any) {
    const validatedArgs = DownloadFileSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesDownload({
            path: validatedArgs.path,
        });

        // The response from filesDownload contains the file data directly
        const result = response.result as any;

        // Extract metadata
        const fileName = result.name || 'Unknown file';
        const fileSize = result.size || 'Unknown size';
        const filePath = result.path_display || validatedArgs.path;

        let fileBuffer: Buffer | undefined;

        // Extract file content - according to official SDK examples, it's in result.fileBinary
        if (result.fileBinary) {
            if (Buffer.isBuffer(result.fileBinary)) {
                fileBuffer = result.fileBinary;
            } else {
                try {
                    fileBuffer = Buffer.from(result.fileBinary);
                } catch (e) {
                    if (typeof result.fileBinary === 'string') {
                        fileBuffer = Buffer.from(result.fileBinary, 'binary');
                    } else if (result.fileBinary.constructor === Uint8Array) {
                        fileBuffer = Buffer.from(result.fileBinary);
                    }
                }
            }
        } else if (Buffer.isBuffer(result)) {
            fileBuffer = result;
        }

        if (fileBuffer) {
            // Try to detect if it's text content
            let isTextContent = false;
            let textContent = '';

            try {
                textContent = fileBuffer.toString('utf8');
                // Simple heuristic: if it contains mostly printable characters, treat as text
                const printableRatio = textContent.split('').filter(char => 
                    /[\x20-\x7E\s]/.test(char)
                ).length / textContent.length;
                
                isTextContent = printableRatio > 0.9 && textContent.length > 0;
            } catch (e) {
                isTextContent = false;
            }

            if (isTextContent && textContent.length < 10000) { // Limit text display to 10KB
                return {
                    content: [
                        {
                            type: "text",
                            text: `📄 Downloaded file: ${fileName}\n📍 Path: ${filePath}\n📏 Size: ${fileSize} bytes\n\n📋 File content (text):\n\n${textContent}`,
                        },
                    ],
                };
            } else {
                // For binary files or large text files, provide base64
                const base64Content = fileBuffer.toString('base64');
                return {
                    content: [
                        {
                            type: "text",
                            text: `📄 Downloaded file: ${fileName}\n📍 Path: ${filePath}\n📏 Size: ${fileSize} bytes\n\n📊 File content (base64):\n\n${base64Content}`,
                        },
                    ],
                };
            }
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `❌ Failed to extract file content from download response. Metadata:\n📄 File: ${fileName}\n📍 Path: ${filePath}\n📏 Size: ${fileSize} bytes`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to download file: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\n💡 Make sure:\n• The file path is correct\n• The file exists\n• You have access to the file`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 You may not have download access to this file`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: This path points to a folder, not a file.\n\n💡 Use a file path, not a folder path`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

export async function handleGetThumbnail(args: any) {
    const validatedArgs = GetThumbnailSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesGetThumbnailV2({
            resource: { ".tag": "path", path: validatedArgs.path },
            format: { ".tag": validatedArgs.format },
            size: { ".tag": validatedArgs.size },
        });

        const result = response.result as any;
        
        if (result.fileBinary) {
            const thumbnailBuffer = Buffer.isBuffer(result.fileBinary) 
                ? result.fileBinary 
                : Buffer.from(result.fileBinary);
            
            const base64Thumbnail = thumbnailBuffer.toString('base64');
            
            return {
                content: [
                    {
                        type: "text",
                        text: `🖼️ Thumbnail generated for: ${validatedArgs.path}\n📏 Format: ${validatedArgs.format}\n📐 Size: ${validatedArgs.size}\n📊 Thumbnail size: ${thumbnailBuffer.length} bytes\n\n🖼️ Thumbnail (base64):\n\n${base64Thumbnail}`,
                    },
                ],
            };
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `❌ Failed to generate thumbnail for: ${validatedArgs.path}\nNo thumbnail data received from Dropbox.`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to get thumbnail for: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\n💡 Make sure the file exists and the path is correct`;
        } else if (error.status === 415) {
            errorMessage += `\nError 415: Unsupported file type.\n\n💡 Thumbnails are only available for:\n• Images (JPEG, PNG, GIF, BMP, TIFF)\n• Videos (MP4, MOV, AVI, etc.)\n• Documents (PDF, DOC, DOCX, etc.)`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 You may not have access to this file`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

export async function handleGetPreview(args: any) {
    const validatedArgs = GetPreviewSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesGetPreview({
            path: validatedArgs.path,
        });

        const result = response.result as any;
        
        if (result.fileBinary) {
            const previewBuffer = Buffer.isBuffer(result.fileBinary) 
                ? result.fileBinary 
                : Buffer.from(result.fileBinary);
            
            const base64Preview = previewBuffer.toString('base64');
            
            return {
                content: [
                    {
                        type: "text",
                        text: `📋 Preview generated for: ${validatedArgs.path}\n📏 Preview size: ${previewBuffer.length} bytes\n\n📄 Preview (base64):\n\n${base64Preview}`,
                    },
                ],
            };
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `❌ Failed to generate preview for: ${validatedArgs.path}\nNo preview data received from Dropbox.`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to get preview for: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\n💡 Make sure the file exists and the path is correct`;
        } else if (error.status === 415) {
            errorMessage += `\nError 415: Unsupported file type.\n\n💡 Previews are only available for:\n• Documents (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX)\n• Text files\n• Images`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 You may not have access to this file`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

export async function handleGetTemporaryLink(args: any) {
    const validatedArgs = GetTemporaryLinkSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesGetTemporaryLink({
        path: validatedArgs.path,
    });

    return {
        content: [
            {
                type: "text",
                text: `Temporary link: ${response.result.link}`,
            },
        ],
    };
}

export async function handleListRevisions(args: any) {
    const validatedArgs = ListRevisionsSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesListRevisions({
        path: validatedArgs.path,
        mode: validatedArgs.mode as any,
        limit: validatedArgs.limit,
    });

    const revisions = (response.result as any).entries?.map((rev: any) =>
        `Revision ID: ${rev.rev} - Modified: ${rev.server_modified} - Size: ${rev.size} bytes`
    ) || [];

    return {
        content: [
            {
                type: "text",
                text: `Revisions for file "${validatedArgs.path}":\n\n${revisions.join('\n') || 'No revisions found'}`,
            },
        ],
    };
}

export async function handleRestoreFile(args: any) {
    const validatedArgs = RestoreFileSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesRestore({
        path: validatedArgs.path,
        rev: validatedArgs.rev,
    });

    return {
        content: [
            {
                type: "text",
                text: `File restored to revision ${validatedArgs.rev}: ${(response.result as any).path_display}`,
            },
        ],
    };
}

export async function handleSaveUrl(args: any) {
    const validatedArgs = SaveUrlSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesSaveUrl({
            path: validatedArgs.path,
            url: validatedArgs.url,
        });

        if (response.result['.tag'] === 'complete') {
            const result = response.result as any;
            return {
                content: [
                    {
                        type: "text",
                        text: `✅ URL saved successfully!\n\n📄 File: ${result.path_display || validatedArgs.path}\n🔗 Source URL: ${validatedArgs.url}\n📏 Size: ${result.size || 'Unknown'} bytes`,
                    },
                ],
            };
        } else if (response.result['.tag'] === 'async_job_id') {
            return {
                content: [
                    {
                        type: "text",
                        text: `⏳ URL save started (async operation)\nJob ID: ${response.result.async_job_id}\n\n🔗 Source URL: ${validatedArgs.url}\n📄 Destination: ${validatedArgs.path}\n\n💡 Use 'save_url_check_job_status' with this Job ID to check progress.`,
                    },
                ],
            };
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `URL save initiated for: ${validatedArgs.url} -> ${validatedArgs.path}`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to save URL: "${validatedArgs.url}" to "${validatedArgs.path}"\n`;

        if (error.status === 400) {
            errorMessage += `\nError 400: Invalid URL or path.\n\n💡 Check:\n• URL is valid and accessible\n• Destination path is valid (starts with '/')\n• URL points to a downloadable file`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\n💡 You may not have write access to the destination folder`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: File already exists at the destination path.\n\n💡 Try:\n• Using a different filename\n• The URL content may have already been saved`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

export async function handleSaveUrlCheckJobStatus(args: any) {
    const validatedArgs = SaveUrlCheckJobStatusSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        const response = await dropbox.filesSaveUrlCheckJobStatus({
            async_job_id: validatedArgs.async_job_id,
        });

        const result = response.result;

        if (result['.tag'] === 'in_progress') {
            return {
                content: [
                    {
                        type: "text",
                        text: `⏳ URL save operation is still in progress.\nJob ID: ${validatedArgs.async_job_id}\nStatus: Processing...`,
                    },
                ],
            };
        } else if (result['.tag'] === 'complete') {
            const completeResult = result as any;
            return {
                content: [
                    {
                        type: "text",
                        text: `✅ URL save completed!\nJob ID: ${validatedArgs.async_job_id}\n📄 File: ${completeResult.path_display}\n📏 Size: ${completeResult.size} bytes`,
                    },
                ],
            };
        } else if (result['.tag'] === 'failed') {
            const failedResult = result as any;
            return {
                content: [
                    {
                        type: "text",
                        text: `❌ URL save failed.\nJob ID: ${validatedArgs.async_job_id}\nError: ${failedResult.reason || 'Unknown error'}`,
                    },
                ],
            };
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `URL save status: ${result['.tag'] || 'Unknown'}\nJob ID: ${validatedArgs.async_job_id}`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to check save URL job status for ID: ${validatedArgs.async_job_id}\n`;

        if (error.status === 400) {
            errorMessage += `\nError 400: Invalid job ID.\n\n💡 The job ID may be malformed or expired`;
        } else if (error.status === 404) {
            errorMessage += `\nError 404: Job not found.\n\n💡 The job ID may be invalid or the job may have been cleaned up`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

/**
 * Main handler for file operations
 */
export async function handleFileOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "upload_file":
            return await handleUploadFile(args) as CallToolResult;
        case "download_file":
            return await handleDownloadFile(args) as CallToolResult;
        case "get_thumbnail":
            return await handleGetThumbnail(args) as CallToolResult;
        case "list_revisions":
            return await handleListRevisions(args) as CallToolResult;
        case "restore_file":
            return await handleRestoreFile(args) as CallToolResult;
        default:
            throw new Error(`Unknown file operation: ${name}`);
    }
}
