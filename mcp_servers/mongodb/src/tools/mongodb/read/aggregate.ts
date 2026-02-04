import { z } from "zod";
import type { AggregationCursor } from "mongodb";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";
import { type Document, EJSON } from "bson";
import { ErrorCodes, MongoDBError } from "../../../common/errors.js";
import { collectCursorUntilMaxBytesLimit } from "../../../helpers/collectCursorUntilMaxBytes.js";
import { operationWithFallback } from "../../../helpers/operationWithFallback.js";
import { AGG_COUNT_MAX_TIME_MS_CAP, ONE_MB, CURSOR_LIMITS_TO_LLM_TEXT } from "../../../helpers/constants.js";
import { LogId } from "../../../common/logger.js";
import { AnyAggregateStage, VectorSearchStage } from "../mongodbSchemas.js";
import {
    assertVectorSearchFilterFieldsAreIndexed,
    type SearchIndex,
} from "../../../helpers/assertVectorSearchFilterFieldsAreIndexed.js";
import type { AutoEmbeddingsUsageMetadata, ConnectionMetadata } from "../../../telemetry/types.js";

export const pipelineDescriptionWithVectorSearch = `\
An array of aggregation stages to execute.
If the user has asked for a vector search, \`$vectorSearch\` **MUST** be the first stage of the pipeline, or the first stage of a \`$unionWith\` subpipeline.
If the user has asked for lexical/Atlas search, use \`$search\` instead of \`$text\`.
### Usage Rules for \`$vectorSearch\`
- **Index Type Detection:**
  Use the collection-indexes tool to determine if the target field has a classic vector index (type: 'vector') or an auto-embed index (type: 'autoEmbed').
- **Classic Vector Search (type: 'vector'):**
  Use 'queryVector' with embeddings as an array of numbers, or as a string with 'embeddingParameters' to generate embeddings.
- **Auto-Embed Vector Search (type: 'autoEmbed'):**
  Use 'query' - MongoDB automatically generates embeddings at query time. Do NOT use 'queryVector' or 'embeddingParameters' for auto-embed indexes.
- **Unset embeddings:**
  Unless the user explicitly requests the embeddings, add an \`$unset\` stage **at the end of the pipeline** to remove the embedding field and avoid context limits. **The $unset stage in this situation is mandatory**.
- **Pre-filtering:**
  If the user requests additional filtering, include filters in \`$vectorSearch.filter\` only for pre-filter fields in the vector index.
  NEVER include fields in $vectorSearch.filter that are not part of the vector index.
- **Post-filtering:**
  For all remaining filters, add a $match stage after $vectorSearch.
- If unsure which fields are filterable, use the collection-indexes tool to determine valid prefilter fields.
- If no requested filters are valid prefilters, omit the filter key from $vectorSearch.

### Usage Rules for \`$search\`
- Include the index name, unless you know for a fact there's a default index. If unsure, use the collection-indexes tool to determine the index name.
- The \`$search\` stage supports multiple operators, such as 'autocomplete', 'text', 'geoWithin', and others. Choose the approprate operator based on the user's query. If unsure of the exact syntax, consult the MongoDB Atlas Search documentation, which can be found here: https://www.mongodb.com/docs/atlas/atlas-search/operators-and-collectors/
`;

const genericPipelineDescription = "An array of aggregation stages to execute.";

export const getAggregateArgs = (vectorSearchEnabled: boolean) =>
    ({
        pipeline: z
            .array(vectorSearchEnabled ? z.union([VectorSearchStage, AnyAggregateStage]) : AnyAggregateStage)
            .describe(vectorSearchEnabled ? pipelineDescriptionWithVectorSearch : genericPipelineDescription),
    }) as const;

export class AggregateTool extends MongoDBToolBase {
    public name = "aggregate";
    public description = "Run an aggregation against a MongoDB collection";
    public argsShape = {
        ...DbOperationArgs,
        ...getAggregateArgs(this.isFeatureEnabled("search")),
        responseBytesLimit: z.number().optional().default(ONE_MB).describe(`\
The maximum number of bytes to return in the response. This value is capped by the server's configured maxBytesPerQuery and cannot be exceeded. \
Note to LLM: If the entire aggregation result is required, use the "export" tool instead of increasing this limit.\
`),
    };
    static operationType: OperationType = "read";

    protected async execute(
        { database, collection, pipeline, responseBytesLimit }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        let aggregationCursor: AggregationCursor | undefined = undefined;
        try {
            const provider = await this.ensureConnected();
            await this.assertOnlyUsesPermittedStages(pipeline);
            if (await this.session.isSearchSupported()) {
                assertVectorSearchFilterFieldsAreIndexed({
                    searchIndexes: (await provider.getSearchIndexes(database, collection)) as SearchIndex[],
                    pipeline,
                    logger: this.session.logger,
                });
            }

            // Check if aggregate operation uses an index if enabled
            if (this.config.indexCheck) {
                const [usesVectorSearchIndex, indexName] = await this.isVectorSearchIndexUsed({
                    database,
                    collection,
                    pipeline,
                });
                switch (usesVectorSearchIndex) {
                    case "not-vector-search-query":
                        await checkIndexUsage({
                            database,
                            collection,
                            operation: "aggregate",
                            explainCallback: async () => {
                                return provider
                                    .aggregate(
                                        database,
                                        collection,
                                        pipeline,
                                        {
                                            // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                                            signal,
                                        },
                                        { writeConcern: undefined }
                                    )
                                    .explain("queryPlanner");
                            },
                            logger: this.session.logger,
                        });
                        break;
                    case "non-existent-index":
                        throw new MongoDBError(
                            ErrorCodes.AtlasVectorSearchIndexNotFound,
                            `Could not find an index with name "${indexName}" in namespace "${database}.${collection}".`
                        );
                    case "valid-index":
                    // nothing to do, everything is correct so ready to run the query
                }
            }

            pipeline = await this.replaceRawValuesWithEmbeddingsIfNecessary({
                database,
                collection,
                pipeline,
            });

            let successMessage: string;
            let documents: unknown[];
            if (pipeline.some((stage) => this.isWriteStage(stage))) {
                // This is a write pipeline, so special-case it and don't attempt to apply limits or caps
                aggregationCursor = provider.aggregate(database, collection, pipeline, {
                    // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                    signal,
                });

                documents = await aggregationCursor.toArray();
                successMessage = "The aggregation pipeline executed successfully.";
            } else {
                const cappedResultsPipeline = [...pipeline];
                if (this.config.maxDocumentsPerQuery > 0) {
                    cappedResultsPipeline.push({ $limit: this.config.maxDocumentsPerQuery });
                }
                aggregationCursor = provider.aggregate(database, collection, cappedResultsPipeline, {
                    // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                    signal,
                });

                const [totalDocuments, cursorResults] = await Promise.all([
                    this.countAggregationResultDocuments({
                        provider,
                        database,
                        collection,
                        pipeline,
                        abortSignal: signal,
                    }),
                    collectCursorUntilMaxBytesLimit({
                        cursor: aggregationCursor,
                        configuredMaxBytesPerQuery: this.config.maxBytesPerQuery,
                        toolResponseBytesLimit: responseBytesLimit,
                        abortSignal: signal,
                    }),
                ]);

                // If the total number of documents that the aggregation would've
                // resulted in would be greater than the configured
                // maxDocumentsPerQuery then we know for sure that the results were
                // capped.
                const aggregationResultsCappedByMaxDocumentsLimit =
                    this.config.maxDocumentsPerQuery > 0 &&
                    !!totalDocuments &&
                    totalDocuments > this.config.maxDocumentsPerQuery;

                documents = cursorResults.documents;
                successMessage = this.generateMessage({
                    aggResultsCount: totalDocuments,
                    documents: cursorResults.documents,
                    appliedLimits: [
                        aggregationResultsCappedByMaxDocumentsLimit ? "config.maxDocumentsPerQuery" : undefined,
                        cursorResults.cappedBy,
                    ].filter((limit): limit is keyof typeof CURSOR_LIMITS_TO_LLM_TEXT => !!limit),
                });
            }

            return {
                content: formatUntrustedData(
                    successMessage,
                    ...(documents.length > 0 ? [EJSON.stringify(documents)] : [])
                ),
            };
        } finally {
            if (aggregationCursor) {
                void this.safeCloseCursor(aggregationCursor);
            }
        }
    }

    private async safeCloseCursor(cursor: AggregationCursor<unknown>): Promise<void> {
        try {
            await cursor.close();
        } catch (error) {
            this.session.logger.warning({
                id: LogId.mongodbCursorCloseError,
                context: "aggregate tool",
                message: `Error when closing the cursor - ${error instanceof Error ? error.message : String(error)}`,
            });
        }
    }

    private async assertOnlyUsesPermittedStages(pipeline: Record<string, unknown>[]): Promise<void> {
        const writeOperations: OperationType[] = ["update", "create", "delete"];
        const isSearchSupported = await this.session.isSearchSupported();

        let writeStageForbiddenError = "";

        if (this.config.readOnly) {
            writeStageForbiddenError = "In readOnly mode you can not run pipelines with $out or $merge stages.";
        } else if (this.config.disabledTools.some((t) => writeOperations.includes(t as OperationType))) {
            writeStageForbiddenError =
                "When 'create', 'update', or 'delete' operations are disabled, you can not run pipelines with $out or $merge stages.";
        }

        for (const stage of pipeline) {
            // This validates that in readOnly mode or "write" operations are disabled, we can't use $out or $merge.
            // This is really important because aggregates are the only "multi-faceted" tool in the MQL, where you
            // can both read and write.
            if (this.isWriteStage(stage) && writeStageForbiddenError) {
                throw new MongoDBError(ErrorCodes.ForbiddenWriteOperation, writeStageForbiddenError);
            }

            // This ensure that you can't use $search if the cluster does not support MongoDB Search
            // either in Atlas or in a local cluster.
            if (this.isSearchStage(stage) && !isSearchSupported) {
                throw new MongoDBError(
                    ErrorCodes.AtlasSearchNotSupported,
                    "Atlas Search is not supported in this cluster."
                );
            }
        }
    }

    private async countAggregationResultDocuments({
        provider,
        database,
        collection,
        pipeline,
        abortSignal,
    }: {
        provider: NodeDriverServiceProvider;
        database: string;
        collection: string;
        pipeline: Document[];
        abortSignal?: AbortSignal;
    }): Promise<number | undefined> {
        const resultsCountAggregation = [...pipeline, { $count: "totalDocuments" }];
        return await operationWithFallback(async (): Promise<number | undefined> => {
            const aggregationResults = await provider
                .aggregate(database, collection, resultsCountAggregation, {
                    // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                    signal: abortSignal,
                })
                .maxTimeMS(AGG_COUNT_MAX_TIME_MS_CAP)
                .toArray();

            const documentWithCount: unknown = aggregationResults.length === 1 ? aggregationResults[0] : undefined;
            const totalDocuments =
                documentWithCount &&
                typeof documentWithCount === "object" &&
                "totalDocuments" in documentWithCount &&
                typeof documentWithCount.totalDocuments === "number"
                    ? documentWithCount.totalDocuments
                    : 0;

            return totalDocuments;
        }, undefined);
    }

    private async replaceRawValuesWithEmbeddingsIfNecessary({
        database,
        collection,
        pipeline,
    }: {
        database: string;
        collection: string;
        pipeline: Document[];
    }): Promise<Document[]> {
        for (const stage of pipeline) {
            if ("$vectorSearch" in stage) {
                const { $vectorSearch: vectorSearchStage } = stage as z.infer<typeof VectorSearchStage>;

                // If the stage is using 'query' field (auto-embed indexes) then
                // it is targeting an `autoEmbed` index. In this case, we don't
                // need to generate embeddings for the query because MongoDB is
                // configured to handle the embeddings generation automatically.
                if ("query" in vectorSearchStage) {
                    continue;
                }

                // If queryVector is already an array, no embedding generation
                // needed.
                if (Array.isArray(vectorSearchStage.queryVector)) {
                    continue;
                }

                // At this point, queryVector must be a string for which we need
                // to generate embeddings.
                if (!vectorSearchStage.queryVector) {
                    throw new MongoDBError(
                        ErrorCodes.AtlasVectorSearchInvalidQuery,
                        "Either 'queryVector' (for classic vector indexes) or 'query' (for auto-embed indexes) must be provided in $vectorSearch. Use the collection-indexes tool to verify which type of index the target field has."
                    );
                }

                if (!vectorSearchStage.embeddingParameters) {
                    throw new MongoDBError(
                        ErrorCodes.AtlasVectorSearchInvalidQuery,
                        "embeddingParameters is mandatory when providing queryVector as a string for classic vector search indexes (type: 'vector'). If the target field has an auto-embed index (type: 'autoEmbed'), use 'query' instead of 'queryVector'. Use the collection-indexes tool to verify the index type."
                    );
                }

                const embeddingParameters = vectorSearchStage.embeddingParameters;
                delete vectorSearchStage.embeddingParameters;

                await this.session.vectorSearchEmbeddingsManager.assertVectorSearchIndexExists({
                    database,
                    collection,
                    path: vectorSearchStage.path,
                });

                const [embeddings] = await this.session.vectorSearchEmbeddingsManager.generateEmbeddings({
                    rawValues: [vectorSearchStage.queryVector],
                    embeddingParameters,
                    inputType: "query",
                });

                if (!embeddings) {
                    throw new MongoDBError(
                        ErrorCodes.AtlasVectorSearchInvalidQuery,
                        "Failed to generate embeddings for the query vector."
                    );
                }

                // $vectorSearch.queryVector can be a BSON.Binary: that it's not either number or an array.
                // It's not exactly valid from the LLM perspective (they can't provide binaries).
                // That's why we overwrite the stage in an untyped way, as what we expose and what LLMs can use is different.
                vectorSearchStage.queryVector = embeddings as string | number[];
            }
        }

        await this.session.vectorSearchEmbeddingsManager.assertFieldsHaveCorrectEmbeddings(
            { database, collection },
            pipeline
        );

        return pipeline;
    }

    private async isVectorSearchIndexUsed({
        database,
        collection,
        pipeline,
    }: {
        database: string;
        collection: string;
        pipeline: Document[];
    }): Promise<["valid-index" | "non-existent-index" | "not-vector-search-query", string?]> {
        // check if the pipeline contains a $vectorSearch stage
        let usesVectorSearch = false;
        let indexName: string = "default";

        for (const stage of pipeline) {
            if ("$vectorSearch" in stage) {
                const { $vectorSearch: vectorSearchStage } = stage as z.infer<typeof VectorSearchStage>;
                usesVectorSearch = true;
                indexName = vectorSearchStage.index;
                break;
            }
        }

        if (!usesVectorSearch) {
            return ["not-vector-search-query"];
        }

        const indexExists = await this.session.vectorSearchEmbeddingsManager.indexExists({
            database,
            collection,
            indexName,
        });

        return [indexExists ? "valid-index" : "non-existent-index", indexName];
    }

    private generateMessage({
        aggResultsCount,
        documents,
        appliedLimits,
    }: {
        aggResultsCount: number | undefined;
        documents: unknown[];
        appliedLimits: (keyof typeof CURSOR_LIMITS_TO_LLM_TEXT)[];
    }): string {
        let message = `The aggregation resulted in ${aggResultsCount === undefined ? "indeterminable number of" : aggResultsCount} documents.`;

        // If we applied a limit or the count is different from the aggregation result count,
        // communicate what is the actual number of returned documents
        if (documents.length !== aggResultsCount || appliedLimits.length) {
            message += ` Returning ${documents.length} documents`;
            if (appliedLimits.length) {
                message += ` while respecting the applied limits of ${appliedLimits
                    .map((limit) => CURSOR_LIMITS_TO_LLM_TEXT[limit])
                    .join(
                        ", "
                    )}. Note to LLM: If the entire query result is required then use "export" tool to export the query results`;
            }

            message += ".";
        }

        return message;
    }

    protected resolveTelemetryMetadata(
        args: ToolArgs<typeof this.argsShape>,
        { result }: { result: CallToolResult }
    ): ConnectionMetadata | AutoEmbeddingsUsageMetadata {
        const [maybeVectorStage] = args.pipeline;
        const usesVectorSearch =
            maybeVectorStage !== null && maybeVectorStage instanceof Object && "$vectorSearch" in maybeVectorStage;
        if (
            usesVectorSearch &&
            "embeddingParameters" in maybeVectorStage["$vectorSearch"] &&
            this.config.voyageApiKey
        ) {
            return {
                ...super.resolveTelemetryMetadata(args, { result }),
                embeddingsGeneratedBy: "mcp",
            };
        }

        if (usesVectorSearch && "query" in maybeVectorStage["$vectorSearch"]) {
            return {
                ...super.resolveTelemetryMetadata(args, { result }),
                embeddingsGeneratedBy: "mongot",
            };
        }

        return super.resolveTelemetryMetadata(args, { result });
    }

    private isSearchStage(stage: Record<string, unknown>): boolean {
        return "$vectorSearch" in stage || "$search" in stage || "$searchMeta" in stage;
    }

    private isWriteStage(stage: Record<string, unknown>): boolean {
        return "$out" in stage || "$merge" in stage;
    }
}
