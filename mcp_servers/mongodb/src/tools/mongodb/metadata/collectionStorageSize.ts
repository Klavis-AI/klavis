import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";

export class CollectionStorageSizeTool extends MongoDBToolBase {
    public name = "collection-storage-size";
    public description = "Gets the size of the collection";
    public argsShape = DbOperationArgs;

    static operationType: OperationType = "metadata";

    protected async execute(
        { database, collection }: ToolArgs<typeof DbOperationArgs>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const [{ value }] = (await provider
            .aggregate(
                database,
                collection,
                [
                    { $collStats: { storageStats: {} } },
                    { $group: { _id: null, value: { $sum: "$storageStats.size" } } },
                ],
                {
                    // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                    signal,
                }
            )
            .toArray()) as [{ value: number }];

        const { units, value: scaledValue } = CollectionStorageSizeTool.getStats(value);

        return {
            content: [
                {
                    text: `The size of "${database}.${collection}" is \`${scaledValue.toFixed(2)} ${units}\``,
                    type: "text",
                },
            ],
        };
    }

    protected handleError(
        error: unknown,
        args: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> | CallToolResult {
        if (error instanceof Error && "codeName" in error && error.codeName === "NamespaceNotFound") {
            return {
                content: [
                    {
                        text: `The size of "${args.database}.${args.collection}" cannot be determined because the collection does not exist.`,
                        type: "text",
                    },
                ],
                isError: true,
            };
        }

        return super.handleError(error, args);
    }

    private static getStats(value: number): { value: number; units: string } {
        const kb = 1024;
        const mb = kb * 1024;
        const gb = mb * 1024;

        if (value > gb) {
            return { value: value / gb, units: "GB" };
        }

        if (value > mb) {
            return { value: value / mb, units: "MB" };
        }
        if (value > kb) {
            return { value: value / kb, units: "KB" };
        }
        return { value, units: "bytes" };
    }
}
