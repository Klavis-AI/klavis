import z from "zod";
import { type CallToolResult } from "@modelcontextprotocol/sdk/types.js";

import { MongoDBToolBase } from "../mongodbTool.js";
import { type ToolArgs, type OperationType, type ToolConstructorParams } from "../../tool.js";
import type { Server } from "../../../server.js";

export class SwitchConnectionTool extends MongoDBToolBase {
    public override name = "switch-connection";
    public override description =
        "Switch to a different MongoDB connection. If the user has configured a connection string or has previously called the connect tool, a connection is already established and there's no need to call this tool unless the user has explicitly requested to switch to a new instance.";

    public override argsShape = {
        connectionString: z
            .string()
            .optional()
            .describe(
                "MongoDB connection string to switch to (in the mongodb:// or mongodb+srv:// format). If a connection string is not provided, the connection string from the config will be used."
            ),
    };

    static operationType: OperationType = "connect";

    constructor(params: ToolConstructorParams) {
        super(params);
        params.session.on("connect", () => {
            this.enable();
        });

        params.session.on("disconnect", () => {
            this.disable();
        });
    }

    public override register(server: Server): boolean {
        const registrationSuccessful = super.register(server);
        /**
         * When connected to mongodb we want to swap connect with
         * switch-connection tool.
         */
        if (registrationSuccessful && !this.session.isConnectedToMongoDB) {
            this.disable();
        }
        return registrationSuccessful;
    }

    protected override async execute({ connectionString }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        if (typeof connectionString !== "string") {
            await this.session.connectToConfiguredConnection();
        } else {
            await this.session.connectToMongoDB({ connectionString });
        }

        return {
            content: [{ type: "text", text: "Successfully connected to MongoDB." }],
        };
    }
}
