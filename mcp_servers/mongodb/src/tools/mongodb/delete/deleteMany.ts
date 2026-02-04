import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType } from "../../tool.js";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";
import { EJSON } from "bson";
import { zEJSON } from "../../args.js";

export class DeleteManyTool extends MongoDBToolBase {
    public name = "delete-many";
    public description = "Removes all documents that match the filter from a MongoDB collection";
    public argsShape = {
        ...DbOperationArgs,
        filter: zEJSON()
            .optional()
            .describe(
                "The query filter, specifying the deletion criteria. Matches the syntax of the filter argument of db.collection.deleteMany()"
            ),
    };
    static operationType: OperationType = "delete";

    protected async execute({
        database,
        collection,
        filter,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if delete operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage({
                database,
                collection,
                operation: "deleteMany",
                explainCallback: async () => {
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
                },
                logger: this.session.logger,
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

    protected getConfirmationMessage({ database, collection, filter }: ToolArgs<typeof this.argsShape>): string {
        const filterDescription =
            filter && Object.keys(filter).length > 0
                ? "```json\n" + `{ "filter": ${EJSON.stringify(filter)} }\n` + "```\n\n"
                : "- **All documents** (No filter)\n\n";
        return (
            `You are about to delete documents from the \`${collection}\` collection in the \`${database}\` database:\n\n` +
            filterDescription +
            "This operation will permanently remove all documents matching the filter.\n\n" +
            "**Do you confirm the execution of the action?**"
        );
    }
}
