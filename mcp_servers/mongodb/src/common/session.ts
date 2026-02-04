import { ObjectId } from "bson";
import type { ApiClient } from "./atlas/apiClient.js";
import { createAtlasApiClient } from "./atlas/apiClient.js";
import type { Implementation } from "@modelcontextprotocol/sdk/types.js";
import type { CompositeLogger } from "./logger.js";
import { LogId } from "./logger.js";
import EventEmitter from "events";
import type {
    AtlasClusterConnectionInfo,
    ConnectionManager,
    ConnectionSettings,
    ConnectionStateConnected,
    ConnectionStateErrored,
} from "./connectionManager.js";
import type { ConnectionStringInfo } from "./connectionInfo.js";
import type { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import { ErrorCodes, MongoDBError } from "./errors.js";
import type { ExportsManager } from "./exportsManager.js";
import type { Client } from "@mongodb-js/atlas-local";
import type { Keychain } from "./keychain.js";
import type { VectorSearchEmbeddingsManager } from "./search/vectorSearchEmbeddingsManager.js";
import { generateConnectionInfoFromCliArgs } from "@mongosh/arg-parser";
import { type UserConfig } from "../common/config/userConfig.js";

export interface SessionOptions {
    userConfig: UserConfig;
    logger: CompositeLogger;
    exportsManager: ExportsManager;
    connectionManager: ConnectionManager;
    keychain: Keychain;
    atlasLocalClient?: Client;
    vectorSearchEmbeddingsManager: VectorSearchEmbeddingsManager;
    apiClient?: ApiClient;
}

export type SessionEvents = {
    connect: [];
    close: [];
    disconnect: [];
    "connection-error": [ConnectionStateErrored];
};

export class Session extends EventEmitter<SessionEvents> {
    private readonly userConfig: UserConfig;
    readonly sessionId: string = new ObjectId().toString();
    readonly exportsManager: ExportsManager;
    readonly connectionManager: ConnectionManager;
    readonly apiClient?: ApiClient;
    readonly atlasLocalClient?: Client;
    readonly keychain: Keychain;
    readonly vectorSearchEmbeddingsManager: VectorSearchEmbeddingsManager;

    mcpClient?: {
        name?: string;
        version?: string;
        title?: string;
    };

    public logger: CompositeLogger;

    constructor({
        userConfig,
        logger,
        connectionManager,
        exportsManager,
        keychain,
        atlasLocalClient,
        vectorSearchEmbeddingsManager,
        apiClient,
    }: SessionOptions) {
        super();

        this.userConfig = userConfig;
        this.keychain = keychain;
        this.logger = logger;
        this.apiClient = apiClient;

        // Create default API client if not provided in the constructor and Atlas tools are enabled (credentials are provided)
        if (!this.apiClient && userConfig.apiClientId && userConfig.apiClientSecret) {
            this.apiClient = createAtlasApiClient(
                {
                    baseUrl: userConfig.apiBaseUrl,
                    credentials: {
                        clientId: userConfig.apiClientId,
                        clientSecret: userConfig.apiClientSecret,
                    },
                },
                logger
            );
        }

        this.atlasLocalClient = atlasLocalClient;
        this.exportsManager = exportsManager;
        this.connectionManager = connectionManager;
        this.vectorSearchEmbeddingsManager = vectorSearchEmbeddingsManager;
        this.connectionManager.events.on("connection-success", () => this.emit("connect"));
        this.connectionManager.events.on("connection-time-out", (error) => this.emit("connection-error", error));
        this.connectionManager.events.on("connection-close", () => this.emit("disconnect"));
        this.connectionManager.events.on("connection-error", (error) => this.emit("connection-error", error));
    }

    setMcpClient(mcpClient: Implementation | undefined): void {
        if (!mcpClient) {
            this.connectionManager.setClientName("unknown");
            this.logger.debug({
                id: LogId.serverMcpClientSet,
                context: "session",
                message: "MCP client info not found",
            });
        }

        this.mcpClient = {
            name: mcpClient?.name || "unknown",
            version: mcpClient?.version || "unknown",
            title: mcpClient?.title || "unknown",
        };

        // Set the client name on the connection manager for appName generation
        this.connectionManager.setClientName(this.mcpClient.name || "unknown");
    }

    async disconnect(): Promise<void> {
        const atlasCluster = this.connectedAtlasCluster;

        await this.connectionManager.close();

        if (atlasCluster?.username && atlasCluster?.projectId && this.apiClient) {
            void this.apiClient
                .deleteDatabaseUser({
                    params: {
                        path: {
                            groupId: atlasCluster.projectId,
                            username: atlasCluster.username,
                            databaseName: "admin",
                        },
                    },
                })
                .catch((err: unknown) => {
                    const error = err instanceof Error ? err : new Error(String(err));
                    this.logger.error({
                        id: LogId.atlasDeleteDatabaseUserFailure,
                        context: "session",
                        message: `Error deleting previous database user: ${error.message}`,
                    });
                });
        }
    }

    async close(): Promise<void> {
        await this.disconnect();
        await this.apiClient?.close();
        await this.exportsManager.close();
        this.emit("close");
    }

    async connectToConfiguredConnection(): Promise<void> {
        const connectionInfo = generateConnectionInfoFromCliArgs({
            ...this.userConfig,
            connectionSpecifier: this.userConfig.connectionString,
        });
        await this.connectToMongoDB(connectionInfo);
    }

    async connectToMongoDB(settings: ConnectionSettings): Promise<void> {
        await this.connectionManager.connect({ ...settings });
    }

    get isConnectedToMongoDB(): boolean {
        return this.connectionManager.currentConnectionState.tag === "connected";
    }

    async isSearchSupported(): Promise<boolean> {
        const state = this.connectionManager.currentConnectionState;
        if (state.tag === "connected") {
            return await state.isSearchSupported();
        }

        return false;
    }

    async assertSearchSupported(): Promise<void> {
        const isSearchSupported = await this.isSearchSupported();
        if (!isSearchSupported) {
            throw new MongoDBError(
                ErrorCodes.AtlasSearchNotSupported,
                "Atlas Search is not supported in the current cluster."
            );
        }
    }

    get serviceProvider(): NodeDriverServiceProvider {
        if (this.isConnectedToMongoDB) {
            const state = this.connectionManager.currentConnectionState as ConnectionStateConnected;
            return state.serviceProvider;
        }

        throw new MongoDBError(ErrorCodes.NotConnectedToMongoDB, "Not connected to MongoDB");
    }

    get connectedAtlasCluster(): AtlasClusterConnectionInfo | undefined {
        return this.connectionManager.currentConnectionState.connectedAtlasCluster;
    }

    get connectionStringInfo(): ConnectionStringInfo | undefined {
        return this.connectionManager.currentConnectionState.connectionStringInfo;
    }
}
