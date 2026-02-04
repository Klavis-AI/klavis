import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { IndexDirection } from "mongodb";

export class CreateIndexTool extends MongoDBToolBase {
    public name = "create-index";
    protected description = "Create an index for a collection";
    protected argsShape = {
        ...DbOperationArgs,
        keys: z.object({}).catchall(z.custom<IndexDirection>()).describe("The index definition"),
        name: z.string().optional().describe("The name of the index"),
    };

    public operationType: OperationType = "create";

    protected async execute({
        database,
        collection,
        keys,
        name,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const indexes = await provider.createIndexes(database, collection, [
            {
                key: keys,
                name,
            },
        ]);

        return {
            content: [
                {
                    text: `Created the index "${indexes[0]}" on collection "${collection}" in database "${database}"`,
                    type: "text",
                },
            ],
        };
    }
}
