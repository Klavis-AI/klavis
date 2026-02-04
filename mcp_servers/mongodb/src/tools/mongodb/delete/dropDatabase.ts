import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";

export class DropDatabaseTool extends MongoDBToolBase {
    public name = "drop-database";
    protected description = "Removes the specified database, deleting the associated data files";
    protected argsShape = {
        database: DbOperationArgs.database,
    };
    public operationType: OperationType = "delete";

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
}
