import { z } from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import type { FindCursor, SortDirection } from "mongodb";
import { checkIndexUsage } from "../../../helpers/indexCheck.js";
import { EJSON } from "bson";
import { collectCursorUntilMaxBytesLimit } from "../../../helpers/collectCursorUntilMaxBytes.js";
import { operationWithFallback } from "../../../helpers/operationWithFallback.js";
import { ONE_MB, QUERY_COUNT_MAX_TIME_MS_CAP, CURSOR_LIMITS_TO_LLM_TEXT } from "../../../helpers/constants.js";
import { zEJSON } from "../../args.js";
import { LogId } from "../../../common/logger.js";

export const FindArgs = {
    filter: zEJSON()
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
    public description = "Run a find query against a MongoDB collection";
    public argsShape = {
        ...DbOperationArgs,
        ...FindArgs,
        responseBytesLimit: z.number().optional().default(ONE_MB).describe(`\
The maximum number of bytes to return in the response. This value is capped by the server's configured maxBytesPerQuery and cannot be exceeded. \
Note to LLM: If the entire query result is required, use the "export" tool instead of increasing this limit.\
`),
    };
    static operationType: OperationType = "read";

    protected async execute(
        { database, collection, filter, projection, limit, sort, responseBytesLimit }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        let findCursor: FindCursor<unknown> | undefined = undefined;
        try {
            const provider = await this.ensureConnected();

            // Check if find operation uses an index if enabled
            if (this.config.indexCheck) {
                await checkIndexUsage({
                    database,
                    collection,
                    operation: "find",
                    explainCallback: async () => {
                        return provider
                            .find(database, collection, filter, {
                                projection,
                                limit,
                                sort,
                                // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                                signal,
                            })
                            .explain("queryPlanner");
                    },
                    logger: this.session.logger,
                });
            }

            const limitOnFindCursor = this.getLimitForFindCursor(limit);

            findCursor = provider.find(database, collection, filter, {
                projection,
                limit: limitOnFindCursor.limit,
                sort,
                // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                signal,
            });

            const [queryResultsCount, cursorResults] = await Promise.all([
                operationWithFallback(
                    () =>
                        provider.countDocuments(database, collection, filter, {
                            // We should be counting documents that the original
                            // query would have yielded which is why we don't
                            // use `limitOnFindCursor` calculated above, only
                            // the limit provided to the tool.
                            limit,
                            maxTimeMS: QUERY_COUNT_MAX_TIME_MS_CAP,
                            // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                            signal,
                        }),
                    undefined
                ),
                collectCursorUntilMaxBytesLimit({
                    cursor: findCursor,
                    configuredMaxBytesPerQuery: this.config.maxBytesPerQuery,
                    toolResponseBytesLimit: responseBytesLimit,
                    abortSignal: signal,
                }),
            ]);

            return {
                content: formatUntrustedData(
                    this.generateMessage({
                        collection,
                        queryResultsCount,
                        documents: cursorResults.documents,
                        appliedLimits: [limitOnFindCursor.cappedBy, cursorResults.cappedBy].filter((limit) => !!limit),
                    }),
                    ...(cursorResults.documents.length > 0 ? [EJSON.stringify(cursorResults.documents)] : [])
                ),
            };
        } finally {
            if (findCursor) {
                void this.safeCloseCursor(findCursor);
            }
        }
    }

    private async safeCloseCursor(cursor: FindCursor<unknown>): Promise<void> {
        try {
            await cursor.close();
        } catch (error) {
            this.session.logger.warning({
                id: LogId.mongodbCursorCloseError,
                context: "find tool",
                message: `Error when closing the cursor - ${error instanceof Error ? error.message : String(error)}`,
            });
        }
    }

    private generateMessage({
        collection,
        queryResultsCount,
        documents,
        appliedLimits,
    }: {
        collection: string;
        queryResultsCount: number | undefined;
        documents: unknown[];
        appliedLimits: (keyof typeof CURSOR_LIMITS_TO_LLM_TEXT)[];
    }): string {
        const appliedLimitsText = appliedLimits.length
            ? `\
while respecting the applied limits of ${appliedLimits.map((limit) => CURSOR_LIMITS_TO_LLM_TEXT[limit]).join(", ")}. \
Note to LLM: If the entire query result is required then use "export" tool to export the query results.\
`
            : "";

        return `\
Query on collection "${collection}" resulted in ${queryResultsCount === undefined ? "indeterminable number of" : queryResultsCount} documents. \
Returning ${documents.length} documents${appliedLimitsText ? ` ${appliedLimitsText}` : "."}\
`;
    }

    private getLimitForFindCursor(providedLimit: number | undefined | null): {
        cappedBy: "config.maxDocumentsPerQuery" | undefined;
        limit: number | undefined;
    } {
        const configuredLimit: number = parseInt(String(this.config.maxDocumentsPerQuery), 10);

        // Setting configured maxDocumentsPerQuery to negative, zero or nullish
        // is equivalent to disabling the max limit applied on documents
        const configuredLimitIsNotApplicable = Number.isNaN(configuredLimit) || configuredLimit <= 0;
        if (configuredLimitIsNotApplicable) {
            return { cappedBy: undefined, limit: providedLimit ?? undefined };
        }

        const providedLimitIsNotApplicable = providedLimit === null || providedLimit === undefined;
        if (providedLimitIsNotApplicable) {
            return { cappedBy: "config.maxDocumentsPerQuery", limit: configuredLimit };
        }

        return {
            cappedBy: configuredLimit < providedLimit ? "config.maxDocumentsPerQuery" : undefined,
            limit: Math.min(providedLimit, configuredLimit),
        };
    }
}
