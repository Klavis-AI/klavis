import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handler for account and utility operations
 */
export async function handleAccountOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;
    const dropbox = getDropboxClient();

    switch (name) {
        case "get_current_account": {
            schemas.GetCurrentAccountSchema.parse(args);
            const response = await dropbox.usersGetCurrentAccount();
            const account = response.result;

            return {
                content: [
                    {
                        type: "text",
                        text: `Account: ${(account as any).name?.display_name || 'Unknown'}\nEmail: ${(account as any).email || 'Unknown'}\nAccount ID: ${(account as any).account_id || 'Unknown'}`,
                    },
                ],
            };
        }

        case "get_space_usage": {
            schemas.GetSpaceUsageSchema.parse(args);
            const response = await dropbox.usersGetSpaceUsage();
            const spaceInfo = response.result as any;
            let info = `Used: ${spaceInfo.used} bytes`;
            if (spaceInfo.allocation) {
                if (spaceInfo.allocation['.tag'] === 'individual') {
                    info += `\nAllocated: ${spaceInfo.allocation.allocated} bytes`;
                } else {
                    info += `\nAllocation Type: ${spaceInfo.allocation['.tag']}`;
                }
            }

            return {
                content: [
                    {
                        type: "text",
                        text: info,
                    },
                ],
            };
        }

        case "get_temporary_link": {
            const validatedArgs = schemas.GetTemporaryLinkSchema.parse(args);
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

        case "get_preview": {
            const validatedArgs = schemas.GetPreviewSchema.parse(args);

            try {
                const response = await dropbox.filesGetPreview({
                    path: validatedArgs.path,
                });

                // Convert preview buffer to base64 for safe transmission
                const previewBuffer = (response.result as any).fileBinary as Buffer;
                const base64Preview = previewBuffer ? previewBuffer.toString('base64') : 'No preview available';

                return {
                    content: [
                        {
                            type: "text",
                            text: `Preview (base64): ${base64Preview}`,
                        },
                    ],
                };
            } catch (error: any) {
                let errorMessage = `Failed to get preview for: "${validatedArgs.path}"\n`;

                // Add detailed API error information
                errorMessage += `\n🔍 Detailed Error Information:\n`;
                errorMessage += `• HTTP Status: ${error.status || 'Unknown'}\n`;
                errorMessage += `• Error Summary: ${error.error_summary || 'Not provided'}\n`;
                errorMessage += `• Error Message: ${error.message || 'Not provided'}\n`;

                if (error.error) {
                    errorMessage += `• API Error Details: ${JSON.stringify(error.error, null, 2)}\n`;
                }

                // Check for specific Dropbox API errors
                if (error.error_summary && error.error_summary.includes('unsupported_extension')) {
                    errorMessage += `\n❌ Unsupported file extension - This file type doesn't support preview generation.\n\n📋 Supported file types:\n\n📄 PDF Preview:\n• .ai, .doc, .docm, .docx, .eps, .gdoc, .gslides\n• .odp, .odt, .pps, .ppsm, .ppsx, .ppt, .pptm, .pptx, .rtf\n\n🌐 HTML Preview:\n• .csv, .ods, .xls, .xlsm, .gsheet, .xlsx\n\n💡 Try:\n• Converting your file to a supported format\n• Using 'download_file' to get the file content instead\n• Using 'get_thumbnail' for image files`;
                } else if (error.error_summary && error.error_summary.includes('unsupported_content')) {
                    errorMessage += `\n❌ Unsupported file content - The file content is not supported for preview generation.\n\n💡 This could mean:\n• File is corrupted or empty\n• File format is not recognized\n• File content doesn't match the extension\n\n💡 Try:\n• Checking if the file can be opened normally\n• Re-saving the file in the original application\n• Using 'download_file' to get the raw file content`;
                } else if (error.error_summary && error.error_summary.includes('in_progress')) {
                    errorMessage += `\n⏳ Preview generation in progress - The preview is still being generated.\n\n💡 This is normal for:\n• Large files\n• Newly uploaded files\n• Complex documents\n\n💡 Try:\n• Waiting a few moments and trying again\n• The preview will be ready shortly`;
                } else if (error.status === 409) {
                    errorMessage += `\n❌ Error 409: Conflict - Preview generation failed due to a conflict.\n\n💡 Common causes:\n• File is currently being modified\n• File is locked or in use\n• Temporary server conflict\n\n💡 Try:\n• Waiting a moment and trying again\n• Using get_file_info to check file status`;
                } else if (error.status === 404) {
                    errorMessage += `\n❌ Error 404: File not found - The path "${validatedArgs.path}" doesn't exist.\n\n💡 Make sure:\n• The file path is correct and starts with '/'\n• The file exists in your Dropbox\n• You have access to the file`;
                } else if (error.status === 403) {
                    errorMessage += `\n❌ Error 403: Permission denied - You don't have permission to preview this file.\n\n💡 This could mean:\n• The file is in a shared space you don't have access to\n• Your access token may have insufficient scope (needs 'files.content.read')`;
                } else if (error.status === 400) {
                    errorMessage += `\n❌ Error 400: Invalid request - Check the file path format.\n\n💡 Requirements:\n• Path must start with '/' (e.g., '/Documents/file.pdf')\n• File must exist and be accessible\n• File extension must be supported for preview`;
                } else if (error.status === 401) {
                    errorMessage += `\n❌ Error 401: Unauthorized - Your access token may be invalid or expired.\n\n💡 Check:\n• Access token is valid and not expired\n• Token has 'files.content.read' permission\n• You're authenticated with the correct Dropbox account`;
                } else if (error.status === 429) {
                    errorMessage += `\n❌ Error 429: Too many requests - You're hitting rate limits.\n\n💡 Tips:\n• Wait a moment before trying again\n• Reduce the frequency of preview requests\n• Consider generating previews in smaller batches`;
                } else {
                    errorMessage += `\n❌ Error ${error.status || 'Unknown'}: ${error.message || error.error_summary || 'Unknown error'}`;
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

        case "save_url": {
            const validatedArgs = schemas.SaveUrlSchema.parse(args);

            try {
                const response = await dropbox.filesSaveUrl({
                    path: validatedArgs.path,
                    url: validatedArgs.url,
                });

                if (response.result['.tag'] === 'complete') {
                    const metadata = (response.result as any).metadata;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `✅ URL content saved successfully!\n\n📄 File: ${metadata.name}\n📁 Path: ${metadata.path_display}\n📏 Size: ${metadata.size} bytes\n🕒 Modified: ${metadata.client_modified}\n\n🌐 Source URL: ${validatedArgs.url}`,
                            },
                        ],
                    };
                } else if (response.result['.tag'] === 'async_job_id') {
                    const jobId = (response.result as any).async_job_id;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `🔄 URL download started (large file detected)\n\n📄 Target: ${validatedArgs.path}\n🌐 Source: ${validatedArgs.url}\n🆔 Job ID: ${jobId}\n\n💡 Use 'save_url_check_job_status' with this job ID to monitor progress.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `⚠️ Unexpected response from save URL operation\n\nTarget: ${validatedArgs.path}\nSource: ${validatedArgs.url}\nResponse: ${JSON.stringify(response.result, null, 2)}`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to save URL content to: "${validatedArgs.path}"\nSource URL: ${validatedArgs.url}\n`;

                if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check the URL and file path.\n\n💡 Common issues:\n• Invalid URL format\n• URL is not accessible\n• File path format is incorrect (should start with '/')\n• File name contains invalid characters`;
                } else if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied\n\n💡 This could mean:\n• You don't have permission to write to this folder\n• Your access token needs 'files.content.write' scope\n• The URL content is blocked by content policy`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - File already exists at this path.\n\n💡 Try:\n• Using a different file name\n• Enabling autorename in your upload settings\n• Deleting the existing file first`;
                } else if (error.status === 507) {
                    errorMessage += `\nError 507: Insufficient storage - Your Dropbox is full.\n\n💡 To fix this:\n• Delete some files to free up space\n• Upgrade your Dropbox plan for more storage`;
                } else if (error.status === 415) {
                    errorMessage += `\nError 415: Unsupported media type - The URL content type is not supported.\n\n💡 Dropbox may not support:\n• Certain file types\n• Very large files\n• Streaming content`;
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

        case "save_url_check_job_status": {
            const validatedArgs = schemas.SaveUrlCheckJobStatusSchema.parse(args);

            try {
                const response = await dropbox.filesSaveUrlCheckJobStatus({
                    async_job_id: validatedArgs.async_job_id,
                });

                if (response.result['.tag'] === 'complete') {
                    const metadata = (response.result as any).metadata;
                    const fileName = metadata?.name || 'Unknown file';
                    const filePath = metadata?.path_display || 'Unknown path';
                    const fileSize = metadata?.size || 'Unknown size';
                    const modified = metadata?.client_modified || metadata?.server_modified || 'Unknown date';

                    return {
                        content: [
                            {
                                type: "text",
                                text: `✅ URL download completed successfully!\n\n📄 File: ${fileName}\n📁 Path: ${filePath}\n📏 Size: ${fileSize} bytes\n🕒 Modified: ${modified}\n\n🆔 Job ID: ${validatedArgs.async_job_id}`,
                            },
                        ],
                    };
                } else if (response.result['.tag'] === 'in_progress') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `🔄 URL download is still in progress...\n\n🆔 Job ID: ${validatedArgs.async_job_id}\n\n💡 Please wait and check again in a few moments.`,
                            },
                        ],
                    };
                } else if (response.result['.tag'] === 'failed') {
                    const failureReason = (response.result as any).reason || 'Unknown error';
                    return {
                        content: [
                            {
                                type: "text",
                                text: `❌ URL download failed\n\n🆔 Job ID: ${validatedArgs.async_job_id}\n🚫 Reason: ${failureReason}\n\n💡 Common failure reasons:\n• URL became inaccessible\n• Network timeout\n• File size too large\n• Content type not supported`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `⚠️ Unknown job status: ${response.result['.tag']}\n\n🆔 Job ID: ${validatedArgs.async_job_id}`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to check save URL job status\nJob ID: ${validatedArgs.async_job_id}\n`;

                if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid job ID - The job ID may be malformed or expired.`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: Job not found - The job ID may be invalid or the job may have been cleaned up.`;
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

        default:
            throw new Error(`Unknown account operation: ${name}`);
    }
}
