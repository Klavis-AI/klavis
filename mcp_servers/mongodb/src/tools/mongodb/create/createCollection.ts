import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { OperationType, ToolArgs } from "../../tool.js";

export class CreateCollectionTool extends MongoDBToolBase {
    public name = "create-collection";
    public description =
        "Creates a new collection in a database. If the database doesn't exist, it will be created automatically.";
    public argsShape = DbOperationArgs;

    static operationType: OperationType = "create";

    protected async execute({ collection, database }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        await provider.createCollection(database, collection);

        return {
            content: [
                {
                    type: "text",
                    text: `Collection "${collection}" created in database "${database}".`,
                },
            ],
        };
    }
}
