import z from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { type ToolArgs, type OperationType, formatUntrustedData } from "../../tool.js";

export class DropIndexTool extends MongoDBToolBase {
    public name = "drop-index";
    public description = "Drop an index for the provided database and collection.";
    public argsShape = {
        ...DbOperationArgs,
        indexName: z.string().nonempty().describe("The name of the index to be dropped."),
        type: this.isFeatureEnabled("search")
            ? z
                  .enum(["classic", "search"])
                  .describe(
                      "The type of index to be deleted. Use 'classic' for standard indexes and 'search' for atlas search and vector search indexes."
                  )
            : z
                  .literal("classic")
                  .default("classic")
                  .describe("The type of index to be deleted. Is always set to 'classic'."),
    };
    static operationType: OperationType = "delete";

    protected async execute(toolArgs: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        switch (toolArgs.type) {
            case "classic":
                return this.dropClassicIndex(provider, toolArgs);
            case "search":
                return this.dropSearchIndex(provider, toolArgs);
        }
    }

    private async dropClassicIndex(
        provider: NodeDriverServiceProvider,
        { database, collection, indexName }: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> {
        const result = await provider.runCommand(database, {
            dropIndexes: collection,
            index: indexName,
        });

        return {
            content: formatUntrustedData(
                `${result.ok ? "Successfully dropped" : "Failed to drop"} the index from the provided namespace.`,
                JSON.stringify({
                    indexName,
                    namespace: `${database}.${collection}`,
                })
            ),
            isError: result.ok ? undefined : true,
        };
    }

    private async dropSearchIndex(
        provider: NodeDriverServiceProvider,
        { database, collection, indexName }: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> {
        await this.session.assertSearchSupported();
        const indexes = await provider.getSearchIndexes(database, collection, indexName);
        if (indexes.length === 0) {
            return {
                content: formatUntrustedData(
                    "Index does not exist in the provided namespace.",
                    JSON.stringify({ indexName, namespace: `${database}.${collection}` })
                ),
                isError: true,
            };
        }

        await provider.dropSearchIndex(database, collection, indexName);
        return {
            content: formatUntrustedData(
                "Successfully dropped the index from the provided namespace.",
                JSON.stringify({
                    indexName,
                    namespace: `${database}.${collection}`,
                })
            ),
        };
    }

    protected getConfirmationMessage({
        database,
        collection,
        indexName,
        type,
    }: ToolArgs<typeof this.argsShape>): string {
        return (
            `You are about to drop the ${type === "search" ? "search index" : "index"} named \`${indexName}\` from the \`${database}.${collection}\` namespace:\n\n` +
            "This operation will permanently remove the index and might affect the performance of queries relying on this index.\n\n" +
            "**Do you confirm the execution of the action?**"
        );
    }
}
