import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";
import { zEJSON } from "../../args.js";

export const CountArgs = {
    query: zEJSON()
        .optional()
        .describe(
            "A filter/query parameter. Allows users to filter the documents to count. Matches the syntax of the filter argument of db.collection.count()."
        ),
};

export class CountTool extends MongoDBToolBase {
    public name = "count";
    public description =
        "Gets the number of documents in a MongoDB collection using db.collection.count() and query as an optional filter parameter";
    public argsShape = {
        ...DbOperationArgs,
        ...CountArgs,
    };

    static operationType: OperationType = "read";

    protected async execute(
        { database, collection, query }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if count operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage({
                database,
                collection,
                operation: "count",
                explainCallback: async () => {
                    return provider.runCommandWithCheck(
                        database,
                        {
                            explain: {
                                count: collection,
                                query,
                            },
                            verbosity: "queryPlanner",
                        },
                        {
                            signal,
                        }
                    );
                },
                logger: this.session.logger,
            });
        }

        const count = await provider.countDocuments(database, collection, query, {
            // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
            signal,
        });

        return {
            content: [
                {
                    text: `Found ${count} documents in the collection "${collection}"${query ? " that matched the query" : ""}.`,
                    type: "text",
                },
            ],
        };
    }
}
