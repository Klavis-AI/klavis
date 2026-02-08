import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";

export class DeleteManyTool extends MongoDBToolBase {
    public name = "delete-many";
    protected description = "Removes all documents that match the filter from a MongoDB collection";
    protected argsShape = {
        ...DbOperationArgs,
        filter: z
            .object({})
            .passthrough()
            .optional()
            .describe(
                "The query filter, specifying the deletion criteria. Matches the syntax of the filter argument of db.collection.deleteMany()"
            ),
    };
    public operationType: OperationType = "delete";

    protected async execute({
        database,
        collection,
        filter,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if delete operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage(provider, database, collection, "deleteMany", async () => {
                return provider.runCommandWithCheck(database, {
                    explain: {
                        delete: collection,
                        deletes: [
                            {
                                q: filter || {},
                                limit: 0, // 0 means delete all matching documents
                            },
                        ],
                    },
                    verbosity: "queryPlanner",
                });
            });
        }

        const result = await provider.deleteMany(database, collection, filter);

        return {
            content: [
                {
                    text: `Deleted \`${result.deletedCount}\` document(s) from collection "${collection}"`,
                    type: "text",
                },
            ],
        };
    }
}
