import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";

export class UpdateManyTool extends MongoDBToolBase {
    public name = "update-many";
    protected description = "Updates all documents that match the specified filter for a collection";
    protected argsShape = {
        ...DbOperationArgs,
        filter: z
            .object({})
            .passthrough()
            .optional()
            .describe(
                "The selection criteria for the update, matching the syntax of the filter argument of db.collection.updateOne()"
            ),
        update: z
            .object({})
            .passthrough()
            .describe("An update document describing the modifications to apply using update operator expressions"),
        upsert: z
            .boolean()
            .optional()
            .describe("Controls whether to insert a new document if no documents match the filter"),
    };
    public operationType: OperationType = "update";

    protected async execute({
        database,
        collection,
        filter,
        update,
        upsert,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if update operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage(provider, database, collection, "updateMany", async () => {
                return provider.runCommandWithCheck(database, {
                    explain: {
                        update: collection,
                        updates: [
                            {
                                q: filter || {},
                                u: update,
                                upsert: upsert || false,
                                multi: true,
                            },
                        ],
                    },
                    verbosity: "queryPlanner",
                });
            });
        }

        const result = await provider.updateMany(database, collection, filter, update, {
            upsert,
        });

        let message = "";
        if (result.matchedCount === 0 && result.modifiedCount === 0 && result.upsertedCount === 0) {
            message = "No documents matched the filter.";
        } else {
            message = `Matched ${result.matchedCount} document(s).`;
            if (result.modifiedCount > 0) {
                message += ` Modified ${result.modifiedCount} document(s).`;
            }
            if (result.upsertedCount > 0) {
                message += ` Upserted ${result.upsertedCount} document with id: ${result.upsertedId?.toString()}.`;
            }
        }

        return {
            content: [
                {
                    text: message,
                    type: "text",
                },
            ],
        };
    }
}
