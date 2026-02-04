import { z } from "zod";
import { ToolArgs, ToolBase, ToolCategory, TelemetryToolMetadata } from "../tool.js";
import { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { ErrorCodes, MongoDBError } from "../../common/errors.js";
import logger, { LogId } from "../../common/logger.js";
import { Server } from "../../server.js";

export const DbOperationArgs = {
    database: z.string().describe("Database name"),
    collection: z.string().describe("Collection name"),
};

export abstract class MongoDBToolBase extends ToolBase {
    private server?: Server;
    public category: ToolCategory = "mongodb";

    protected async ensureConnected(): Promise<NodeDriverServiceProvider> {
        if (!this.session.serviceProvider) {
            if (this.session.connectedAtlasCluster) {
                throw new MongoDBError(
                    ErrorCodes.NotConnectedToMongoDB,
                    `Attempting to connect to Atlas cluster "${this.session.connectedAtlasCluster.clusterName}", try again in a few seconds.`
                );
            }

            if (this.config.connectionString) {
                try {
                    await this.connectToMongoDB(this.config.connectionString);
                } catch (error) {
                    logger.error(
                        LogId.mongodbConnectFailure,
                        "mongodbTool",
                        `Failed to connect to MongoDB instance using the connection string from the config: ${error as string}`
                    );
                    throw new MongoDBError(ErrorCodes.MisconfiguredConnectionString, "Not connected to MongoDB.");
                }
            }
        }

        if (!this.session.serviceProvider) {
            throw new MongoDBError(ErrorCodes.NotConnectedToMongoDB, "Not connected to MongoDB");
        }

        return this.session.serviceProvider;
    }

    public register(server: Server): boolean {
        this.server = server;
        return super.register(server);
    }

    protected handleError(
        error: unknown,
        args: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> | CallToolResult {
        if (error instanceof MongoDBError) {
            const connectTools = this.server?.tools
                .filter((t) => t.operationType === "connect")
                .sort((a, b) => a.category.localeCompare(b.category)); // Sort Altas tools before MongoDB tools

            // Find the first Atlas connect tool if available and suggest to the LLM to use it.
            // Note: if we ever have multiple Atlas connect tools, we may want to refine this logic to select the most appropriate one.
            const atlasConnectTool = connectTools?.find((t) => t.category === "atlas");
            const llmConnectHint = atlasConnectTool
                ? `Note to LLM: prefer using the "${atlasConnectTool.name}" tool to connect to an Atlas cluster over using a connection string. Make sure to ask the user to specify a cluster name they want to connect to or ask them if they want to use the "list-clusters" tool to list all their clusters. Do not invent cluster names or connection strings unless the user has explicitly specified them. If they've previously connected to MongoDB using MCP, you can ask them if they want to reconnect using the same cluster/connection.`
                : "Note to LLM: do not invent connection strings and explicitly ask the user to provide one. If they have previously connected to MongoDB using MCP, you can ask them if they want to reconnect using the same connection string.";

            const connectToolsNames = connectTools?.map((t) => `"${t.name}"`).join(", ");
            switch (error.code) {
                case ErrorCodes.NotConnectedToMongoDB:
                    return {
                        content: [
                            {
                                type: "text",
                                text: "You need to connect to a MongoDB instance before you can access its data.",
                            },
                            {
                                type: "text",
                                text: connectToolsNames
                                    ? `Please use one of the following tools: ${connectToolsNames} to connect to a MongoDB instance or update the MCP server configuration to include a connection string. ${llmConnectHint}`
                                    : "There are no tools available to connect. Please update the configuration to include a connection string and restart the server.",
                            },
                        ],
                        isError: true,
                    };
                case ErrorCodes.MisconfiguredConnectionString:
                    return {
                        content: [
                            {
                                type: "text",
                                text: "The configured connection string is not valid. Please check the connection string and confirm it points to a valid MongoDB instance.",
                            },
                            {
                                type: "text",
                                text: connectTools
                                    ? `Alternatively, you can use one of the following tools: ${connectToolsNames} to connect to a MongoDB instance. ${llmConnectHint}`
                                    : "Please update the configuration to use a valid connection string and restart the server.",
                            },
                        ],
                        isError: true,
                    };
                case ErrorCodes.ForbiddenCollscan:
                    return {
                        content: [
                            {
                                type: "text",
                                text: error.message,
                            },
                        ],
                        isError: true,
                    };
            }
        }

        return super.handleError(error, args);
    }

    protected connectToMongoDB(connectionString: string): Promise<void> {
        return this.session.connectToMongoDB(connectionString, this.config.connectOptions);
    }

    protected resolveTelemetryMetadata(
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        args: ToolArgs<typeof this.argsShape>
    ): TelemetryToolMetadata {
        const metadata: TelemetryToolMetadata = {};

        // Add projectId to the metadata if running a MongoDB operation to an Atlas cluster
        if (this.session.connectedAtlasCluster?.projectId) {
            metadata.projectId = this.session.connectedAtlasCluster.projectId;
        }

        return metadata;
    }
}
