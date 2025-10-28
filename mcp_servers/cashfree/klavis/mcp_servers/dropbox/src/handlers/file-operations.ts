import { getDropboxClient } from '../utils/context.js';
import {
    UploadFileSchema,
    DownloadFileSchema,
    GetThumbnailSchema,
    GetTemporaryLinkSchema,
    ListRevisionsSchema,
    RestoreFileSchema,
    SaveUrlSchema,
    SaveUrlCheckJobStatusSchema
} from '../schemas/index.js';
import { CallToolRequest, CallToolResult, ImageContent, AudioContent } from "@modelcontextprotocol/sdk/types.js";
import type { ReadResourceResult } from "@modelcontextprotocol/sdk/types.js";
import { getUri } from 'get-uri';
import { lookup } from 'mime-types';
import {
    dropboxResourceUriToPath,
    isFolderPath
} from '../utils/path-url-handling.js';
import { DropboxMCPError, ErrorModules, ErrorTypes } from '../error.js';
import { wrapGetUriError } from '../utils/error-msg.js';

/**
 * Creates an ImageContent object for MCP responses
 */
function createImageContent(data: Buffer, mimeType: string): ImageContent {
    return {
        type: "image" as const,
        data: data.toString('base64'),
        mimeType: mimeType,
    };
}

/**
 * Create an AudioContent object for MCP responses
 */
function createAudioContent(data: Buffer, mimeType: string): AudioContent {
    return {
        type: "audio" as const,
        data: data.toString('base64'),
        mimeType: mimeType,
    };
}

/**
 * Detects file type and MIME type based on file extension using mime-types library
 */
export function detectFileType(fileName: string): { mimeType: string; contentType: 'image' | 'audio' | 'text' | 'binary' } {
    // Use mime-types library to get MIME type from filename
    const mimeType = lookup(fileName) || 'application/octet-stream';

    // Determine content type category based on MIME type
    if (mimeType.startsWith('image/')) {
        return { mimeType, contentType: 'image' };
    }

    if (mimeType.startsWith('audio/')) {
        return { mimeType, contentType: 'audio' };
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

    let source = validatedArgs.source_uri;
    // No allow file:// URIs for security reasons
    if (source.startsWith('file://')) {
        throw new DropboxMCPError(ErrorTypes.OTHERS_ERROR, ErrorModules.OTHERS,
            "File URIs are not allowed for security reasons. Please use http://, https://, ftp://, or data: URIs."
        );
    }
    const targetPath = validatedArgs.dropbox_path;

    // Get stream from URI using get-uri (supports http://, https://, ftp://, data:.)
    let stream: NodeJS.ReadableStream;

    try {
        stream = await getUri(source);
    } catch (error) {
        wrapGetUriError(error, source);
    }

    // Use chunked upload for all files to avoid Node.js fetch duplex issues
    // and handle both small and large files consistently
    return await handleChunkedUpload(dropbox, stream, targetPath, validatedArgs, source);
}

/**
 * Handle large file uploads using Dropbox's chunked upload session
 */
async function handleChunkedUpload(
    dropbox: any,
    stream: NodeJS.ReadableStream,
    targetPath: string,
    validatedArgs: any,
    source: string
) {
    const CHUNK_SIZE = 4 * 1024 * 1024; // 4MB chunks
    let sessionId: string | undefined;
    let uploadedBytes = 0;
    let buffer = Buffer.alloc(0);

    try {
        // Start upload session
        const startResponse = await dropbox.filesUploadSessionStart({
            close: false,
            contents: Buffer.alloc(0),
        });
        sessionId = startResponse.result.session_id;

        // Process stream in chunks
        for await (const chunk of stream) {
            buffer = Buffer.concat([buffer, Buffer.from(chunk)]);

            // If we have enough data for a chunk, upload it
            while (buffer.length >= CHUNK_SIZE) {
                const chunkToUpload = buffer.slice(0, CHUNK_SIZE);
                buffer = buffer.slice(CHUNK_SIZE);

                await dropbox.filesUploadSessionAppendV2({
                    cursor: {
                        session_id: sessionId,
                        offset: uploadedBytes,
                    },
                    close: false,
                    contents: chunkToUpload,
                });

                uploadedBytes += chunkToUpload.length;
            }
        }

        // Upload any remaining data and finish the session
        const finishResponse = await dropbox.filesUploadSessionFinish({
            cursor: {
                session_id: sessionId,
                offset: uploadedBytes,
            },
            commit: {
                path: targetPath,
                mode: validatedArgs.mode as any,
                autorename: validatedArgs.autorename,
                mute: validatedArgs.mute,
            },
            contents: buffer, // Upload remaining data
        });

        const totalSize = uploadedBytes + buffer.length;

        return {
            content: [
                {
                    type: "text",
                    text: `File uploaded successfully (chunked upload)!\n\nSource URI: ${source}\nDropbox path: ${finishResponse.result.path_display}\nFile size: ${finishResponse.result.size} bytes (${(finishResponse.result.size / 1024 / 1024).toFixed(2)} MB)\nUploaded size: ${totalSize} bytes (${(totalSize / 1024 / 1024).toFixed(2)} MB)\nUpload mode: ${validatedArgs.mode}\nAutorename: ${validatedArgs.autorename}`,
                },
            ],
        };
    } catch (error) {
        // If we started a session but failed, we should consider cleaning up
        // but Dropbox sessions auto-expire, so it's not critical
        throw error;
    }
}

export async function handleDownloadFile(args: any) {
    const validatedArgs = DownloadFileSchema.parse(args);
    const dropbox = getDropboxClient();
    const path = validatedArgs.path;
    if (!isFolderPath(path)) {
        const { mimeType, contentType } = detectFileType(path);
        if (['image', 'audio', 'text'].includes(contentType)) {
            const response = await dropbox.filesDownload({
                path: path,
            });
            const result = response.result as any;
            const fileBuffer = Buffer.from(result.fileBinary, 'binary');
            let content;
            switch (contentType) {
                case 'image':
                    content = createImageContent(fileBuffer, mimeType);
                    break;
                case 'audio':
                    content = createAudioContent(fileBuffer, mimeType);
                    break;
                case 'text':
                    content = {
                        type: "text",
                        text: fileBuffer.toString('utf8'),
                    }
            }
            return {
                content: [content],
            };
        }
    }
    return {
        content: [
            {
                type: "text",
                text: `Use resources/read to access the fileContent at URI: dropbox://${path}`,
            },
        ],

    };
}

export async function handleGetThumbnail(args: any) {
    const validatedArgs = GetThumbnailSchema.parse(args);
    const dropbox = getDropboxClient();

    const response = await dropbox.filesGetThumbnailV2({
        resource: { ".tag": "path", path: validatedArgs.path },
        format: { ".tag": validatedArgs.format },
        size: { ".tag": validatedArgs.size },
    });

    const result = response.result as any;

    const thumbnailBuffer = Buffer.isBuffer(result.fileBinary)
        ? result.fileBinary
        : Buffer.from(result.fileBinary, 'binary');

    const base64Thumbnail = thumbnailBuffer.toString('base64');
    const mimeType = `image/${validatedArgs.format}`;

    // Create image content using the helper function
    const imageContent = createImageContent(base64Thumbnail, mimeType);

    return {
        content: [imageContent],
    };
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
}

export async function handleSaveUrlCheckJobStatus(args: any) {
    const validatedArgs = SaveUrlCheckJobStatusSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleReadResource(uri: string): Promise<ReadResourceResult> {
    if (!uri.startsWith('dropbox://')) {
        throw new Error('Invalid resource URI. Must start with dropbox://');
    }

    const filePath = dropboxResourceUriToPath(uri);

    try {
        const dropboxClient = getDropboxClient();
        const response = await dropboxClient.filesDownload({
            path: filePath,
        });

        const result = response.result as any;
        let fileBuffer: Buffer | undefined;

        // Extract file content
        if (result.fileBinary) {
            if (Buffer.isBuffer(result.fileBinary)) {
                fileBuffer = result.fileBinary;
            } else {
                // According to official examples, fileBinary should be treated as binary data
                fileBuffer = Buffer.from(result.fileBinary, 'binary');
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
        case "dropbox_upload_file":
            return await handleUploadFile(args) as CallToolResult;
        case "dropbox_download_file":
            return await handleDownloadFile(args) as CallToolResult;
        case "dropbox_get_thumbnail":
            return await handleGetThumbnail(args) as CallToolResult;
        case "dropbox_list_revisions":
            return await handleListRevisions(args) as CallToolResult;
        case "dropbox_restore_file":
            return await handleRestoreFile(args) as CallToolResult;
        case "dropbox_save_url":
            return await handleSaveUrl(args) as CallToolResult;
        case "dropbox_save_url_check_job_status":
            return await handleSaveUrlCheckJobStatus(args) as CallToolResult;
        case "dropbox_get_temporary_link":
            return await handleGetTemporaryLink(args) as CallToolResult;
        default:
            throw new Error(`Unknown file operation: ${name}`);
    }
}
