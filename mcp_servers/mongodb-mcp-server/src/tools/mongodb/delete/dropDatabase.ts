import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType } from "../../tool.js";

export class DropDatabaseTool extends MongoDBToolBase {
    public name = "drop-database";
    public description = "Removes the specified database, deleting the associated data files";
    public argsShape = {
        database: DbOperationArgs.database,
    };
    static operationType: OperationType = "delete";

    protected async execute({ database }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const result = await provider.dropDatabase(database);

        return {
            content: [
                {
                    text: `${result.ok ? "Successfully dropped" : "Failed to drop"} database "${database}"`,
                    type: "text",
                },
            ],
        };
    }

    protected getConfirmationMessage({ database }: ToolArgs<typeof this.argsShape>): string {
        return (
            `You are about to drop the \`${database}\` database:\n\n` +
            "This operation will permanently remove the database and ALL its collections, documents, and indexes.\n\n" +
            "**Do you confirm the execution of the action?**"
        );
    }
}
