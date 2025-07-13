import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

/**
 * Handler for batch operations and file locking
 */
export async function handleBatchOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;
    const dropbox = getDropboxClient();

    switch (name) {
        case "batch_delete": {
            const validatedArgs = schemas.BatchDeleteSchema.parse(args);

            try {
                const response = await dropbox.filesDeleteBatch({
                    entries: validatedArgs.entries,
                });

                const result = response.result as any;

                // Handle both sync and async responses
                if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                    let resultMessage = `Batch delete completed:\n`;
                    resultMessage += `Successful: ${successful}\n`;
                    resultMessage += `Failed: ${failed}`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any) => `  - ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'async_job_id') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch delete started (async operation)\nJob ID: ${result.async_job_id}\n\nThe operation is processing in the background.\nUse 'check_batch_job_status' with this Job ID to monitor progress and get final results.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch delete initiated. Processing ${validatedArgs.entries.length} entries.`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to perform batch delete on ${validatedArgs.entries.length} items\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You may not have permission to delete some of these files/folders.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Check that all paths are valid and properly formatted.`;
                } else if (error.status === 429) {
                    errorMessage += `\nError 429: Too many requests - You're hitting rate limits. Try with fewer files or wait a moment.`;
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

        case "batch_move": {
            const validatedArgs = schemas.BatchMoveSchema.parse(args);

            try {
                const response = await dropbox.filesMoveBatchV2({
                    entries: validatedArgs.entries,
                    autorename: validatedArgs.autorename,
                    allow_ownership_transfer: validatedArgs.allow_ownership_transfer,
                });

                const result = response.result as any;

                // Handle both sync and async responses
                if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                    let resultMessage = `Batch move completed:\n`;
                    resultMessage += `Successful: ${successful}\n`;
                    resultMessage += `Failed: ${failed}`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any) => `  - ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'async_job_id') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch move started (async operation)\nJob ID: ${result.async_job_id}\nThe operation is processing in the background. Use the job ID to check status.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch move initiated. Processing ${validatedArgs.entries.length} entries.`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to perform batch move on ${validatedArgs.entries.length} items\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You may not have permission to move some of these files/folders.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Check that all source and destination paths are valid.`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Some destination paths may already exist or there are path conflicts.`;
                } else if (error.status === 429) {
                    errorMessage += `\nError 429: Too many requests - You're hitting rate limits. Try with fewer files or wait a moment.`;
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

        case "batch_copy": {
            const validatedArgs = schemas.BatchCopySchema.parse(args);

            try {
                const response = await dropbox.filesCopyBatchV2({
                    entries: validatedArgs.entries,
                });

                const result = response.result as any;

                // Handle both sync and async responses
                if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                    let resultMessage = `Batch copy completed:\n`;
                    resultMessage += `Successful: ${successful}\n`;
                    resultMessage += `Failed: ${failed}`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any) => `  - ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'async_job_id') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch copy started (async operation)\nJob ID: ${result.async_job_id}\n\nThe operation is processing in the background.\nNext Steps:\n1. Use 'check_batch_job_status' tool with this Job ID\n2. Monitor progress until completion\n3. The tool will show final results (successful / failed counts)\n\nTip: Large batches or many files typically trigger async processing.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch copy initiated. Processing ${validatedArgs.entries.length} entries.`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to perform batch copy on ${validatedArgs.entries.length} items\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You may not have permission to copy some of these files/folders.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Bad request - Check that all source and destination paths are valid.\n\nBatch Copy Parameter Guide:\n- Use simple entries: [{"from_path": "/source", "to_path": "/dest"}]\n- Set top-level 'autorename: true' to auto-rename conflicts\n- Don't include per-entry options like 'allow_shared_folder'\n- Ensure all paths start with '/' and files/folders exist`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Some destination paths may already exist or there are path conflicts.\n\nTips:\n- Set top-level 'autorename: true' to automatically rename conflicting files\n- Check for duplicate destination paths in your batch\n- Verify destination folders exist`;
                } else if (error.status === 429) {
                    errorMessage += `\nError 429: Too many requests - You're hitting rate limits.\n\nTips:\n- Try with fewer files (batches of 100-500)\n- Wait a few seconds between requests\n- Consider using smaller batch sizes\n- Batch operations are more efficient than individual calls`;
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

        case "check_batch_job_status": {
            const validatedArgs = schemas.BatchJobStatusSchema.parse(args);

            try {
                // Try checking different types of batch operations
                let statusResponse;
                let operationType = "operation";

                // First try copy batch check
                try {
                    statusResponse = await dropbox.filesCopyBatchCheckV2({
                        async_job_id: validatedArgs.async_job_id,
                    });
                    operationType = "copy";
                } catch (copyError: any) {
                    // If copy check fails, try move batch check
                    try {
                        statusResponse = await dropbox.filesMoveBatchCheckV2({
                            async_job_id: validatedArgs.async_job_id,
                        });
                        operationType = "move";
                    } catch (moveError: any) {
                        // If move check fails, try delete batch check
                        try {
                            statusResponse = await dropbox.filesDeleteBatchCheck({
                                async_job_id: validatedArgs.async_job_id,
                            });
                            operationType = "delete";
                        } catch (deleteError: any) {
                            throw new Error(`Unable to check job status. Job ID may be invalid or expired: ${validatedArgs.async_job_id}`);
                        }
                    }
                }

                const result = statusResponse.result as any;

                if (result['.tag'] === 'in_progress') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch ${operationType} operation is still in progress.\nJob ID: ${validatedArgs.async_job_id}\nStatus: Processing...`,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.filter((entry: any) => entry['.tag'] === 'failure').length;

                    let resultMessage = `Batch ${operationType} operation completed!\n`;
                    resultMessage += `Job ID: ${validatedArgs.async_job_id}\n`;
                    resultMessage += `Successful: ${successful}\n`;
                    resultMessage += `Failed: ${failed}`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'failed') {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch ${operationType} operation failed.\nJob ID: ${validatedArgs.async_job_id}\nError: ${result.reason || 'Unknown error'}`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Batch ${operationType} operation status: ${result['.tag'] || 'Unknown'}\nJob ID: ${validatedArgs.async_job_id}`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to check batch job status for ID: ${validatedArgs.async_job_id}\n`;

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

        case "lock_file_batch": {
            const validatedArgs = schemas.LockFileBatchSchema.parse(args);

            try {
                const response = await dropbox.filesLockFileBatch({
                    entries: validatedArgs.entries,
                });

                const result = response.result as any;

                // Check if response has entries directly (sync response)
                if (result.entries) {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.length - successful;

                    let resultMessage = `File locking batch operation completed!\n\n`;
                    resultMessage += `Successfully locked: ${successful} file(s)\n`;
                    resultMessage += `Failed to lock: ${failed} file(s)`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                }
                // Check if response is immediate or async (with .tag)
                else if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.length - successful;

                    let resultMessage = `File locking batch operation completed!\n\n`;
                    resultMessage += `Successfully locked: ${successful} file(s)\n`;
                    resultMessage += `Failed to lock: ${failed} file(s)`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'async_job_id') {
                    const jobId = result.async_job_id;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `File locking batch operation started (large batch detected)\n\nJob ID: ${jobId}\n\nUse 'check_batch_job_status' with this job ID to monitor progress.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Unknown response from file locking operation: ${result['.tag'] || 'undefined'}\nFull response: ${JSON.stringify(result, null, 2)}`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to lock files\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to lock these files.\n\nFile locking may require:\n- Edit permissions on the files\n- Files to be in shared folders you manage\n- Dropbox Business account features`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: One or more files not found - Check that all file paths exist.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check file paths and batch size (max 1000 files).`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Some files may already be locked or in use.`;
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

        case "unlock_file_batch": {
            const validatedArgs = schemas.UnlockFileBatchSchema.parse(args);

            try {
                const response = await dropbox.filesUnlockFileBatch({
                    entries: validatedArgs.entries,
                });

                const result = response.result as any;

                // Check if response has entries directly (sync response)
                if (result.entries) {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.length - successful;

                    let resultMessage = `File unlocking batch operation completed!\n\n`;
                    resultMessage += `Successfully unlocked: ${successful} file(s)\n`;
                    resultMessage += `Failed to unlock: ${failed} file(s)`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                }
                // Check if response is immediate or async (with .tag)
                else if (result['.tag'] === 'complete') {
                    const entries = result.entries || [];
                    const successful = entries.filter((entry: any) => entry['.tag'] === 'success').length;
                    const failed = entries.length - successful;

                    let resultMessage = `File unlocking batch operation completed!\n\n`;
                    resultMessage += `Successfully unlocked: ${successful} file(s)\n`;
                    resultMessage += `Failed to unlock: ${failed} file(s)`;

                    if (failed > 0) {
                        const failureDetails = entries
                            .filter((entry: any) => entry['.tag'] === 'failure')
                            .map((entry: any, index: number) => `  ${index + 1}. ${entry.failure?.reason || 'Unknown error'}`)
                            .join('\n');
                        resultMessage += `\n\nFailure details:\n${failureDetails}`;
                    }

                    return {
                        content: [
                            {
                                type: "text",
                                text: resultMessage,
                            },
                        ],
                    };
                } else if (result['.tag'] === 'async_job_id') {
                    const jobId = result.async_job_id;
                    return {
                        content: [
                            {
                                type: "text",
                                text: `File unlocking batch operation started (large batch detected)\n\nJob ID: ${jobId}\n\nUse 'check_batch_job_status' with this job ID to monitor progress.`,
                            },
                        ],
                    };
                } else {
                    return {
                        content: [
                            {
                                type: "text",
                                text: `Unknown response from file unlocking operation: ${result['.tag'] || 'undefined'}\nFull response: ${JSON.stringify(result, null, 2)}`,
                            },
                        ],
                    };
                }
            } catch (error: any) {
                let errorMessage = `Failed to unlock files\n`;

                if (error.status === 403) {
                    errorMessage += `\nError 403: Permission denied - You don't have permission to unlock these files.\n\nYou can only unlock:\n- Files you previously locked\n- Files in shared folders you manage\n- Files you have edit permissions for`;
                } else if (error.status === 404) {
                    errorMessage += `\nError 404: One or more files not found - Check that all file paths exist.`;
                } else if (error.status === 400) {
                    errorMessage += `\nError 400: Invalid request - Check file paths and batch size (max 1000 files).`;
                } else if (error.status === 409) {
                    errorMessage += `\nError 409: Conflict - Some files may not be locked or may be locked by others.`;
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
            throw new Error(`Unknown batch operation: ${name}`);
    }
}
