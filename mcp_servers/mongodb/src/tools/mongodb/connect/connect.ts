import { z } from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolConstructorParams } from "../../tool.js";
import type { Server } from "../../../server.js";
export class ConnectTool extends MongoDBToolBase {
    public override name = "connect";
    public override description =
        "Connect to a MongoDB instance. The config resource captures if the server is already connected to a MongoDB cluster. If the user has configured a connection string or has previously called the connect tool, a connection is already established and there's no need to call this tool unless the user has explicitly requested to switch to a new MongoDB cluster.";

    // Here the default is empty just to trigger registration, but we're going to override it with the correct
    // schema in the register method.
    public override argsShape = {
        connectionString: z.string().describe("MongoDB connection string (in the mongodb:// or mongodb+srv:// format)"),
    };

    static operationType: OperationType = "connect";

    constructor(params: ToolConstructorParams) {
        super(params);
        params.session.on("connect", () => {
            this.disable();
        });

        params.session.on("disconnect", () => {
            this.enable();
        });
    }

    public override register(server: Server): boolean {
        const registrationSuccessful = super.register(server);
        /**
         * When connected to mongodb we want to swap connect with
         * switch-connection tool.
         */
        if (registrationSuccessful && this.session.isConnectedToMongoDB) {
            this.disable();
        }
        return registrationSuccessful;
    }

    protected override async execute({ connectionString }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        await this.session.connectToMongoDB({ connectionString });

        return {
            content: [{ type: "text", text: "Successfully connected to MongoDB." }],
        };
    }
}
