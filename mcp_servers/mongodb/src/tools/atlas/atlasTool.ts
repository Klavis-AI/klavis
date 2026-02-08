import { ToolBase, ToolCategory, TelemetryToolMetadata, ToolArgs } from "../tool.js";
import { ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import logger, { LogId } from "../../common/logger.js";
import { z } from "zod";
import { ApiClientError } from "../../common/atlas/apiClientError.js";

export abstract class AtlasToolBase extends ToolBase {
    public category: ToolCategory = "atlas";

    protected verifyAllowed(): boolean {
        if (!this.config.apiClientId || !this.config.apiClientSecret) {
            return false;
        }
        return super.verifyAllowed();
    }

    protected handleError(
        error: unknown,
        args: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> | CallToolResult {
        if (error instanceof ApiClientError) {
            const statusCode = error.response.status;

            if (statusCode === 401) {
                return {
                    content: [
                        {
                            type: "text",
                            text: `Unable to authenticate with MongoDB Atlas, API error: ${error.message}

Hint: Your API credentials may be invalid, expired or lack permissions.
Please check your Atlas API credentials and ensure they have the appropriate permissions.
For more information on setting up API keys, visit: https://www.mongodb.com/docs/atlas/configure-api-access/`,
                        },
                    ],
                    isError: true,
                };
            }

            if (statusCode === 403) {
                return {
                    content: [
                        {
                            type: "text",
                            text: `Received a Forbidden API Error: ${error.message}

You don't have sufficient permissions to perform this action in MongoDB Atlas
Please ensure your API key has the necessary roles assigned.
For more information on Atlas API access roles, visit: https://www.mongodb.com/docs/atlas/api/service-accounts-overview/`,
                        },
                    ],
                    isError: true,
                };
            }
        }

        // For other types of errors, use the default error handling from the base class
        return super.handleError(error, args);
    }

    /**
     *
     * Resolves the tool metadata from the arguments passed to the tool
     *
     * @param args - The arguments passed to the tool
     * @returns The tool metadata
     */
    protected resolveTelemetryMetadata(
        ...args: Parameters<ToolCallback<typeof this.argsShape>>
    ): TelemetryToolMetadata {
        const toolMetadata: TelemetryToolMetadata = {};
        if (!args.length) {
            return toolMetadata;
        }

        // Create a typed parser for the exact shape we expect
        const argsShape = z.object(this.argsShape);
        const parsedResult = argsShape.safeParse(args[0]);

        if (!parsedResult.success) {
            logger.debug(
                LogId.telemetryMetadataError,
                "tool",
                `Error parsing tool arguments: ${parsedResult.error.message}`
            );
            return toolMetadata;
        }

        const data = parsedResult.data;

        // Extract projectId using type guard
        if ("projectId" in data && typeof data.projectId === "string" && data.projectId.trim() !== "") {
            toolMetadata.projectId = data.projectId;
        }

        // Extract orgId using type guard
        if ("orgId" in data && typeof data.orgId === "string" && data.orgId.trim() !== "") {
            toolMetadata.orgId = data.orgId;
        }
        return toolMetadata;
    }
}
