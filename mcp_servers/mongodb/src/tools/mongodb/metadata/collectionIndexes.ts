import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import type { Document } from "bson";

type IndexStatus = {
    name: string;
    key: Document;
};

export class CollectionIndexesTool extends MongoDBToolBase {
    public name = "collection-indexes";
    public description = "Describe the indexes for a collection";
    public argsShape = DbOperationArgs;
    static operationType: OperationType = "metadata";

    protected async execute({ database, collection }: ToolArgs<typeof DbOperationArgs>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const indexes = await provider.getIndexes(database, collection);
        const indexDefinitions: IndexStatus[] = indexes.map((index) => ({
            name: index.name as string,
            key: index.key as Document,
        }));

        const searchIndexDefinitions: Document[] = [];
        if (this.isFeatureEnabled("search") && (await this.session.isSearchSupported())) {
            const searchIndexes = await provider.getSearchIndexes(database, collection);
            searchIndexDefinitions.push(...this.extractSearchIndexDetails(searchIndexes));
        }

        return {
            content: [
                ...formatUntrustedData(
                    `Found ${indexDefinitions.length} classic indexes in the collection "${collection}":`,
                    ...indexDefinitions.map((i) => JSON.stringify(i))
                ),
                ...(searchIndexDefinitions.length > 0
                    ? formatUntrustedData(
                          `Found ${searchIndexDefinitions.length} search and vector search indexes in the collection "${collection}":`,
                          ...searchIndexDefinitions.map((i) => JSON.stringify(i))
                      )
                    : []),
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
                        text: `The indexes for "${args.database}.${args.collection}" cannot be determined because the collection does not exist.`,
                        type: "text",
                    },
                ],
                isError: true,
            };
        }

        return super.handleError(error, args);
    }

    /**
     * Atlas Search index status contains a lot of information that is not relevant for the agent at this stage.
     * Like for example, the status on each of the dedicated nodes. We only care about the main status, if it's
     * queryable and the index name. We are also picking the index definition as it can be used by the agent to
     * understand which fields are available for searching.
     **/
    protected extractSearchIndexDetails(indexes: Record<string, unknown>[]): Document[] {
        return indexes.map((index) => {
            const result: Document = {};

            if (index["name"] !== undefined) {
                result.name = index["name"];
            }
            if (index["type"] !== undefined) {
                result.type = index["type"];
            }
            if (index["status"] !== undefined) {
                result.status = index["status"];
            }
            if (index["queryable"] !== undefined) {
                result.queryable = index["queryable"];
            }
            if (index["latestDefinition"] !== undefined) {
                result.latestDefinition = index["latestDefinition"];
            }

            return result;
        });
    }
}
