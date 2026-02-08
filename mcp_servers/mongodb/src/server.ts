import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Session } from "./common/session.js";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { AtlasTools } from "./tools/atlas/tools.js";
import { MongoDbTools } from "./tools/mongodb/tools.js";
import logger, { LogId, LoggerBase, McpLogger, DiskLogger, ConsoleLogger } from "./common/logger.js";
import { ObjectId } from "mongodb";
import { Telemetry } from "./telemetry/telemetry.js";
import { UserConfig } from "./common/config.js";
import { type ServerEvent } from "./telemetry/types.js";
import { type ServerCommand } from "./telemetry/types.js";
import { CallToolRequestSchema, CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "assert";
import { ToolBase } from "./tools/tool.js";

export interface ServerOptions {
    session: Session;
    userConfig: UserConfig;
    mcpServer: McpServer;
    telemetry: Telemetry;
}

export class Server {
    public readonly session: Session;
    public readonly mcpServer: McpServer;
    private readonly telemetry: Telemetry;
    public readonly userConfig: UserConfig;
    public readonly tools: ToolBase[] = [];
    private readonly startTime: number;

    constructor({ session, mcpServer, userConfig, telemetry }: ServerOptions) {
        this.startTime = Date.now();
        this.session = session;
        this.telemetry = telemetry;
        this.mcpServer = mcpServer;
        this.userConfig = userConfig;
    }

    async connect(transport: Transport): Promise<void> {
        await this.validateConfig();

        this.mcpServer.server.registerCapabilities({ logging: {} });

        this.registerTools();
        this.registerResources();

        // This is a workaround for an issue we've seen with some models, where they'll see that everything in the `arguments`
        // object is optional, and then not pass it at all. However, the MCP server expects the `arguments` object to be if
        // the tool accepts any arguments, even if they're all optional.
        //
        // see: https://github.com/modelcontextprotocol/typescript-sdk/blob/131776764536b5fdca642df51230a3746fb4ade0/src/server/mcp.ts#L705
        // Since paramsSchema here is not undefined, the server will create a non-optional z.object from it.
        const existingHandler = (
            this.mcpServer.server["_requestHandlers"] as Map<
                string,
                (request: unknown, extra: unknown) => Promise<CallToolResult>
            >
        ).get(CallToolRequestSchema.shape.method.value);

        assert(existingHandler, "No existing handler found for CallToolRequestSchema");

        this.mcpServer.server.setRequestHandler(CallToolRequestSchema, (request, extra): Promise<CallToolResult> => {
            if (!request.params.arguments) {
                request.params.arguments = {};
            }

            return existingHandler(request, extra);
        });

        const loggers: LoggerBase[] = [];
        if (this.userConfig.loggers.includes("mcp")) {
            loggers.push(new McpLogger(this.mcpServer));
        }
        if (this.userConfig.loggers.includes("disk")) {
            loggers.push(await DiskLogger.fromPath(this.userConfig.logPath));
        }
        if (this.userConfig.loggers.includes("stderr")) {
            loggers.push(new ConsoleLogger());
        }
        logger.setLoggers(...loggers);

        this.mcpServer.server.oninitialized = () => {
            this.session.setAgentRunner(this.mcpServer.server.getClientVersion());
            this.session.sessionId = new ObjectId().toString();

            logger.info(
                LogId.serverInitialized,
                "server",
                `Server started with transport ${transport.constructor.name} and agent runner ${this.session.agentRunner?.name}`
            );

            this.emitServerEvent("start", Date.now() - this.startTime);
        };

        this.mcpServer.server.onclose = () => {
            const closeTime = Date.now();
            this.emitServerEvent("stop", Date.now() - closeTime);
        };

        this.mcpServer.server.onerror = (error: Error) => {
            const closeTime = Date.now();
            this.emitServerEvent("stop", Date.now() - closeTime, error);
        };

        await this.mcpServer.connect(transport);
    }

    async close(): Promise<void> {
        await this.telemetry.close();
        await this.session.close();
        await this.mcpServer.close();
    }

    /**
     * Emits a server event
     * @param command - The server command (e.g., "start", "stop", "register", "deregister")
     * @param additionalProperties - Additional properties specific to the event
     */
    private emitServerEvent(command: ServerCommand, commandDuration: number, error?: Error) {
        const event: ServerEvent = {
            timestamp: new Date().toISOString(),
            source: "mdbmcp",
            properties: {
                result: "success",
                duration_ms: commandDuration,
                component: "server",
                category: "other",
                command: command,
            },
        };

        if (command === "start") {
            event.properties.startup_time_ms = commandDuration;
            event.properties.read_only_mode = this.userConfig.readOnly || false;
            event.properties.disabled_tools = this.userConfig.disabledTools || [];
        }
        if (command === "stop") {
            event.properties.runtime_duration_ms = Date.now() - this.startTime;
            if (error) {
                event.properties.result = "failure";
                event.properties.reason = error.message;
            }
        }

        this.telemetry.emitEvents([event]).catch(() => {});
    }

    private registerTools() {
        for (const toolConstructor of [...AtlasTools, ...MongoDbTools]) {
            const tool = new toolConstructor(this.session, this.userConfig, this.telemetry);
            if (tool.register(this)) {
                this.tools.push(tool);
            }
        }
    }

    private registerResources() {
        this.mcpServer.resource(
            "config",
            "config://config",
            {
                description:
                    "Server configuration, supplied by the user either as environment variables or as startup arguments",
            },
            (uri) => {
                const result = {
                    telemetry: this.userConfig.telemetry,
                    logPath: this.userConfig.logPath,
                    connectionString: this.userConfig.connectionString
                        ? "set; access to MongoDB tools are currently available to use"
                        : "not set; before using any MongoDB tool, you need to configure a connection string, alternatively you can setup MongoDB Atlas access, more info at 'https://github.com/mongodb-js/mongodb-mcp-server'.",
                    connectOptions: this.userConfig.connectOptions,
                    atlas:
                        this.userConfig.apiClientId && this.userConfig.apiClientSecret
                            ? "set; MongoDB Atlas tools are currently available to use"
                            : "not set; MongoDB Atlas tools are currently unavailable, to have access to MongoDB Atlas tools like creating clusters or connecting to clusters make sure to setup credentials, more info at 'https://github.com/mongodb-js/mongodb-mcp-server'.",
                };
                return {
                    contents: [
                        {
                            text: JSON.stringify(result),
                            mimeType: "application/json",
                            uri: uri.href,
                        },
                    ],
                };
            }
        );
    }

    private async validateConfig(): Promise<void> {
        const transport = this.userConfig.transport as string;
        if (transport !== "http" && transport !== "stdio") {
            throw new Error(`Invalid transport: ${transport}`);
        }

        const telemetry = this.userConfig.telemetry as string;
        if (telemetry !== "enabled" && telemetry !== "disabled") {
            throw new Error(`Invalid telemetry: ${telemetry}`);
        }

        if (this.userConfig.httpPort < 1 || this.userConfig.httpPort > 65535) {
            throw new Error(`Invalid httpPort: ${this.userConfig.httpPort}`);
        }

        if (this.userConfig.loggers.length === 0) {
            throw new Error("No loggers found in config");
        }

        const loggerTypes = new Set(this.userConfig.loggers);
        if (loggerTypes.size !== this.userConfig.loggers.length) {
            throw new Error("Duplicate loggers found in config");
        }

        for (const loggerType of this.userConfig.loggers as string[]) {
            if (loggerType !== "mcp" && loggerType !== "disk" && loggerType !== "stderr") {
                throw new Error(`Invalid logger: ${loggerType}`);
            }
        }

        if (this.userConfig.connectionString) {
            try {
                await this.session.connectToMongoDB(this.userConfig.connectionString, this.userConfig.connectOptions);
            } catch (error) {
                console.error(
                    "Failed to connect to MongoDB instance using the connection string from the config: ",
                    error
                );
                throw new Error("Failed to connect to MongoDB instance using the connection string from the config");
            }
        }

        if (this.userConfig.apiClientId && this.userConfig.apiClientSecret) {
            try {
                await this.session.apiClient.validateAccessToken();
            } catch (error) {
                if (this.userConfig.connectionString === undefined) {
                    console.error("Failed to validate MongoDB Atlas the credentials from the config: ", error);

                    throw new Error(
                        "Failed to connect to MongoDB Atlas instance using the credentials from the config"
                    );
                }
                console.error(
                    "Failed to validate MongoDB Atlas the credentials from the config, but validated the connection string."
                );
            }
        }
    }
}
