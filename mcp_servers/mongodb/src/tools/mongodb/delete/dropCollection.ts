import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType } from "../../tool.js";

export class DropCollectionTool extends MongoDBToolBase {
    public name = "drop-collection";
    public description =
        "Removes a collection or view from the database. The method also removes any indexes associated with the dropped collection.";
    public argsShape = {
        ...DbOperationArgs,
    };
    static operationType: OperationType = "delete";

    protected async execute({ database, collection }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const result = await provider.dropCollection(database, collection);

        return {
            content: [
                {
                    text: `${result ? "Successfully dropped" : "Failed to drop"} collection "${collection}" from database "${database}"`,
                    type: "text",
                },
            ],
        };
    }

    protected getConfirmationMessage({ database, collection }: ToolArgs<typeof this.argsShape>): string {
        return (
            `You are about to drop the \`${collection}\` collection from the \`${database}\` database:\n\n` +
            "This operation will permanently remove the collection and all its data, including indexes.\n\n" +
            "**Do you confirm the execution of the action?**"
        );
    }
}
