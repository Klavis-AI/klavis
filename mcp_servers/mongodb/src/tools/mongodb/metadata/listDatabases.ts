import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { MongoDBToolBase } from "../mongodbTool.js";
import * as bson from "bson";
import { OperationType } from "../../tool.js";

export class ListDatabasesTool extends MongoDBToolBase {
    public name = "list-databases";
    protected description = "List all databases for a MongoDB connection";
    protected argsShape = {};
    public operationType: OperationType = "metadata";

    protected async execute(): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const dbs = (await provider.listDatabases("")).databases as { name: string; sizeOnDisk: bson.Long }[];

        return {
            content: dbs.map((db) => {
                return {
                    text: `Name: ${db.name}, Size: ${db.sizeOnDisk.toString()} bytes`,
                    type: "text",
                };
            }),
        };
    }
}
