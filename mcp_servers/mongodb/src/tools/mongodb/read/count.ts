import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { z } from "zod";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";

export const CountArgs = {
    query: z
        .object({})
        .passthrough()
        .optional()
        .describe(
            "A filter/query parameter. Allows users to filter the documents to count. Matches the syntax of the filter argument of db.collection.count()."
        ),
};

export class CountTool extends MongoDBToolBase {
    public name = "count";
    protected description =
        "Gets the number of documents in a MongoDB collection using db.collection.count() and query as an optional filter parameter";
    protected argsShape = {
        ...DbOperationArgs,
        ...CountArgs,
    };

    public operationType: OperationType = "read";

    protected async execute({ database, collection, query }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if count operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage(provider, database, collection, "count", async () => {
                return provider.runCommandWithCheck(database, {
                    explain: {
                        count: collection,
                        query,
                    },
                    verbosity: "queryPlanner",
                });
            });
        }

        const count = await provider.count(database, collection, query);

        return {
            content: [
                {
                    text: `Found ${count} documents in the collection "${collection}"`,
                    type: "text",
                },
            ],
        };
    }
}
