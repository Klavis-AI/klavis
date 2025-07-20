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
import { CallToolRequest, CallToolResult, ImageContent, } from "@modelcontextprotocol/sdk/types.js";
import { readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { stat } from 'fs/promises';
import { lookup } from 'mime-types';

/**
 * Creates an ImageContent object for MCP responses
 */
function createImageContent(base64Data: string, mimeType: string): ImageContent {
    return {
        type: "image" as const,
        data: base64Data,
        mimeType: mimeType,
    };
}

/**
 * Detects file type and MIME type based on file extension using mime-types library
 */
export function detectFileType(fileName: string): { mimeType: string; contentType: 'image' | 'text' | 'binary' } {
    // Use mime-types library to get MIME type from filename
    const mimeType = lookup(fileName) || 'application/octet-stream';

    // Determine content type category based on MIME type
    if (mimeType.startsWith('image/')) {
        return { mimeType, contentType: 'image' };
    }

    if (mimeType.startsWith('text/') ||
        ['application/json', 'application/xml', 'application/javascript', 'application/typescript'].includes(mimeType)) {
        return { mimeType, contentType: 'text' };
    }

    // Everything else is binary
    return { mimeType, contentType: 'binary' };
}

export async function handleUploadFile(args: any) {
    const validatedArgs = UploadFileSchema.parse(args);
    const dropbox = getDropboxClient();

    try {
        // Parse the file:// URI to get the local file path
        let localFilePath: string;
        try {
            localFilePath = fileURLToPath(validatedArgs.local_file_uri);
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Invalid file URI: ${validatedArgs.local_file_uri}\nPlease use a valid file:// URI format (e.g., 'file:///absolute/path/to/file')`,
                    },
                ],
            };
        }

        // Check if file exists and get file stats
        let fileStats;
        try {
            fileStats = await stat(localFilePath);
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `File not found: ${localFilePath}\nPlease ensure the file exists and the path is correct.`,
                    },
                ],
            };
        }

        // Check if it's a regular file (not a directory)
        if (!fileStats.isFile()) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Path is not a file: ${localFilePath}\nPlease provide a path to a regular file, not a directory.`,
                    },
                ],
            };
        }

        // Read the file as binary data
        let fileContent: Buffer;
        try {
            fileContent = await readFile(localFilePath);
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to read file: ${localFilePath}\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
                    },
                ],
            };
        }

        // Upload to Dropbox
        const response = await dropbox.filesUpload({
            path: validatedArgs.dropbox_path,
            contents: fileContent,
            mode: validatedArgs.mode as any,
            autorename: validatedArgs.autorename,
            mute: validatedArgs.mute,
        });

        return {
            content: [
                {
                    type: "text",
                    text: `File uploaded successfully!\n\nLocal file: ${localFilePath}\nDropbox path: ${response.result.path_display}\nFile size: ${response.result.size} bytes (${(response.result.size / 1024).toFixed(2)} KB)\nLocal file size: ${fileStats.size} bytes\nUpload mode: ${validatedArgs.mode}\nAutorename: ${validatedArgs.autorename}`,
                },
            ],
        };
    } catch (error: any) {
        let errorMessage = `Failed to upload file from ${validatedArgs.local_file_uri} to ${validatedArgs.dropbox_path}\n`;

        if (error.status === 400) {
            errorMessage += `\nError 400: Bad request - Check the Dropbox path format.\n\nPath requirements:\n- Must start with '/' (e.g., '/Documents/file.txt')\n- Use forward slashes (/) not backslashes (\\)\n- Avoid special characters that aren't URL-safe\n- Include the filename in the path`;
        } else if (error.status === 401) {
            errorMessage += `\nError 401: Unauthorized - Your access token may be invalid or expired.\n\nCheck:\n- Access token is valid and not expired\n- Token has 'files.content.write' permission\n- You're authenticated with the correct Dropbox account`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied - You don't have permission to upload to this location.\n\nThis could mean:\n- The destination folder is read-only\n- You don't have write access to the folder\n- The folder is in a shared space with restricted permissions`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: Conflict - A file with this name already exists.\n\nOptions:\n- Set autorename=true to automatically rename the file\n- Use mode='overwrite' to replace the existing file\n- Choose a different filename`;
        } else if (error.status === 429) {
            errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\nTry:\n- Waiting a moment before retrying\n- Reducing the frequency of uploads\n- Uploading smaller files or fewer files at once`;
        } else {
            errorMessage += `\nError ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}\n\nGeneral troubleshooting:\n- Check your internet connection\n- Verify the Dropbox path is valid\n- Ensure the local file is accessible\n- Confirm proper authentication`;
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

            // Return a resource URI instead of file content
            const resourceUri = `dropbox://${validatedArgs.path}`;

            return {
                content: [
                    {
                        type: "text",
                        text: `Use resources/read to access the file content at: ${resourceUri}`,
                    },
                ],
            };

        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to extract file content from download response. Metadata:\nFile: ${fileName}\nPath: ${filePath}\nSize: ${fileSize} bytes`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to download file: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\nMake sure:\n- The file path is correct\n- The file exists\n- You have access to the file`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\nYou may not have download access to this file`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: This path points to a folder, not a file.\n\nUse a file path, not a folder path`;
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
            const mimeType = `image/${validatedArgs.format}`;

            // Create image content using the helper function
            const imageContent = createImageContent(base64Thumbnail, mimeType);

            return {
                content: [imageContent],
            };
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to generate thumbnail for: ${validatedArgs.path}\nNo thumbnail data received from Dropbox.`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to get thumbnail for: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\nMake sure the file exists and the path is correct`;
        } else if (error.status === 415) {
            errorMessage += `\nError 415: Unsupported file type.\n\nThumbnails are only available for:\n- Images (JPEG, PNG, GIF, BMP, TIFF)\n- Videos (MP4, MOV, AVI, etc.)\n- Documents (PDF, DOC, DOCX, etc.)`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\nYou may not have access to this file`;
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

            // Detect content type using our helper function
            const { mimeType, contentType } = detectFileType(validatedArgs.path);
            const base64Preview = previewBuffer.toString('base64');

            // Return different content types based on the preview format
            if (contentType === 'image') {
                // For image files, return as image content
                const imageContent = createImageContent(base64Preview, mimeType);
                return {
                    content: [imageContent],
                };
            } else if (contentType === 'text') {
                // For text-based previews (HTML, CSV, etc.), try to decode as text
                try {
                    const textContent = previewBuffer.toString('utf8');
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Preview generated for: ${validatedArgs.path}\nContent-Type: ${mimeType}\nPreview size: ${previewBuffer.length} bytes\n\nPreview content:\n\n${textContent}`,
                            },
                        ],
                    };
                } catch (e) {
                    // Fallback to base64 if text decoding fails
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Preview generated for: ${validatedArgs.path}\nContent-Type: ${mimeType}\nPreview size: ${previewBuffer.length} bytes\n\nPreview content (base64):\n\n${base64Preview}`,
                            },
                        ],
                    };
                }
            } else {
                // For binary content like PDFs, check if the preview is actually an image
                // Dropbox often returns image previews for PDF and Office documents
                const isImagePreview = previewBuffer.length > 0 && (
                    previewBuffer.subarray(0, 4).toString('hex') === '89504e47' || // PNG
                    previewBuffer.subarray(0, 3).toString('hex') === 'ffd8ff' ||   // JPEG
                    previewBuffer.subarray(0, 6).toString() === 'GIF87a' ||         // GIF87a
                    previewBuffer.subarray(0, 6).toString() === 'GIF89a'            // GIF89a
                );

                if (isImagePreview) {
                    // Detect the actual image format from the preview data
                    let imageFormat = 'png';
                    if (previewBuffer.subarray(0, 3).toString('hex') === 'ffd8ff') {
                        imageFormat = 'jpeg';
                    } else if (previewBuffer.subarray(0, 6).toString().startsWith('GIF')) {
                        imageFormat = 'gif';
                    }

                    const imageContent = createImageContent(base64Preview, `image/${imageFormat}`);
                    return {
                        content: [imageContent],
                    };
                } else {
                    // For non-image binary previews, return as base64 text
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Preview generated for: ${validatedArgs.path}\nContent-Type: ${mimeType}\nPreview size: ${previewBuffer.length} bytes\n\nPreview content (base64):\n\n${base64Preview}`,
                            },
                        ],
                    };
                }
            }
        } else {
            return {
                content: [
                    {
                        type: "text",
                        text: `Failed to generate preview for: ${validatedArgs.path}\nNo preview data received from Dropbox.`,
                    },
                ],
            };
        }
    } catch (error: any) {
        let errorMessage = `Failed to get preview for: "${validatedArgs.path}"\n`;

        if (error.status === 404) {
            errorMessage += `\nError 404: File not found.\n\nMake sure the file exists and the path is correct`;
        } else if (error.status === 415) {
            errorMessage += `\nError 415: Unsupported file type.\n\nPreviews are only available for:\n- Documents (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX)\n- Text files\n- Images`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\nYou may not have access to this file`;
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
                        text: `URL saved successfully!\n\nFile: ${result.path_display || validatedArgs.path}\nSource URL: ${validatedArgs.url}\nSize: ${result.size || 'Unknown'} bytes`,
                    },
                ],
            };
        } else if (response.result['.tag'] === 'async_job_id') {
            return {
                content: [
                    {
                        type: "text",
                        text: `URL save started (async operation)\nJob ID: ${response.result.async_job_id}\n\nSource URL: ${validatedArgs.url}\nDestination: ${validatedArgs.path}\n\nUse 'save_url_check_job_status' with this Job ID to check progress.`,
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
            errorMessage += `\nError 400: Invalid URL or path.\n\nCheck:\n- URL is valid and accessible\n- Destination path is valid (starts with '/')\n- URL points to a downloadable file`;
        } else if (error.status === 403) {
            errorMessage += `\nError 403: Permission denied.\n\nYou may not have write access to the destination folder`;
        } else if (error.status === 409) {
            errorMessage += `\nError 409: File already exists at the destination path.\n\nTry:\n- Using a different filename\n- The URL content may have already been saved`;
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
                        text: `URL save operation is still in progress.\nJob ID: ${validatedArgs.async_job_id}\nStatus: Processing...`,
                    },
                ],
            };
        } else if (result['.tag'] === 'complete') {
            const completeResult = result as any;
            return {
                content: [
                    {
                        type: "text",
                        text: `URL save completed!\nJob ID: ${validatedArgs.async_job_id}\nFile: ${completeResult.path_display}\nSize: ${completeResult.size} bytes`,
                    },
                ],
            };
        } else if (result['.tag'] === 'failed') {
            const failedResult = result as any;
            return {
                content: [
                    {
                        type: "text",
                        text: `URL save failed.\nJob ID: ${validatedArgs.async_job_id}\nError: ${failedResult.reason || 'Unknown error'}`,
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
            errorMessage += `\nError 400: Invalid job ID.\n\nThe job ID may be malformed or expired`;
        } else if (error.status === 404) {
            errorMessage += `\nError 404: Job not found.\n\nThe job ID may be invalid or the job may have been cleaned up`;
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

export async function handleReadResource(uri: string) {
    if (!uri.startsWith('dropbox://')) {
        throw new Error('Invalid resource URI. Must start with dropbox://');
    }

    const filePath = uri.replace('dropbox://', '');
    
    try {
        const dropboxClient = getDropboxClient();
        const response = await dropboxClient.filesDownload({
            path: filePath.startsWith('/') ? filePath : `/${filePath}`,
        });

        const result = response.result as any;
        let fileBuffer: Buffer | undefined;

        // Extract file content
        if (result.fileBinary) {
            if (Buffer.isBuffer(result.fileBinary)) {
                fileBuffer = result.fileBinary;
            } else {
                fileBuffer = Buffer.from(result.fileBinary);
            }
        }

        if (fileBuffer) {
            const fileName = result.name || 'Unknown file';
            const { mimeType } = detectFileType(fileName);
            
            if (mimeType.startsWith('text/')) {
                // Return text content directly
                return {
                    contents: [
                        {
                            uri: uri,
                            mimeType: mimeType,
                            text: fileBuffer.toString('utf8'),
                        },
                    ],
                };
            } else {
                // Return binary content as base64
                return {
                    contents: [
                        {
                            uri: uri,
                            mimeType: mimeType,
                            blob: fileBuffer.toString('base64'),
                        },
                    ],
                };
            }
        }

        throw new Error('Failed to extract file content');
    } catch (error: any) {
        throw new Error(`Failed to read resource: ${error.message}`);
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
