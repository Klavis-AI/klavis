import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import { EJSON } from "bson";

export class DbStatsTool extends MongoDBToolBase {
    public name = "db-stats";
    public description = "Returns statistics that reflect the use state of a single database";
    public argsShape = {
        database: DbOperationArgs.database,
    };

    static operationType: OperationType = "metadata";

    protected async execute(
        { database }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const result = await provider.runCommandWithCheck(
            database,
            {
                dbStats: 1,
                scale: 1,
            },
            { signal }
        );

        return {
            content: formatUntrustedData(`Statistics for database ${database}`, EJSON.stringify(result)),
        };
    }
}
