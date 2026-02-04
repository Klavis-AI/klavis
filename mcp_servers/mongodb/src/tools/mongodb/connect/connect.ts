import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import assert from "assert";
import { UserConfig } from "../../../common/config.js";
import { Telemetry } from "../../../telemetry/telemetry.js";
import { Session } from "../../../common/session.js";
import { Server } from "../../../server.js";

const disconnectedSchema = z
    .object({
        connectionString: z.string().describe("MongoDB connection string (in the mongodb:// or mongodb+srv:// format)"),
    })
    .describe("Options for connecting to MongoDB.");

const connectedSchema = z
    .object({
        connectionString: z
            .string()
            .optional()
            .describe("MongoDB connection string to switch to (in the mongodb:// or mongodb+srv:// format)"),
    })
    .describe(
        "Options for switching the current MongoDB connection. If a connection string is not provided, the connection string from the config will be used."
    );

const connectedName = "switch-connection" as const;
const disconnectedName = "connect" as const;

const connectedDescription =
    "Switch to a different MongoDB connection. If the user has configured a connection string or has previously called the connect tool, a connection is already established and there's no need to call this tool unless the user has explicitly requested to switch to a new instance.";
const disconnectedDescription = "Connect to a MongoDB instance";

export class ConnectTool extends MongoDBToolBase {
    public name: typeof connectedName | typeof disconnectedName = disconnectedName;
    protected description: typeof connectedDescription | typeof disconnectedDescription = disconnectedDescription;

    // Here the default is empty just to trigger registration, but we're going to override it with the correct
    // schema in the register method.
    protected argsShape = {
        connectionString: z.string().optional(),
    };

    public operationType: OperationType = "connect";

    constructor(session: Session, config: UserConfig, telemetry: Telemetry) {
        super(session, config, telemetry);
        session.on("disconnect", () => {
            this.updateMetadata();
        });
    }

    protected async execute({ connectionString }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        switch (this.name) {
            case disconnectedName:
                assert(connectionString, "Connection string is required");
                break;
            case connectedName:
                connectionString ??= this.config.connectionString;
                assert(
                    connectionString,
                    "Cannot switch to a new connection because no connection string was provided and no default connection string is configured."
                );
                break;
        }

        await this.connectToMongoDB(connectionString);
        this.updateMetadata();
        return {
            content: [{ type: "text", text: "Successfully connected to MongoDB." }],
        };
    }

    public register(server: Server): boolean {
        if (super.register(server)) {
            this.updateMetadata();
            return true;
        }

        return false;
    }

    private updateMetadata(): void {
        if (this.config.connectionString || this.session.serviceProvider) {
            this.update?.({
                name: connectedName,
                description: connectedDescription,
                inputSchema: connectedSchema,
            });
        } else {
            this.update?.({
                name: disconnectedName,
                description: disconnectedDescription,
                inputSchema: disconnectedSchema,
            });
        }
    }
}
