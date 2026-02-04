import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { OperationType, ToolArgs } from "../../tool.js";

export class CreateCollectionTool extends MongoDBToolBase {
    public name = "create-collection";
    protected description =
        "Creates a new collection in a database. If the database doesn't exist, it will be created automatically.";
    protected argsShape = DbOperationArgs;

    public operationType: OperationType = "create";

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
