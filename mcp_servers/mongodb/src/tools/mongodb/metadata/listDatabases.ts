import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { MongoDBToolBase } from "../mongodbTool.js";
import type * as bson from "bson";
import type { OperationType } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import { z } from "zod";

export const ListDatabasesOutputSchema = {
    databases: z.array(
        z.object({
            name: z.string(),
            size: z.number(),
        })
    ),
    totalCount: z.number(),
};

// JSDoc comment needed to tell knip that this is intentionally public
/** @public - Used by UI components */
export type ListDatabasesOutput = z.infer<z.ZodObject<typeof ListDatabasesOutputSchema>>;

export class ListDatabasesTool extends MongoDBToolBase {
    public name = "list-databases";
    public description = "List all databases for a MongoDB connection";
    public argsShape = {};
    public override outputSchema = ListDatabasesOutputSchema;
    static operationType: OperationType = "metadata";

    protected async execute(): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const dbs = (await provider.listDatabases("")).databases as { name: string; sizeOnDisk: bson.Long }[];
        const databases = dbs.map((db) => ({
            name: db.name,
            size: Number(db.sizeOnDisk),
        }));

        return {
            content: formatUntrustedData(
                `Found ${dbs.length} databases`,
                ...dbs.map((db) => `Name: ${db.name}, Size: ${db.sizeOnDisk.toString()} bytes`)
            ),
            structuredContent: {
                databases,
                totalCount: databases.length,
            },
        };
    }
}
