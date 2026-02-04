import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { SortDirection } from "mongodb";
import { EJSON } from "bson";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";

export const FindArgs = {
    filter: z
        .object({})
        .passthrough()
        .optional()
        .describe("The query filter, matching the syntax of the query argument of db.collection.find()"),
    projection: z
        .object({})
        .passthrough()
        .optional()
        .describe("The projection, matching the syntax of the projection argument of db.collection.find()"),
    limit: z.number().optional().default(10).describe("The maximum number of documents to return"),
    sort: z
        .object({})
        .catchall(z.custom<SortDirection>())
        .optional()
        .describe(
            "A document, describing the sort order, matching the syntax of the sort argument of cursor.sort(). The keys of the object are the fields to sort on, while the values are the sort directions (1 for ascending, -1 for descending)."
        ),
};

export class FindTool extends MongoDBToolBase {
    public name = "find";
    protected description = "Run a find query against a MongoDB collection";
    protected argsShape = {
        ...DbOperationArgs,
        ...FindArgs,
    };
    public operationType: OperationType = "read";

    protected async execute({
        database,
        collection,
        filter,
        projection,
        limit,
        sort,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        // Check if find operation uses an index if enabled
        if (this.config.indexCheck) {
            await checkIndexUsage(provider, database, collection, "find", async () => {
                return provider.find(database, collection, filter, { projection, limit, sort }).explain("queryPlanner");
            });
        }

        const documents = await provider.find(database, collection, filter, { projection, limit, sort }).toArray();

        const content: Array<{ text: string; type: "text" }> = [
            {
                text: `Found ${documents.length} documents in the collection "${collection}":`,
                type: "text",
            },
            ...documents.map((doc) => {
                return {
                    text: EJSON.stringify(doc),
                    type: "text",
                } as { text: string; type: "text" };
            }),
        ];

        return {
            content,
        };
    }
}
