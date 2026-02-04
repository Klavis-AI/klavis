import { z } from "zod";
import type { ToolArgs, ToolCategory } from "../tool.js";
import { ToolBase } from "../tool.js";
import type { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { ErrorCodes, MongoDBError } from "../../common/errors.js";
import { LogId } from "../../common/logger.js";
import type { Server } from "../../server.js";
import type { ConnectionMetadata } from "../../telemetry/types.js";

export const DbOperationArgs = {
    database: z.string().describe("Database name"),
    collection: z.string().describe("Collection name"),
};

export abstract class MongoDBToolBase extends ToolBase {
    protected server?: Server;
    static category: ToolCategory = "mongodb";

    protected async ensureConnected(): Promise<NodeDriverServiceProvider> {
        if (!this.session.isConnectedToMongoDB) {
            if (this.session.connectedAtlasCluster) {
                throw new MongoDBError(
                    ErrorCodes.NotConnectedToMongoDB,
                    `Attempting to connect to Atlas cluster "${this.session.connectedAtlasCluster.clusterName}", try again in a few seconds.`
                );
            }

            if (this.config.connectionString) {
                try {
                    await this.session.connectToConfiguredConnection();
                } catch (error) {
                    this.session.logger.error({
                        id: LogId.mongodbConnectFailure,
                        context: "mongodbTool",
                        message: `Failed to connect to MongoDB instance using the connection string from the config: ${error as string}`,
                    });
                    throw new MongoDBError(ErrorCodes.MisconfiguredConnectionString, "Not connected to MongoDB.");
                }
            }
        }

        if (!this.session.isConnectedToMongoDB) {
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
            switch (error.code) {
                case ErrorCodes.NotConnectedToMongoDB:
                case ErrorCodes.MisconfiguredConnectionString: {
                    const connectionError = error as MongoDBError<
                        ErrorCodes.NotConnectedToMongoDB | ErrorCodes.MisconfiguredConnectionString
                    >;
                    const outcome = this.server?.connectionErrorHandler(connectionError, {
                        availableTools: this.server?.tools ?? [],
                        connectionState: this.session.connectionManager.currentConnectionState,
                    });
                    if (outcome?.errorHandled) {
                        return outcome.result;
                    }

                    return super.handleError(error, args);
                }
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
                case ErrorCodes.AtlasSearchNotSupported: {
                    const CTA = this.server?.isToolCategoryAvailable("atlas-local" as unknown as ToolCategory)
                        ? "`atlas-local` tools"
                        : "Atlas CLI";
                    return {
                        content: [
                            {
                                text: `The connected MongoDB deployment does not support vector search indexes. Either connect to a MongoDB Atlas cluster or use the ${CTA} to create and manage a local Atlas deployment.`,
                                type: "text",
                            },
                        ],
                        isError: true,
                    };
                }
            }
        }

        return super.handleError(error, args);
    }

    /**
     * Resolves the tool metadata from the arguments passed to the mongoDB tools.
     *
     * Since MongoDB tools are executed against a MongoDB instance, the tool calls will always have the connection information.
     *
     * @param result - The result of the tool call.
     * @param args - The arguments passed to the tool
     * @returns The tool metadata
     */
    protected resolveTelemetryMetadata(
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        _args: ToolArgs<typeof this.argsShape>,
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        { result }: { result: CallToolResult }
    ): ConnectionMetadata {
        return this.getConnectionInfoMetadata();
    }
}
