import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { EJSON } from "bson";

export class DbStatsTool extends MongoDBToolBase {
    public name = "db-stats";
    protected description = "Returns statistics that reflect the use state of a single database";
    protected argsShape = {
        database: DbOperationArgs.database,
    };

    public operationType: OperationType = "metadata";

    protected async execute({ database }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const result = await provider.runCommandWithCheck(database, {
            dbStats: 1,
            scale: 1,
        });

        return {
            content: [
                {
                    text: `Statistics for database ${database}`,
                    type: "text",
                },
                {
                    text: EJSON.stringify(result),
                    type: "text",
                },
            ],
        };
    }
}
