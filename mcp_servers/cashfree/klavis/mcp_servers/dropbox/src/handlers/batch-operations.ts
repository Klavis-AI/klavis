import { CallToolRequest, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import * as schemas from "../schemas/index.js";
import { getDropboxClient } from "../utils/context.js";

export async function handleBatchDelete(args: any) {
    const validatedArgs = schemas.BatchDeleteSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleBatchMove(args: any) {
    const validatedArgs = schemas.BatchMoveSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleBatchCopy(args: any) {
    const validatedArgs = schemas.BatchCopySchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleCheckBatchJobStatus(args: any) {
    const validatedArgs = schemas.BatchJobStatusSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleLockFileBatch(args: any) {
    const validatedArgs = schemas.LockFileBatchSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

export async function handleUnlockFileBatch(args: any) {
    const validatedArgs = schemas.UnlockFileBatchSchema.parse(args);
    const dropbox = getDropboxClient();

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
}

/**
 * Main handler for batch operations
 */
export async function handleBatchOperation(request: CallToolRequest): Promise<CallToolResult> {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "dropbox_batch_delete":
            return await handleBatchDelete(args) as CallToolResult;
        case "dropbox_batch_move":
            return await handleBatchMove(args) as CallToolResult;
        case "dropbox_batch_copy":
            return await handleBatchCopy(args) as CallToolResult;
        case "dropbox_check_batch_job_status":
            return await handleCheckBatchJobStatus(args) as CallToolResult;
        case "dropbox_lock_file_batch":
            return await handleLockFileBatch(args) as CallToolResult;
        case "dropbox_unlock_file_batch":
            return await handleUnlockFileBatch(args) as CallToolResult;
        default:
            throw new Error(`Unknown batch operation: ${name}`);
    }
}
