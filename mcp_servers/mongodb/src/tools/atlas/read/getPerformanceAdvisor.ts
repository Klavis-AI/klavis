import { z } from "zod";
import { AtlasToolBase } from "../atlasTool.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { OperationType, ToolArgs } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import {
    getSuggestedIndexes,
    getDropIndexSuggestions,
    getSchemaAdvice,
    getSlowQueries,
    DEFAULT_SLOW_QUERY_LOGS_LIMIT,
    SUGGESTED_INDEXES_COPY,
    SLOW_QUERY_LOGS_COPY,
} from "../../../common/atlas/performanceAdvisorUtils.js";
import { AtlasArgs } from "../../args.js";
import type { PerfAdvisorToolMetadata } from "../../../telemetry/types.js";

const PerformanceAdvisorOperationType = z.enum([
    "suggestedIndexes",
    "dropIndexSuggestions",
    "slowQueryLogs",
    "schemaSuggestions",
]);

export class GetPerformanceAdvisorTool extends AtlasToolBase {
    public name = "atlas-get-performance-advisor";
    public description = `Get MongoDB Atlas performance advisor recommendations and suggestions, which includes the operations: suggested indexes, drop index suggestions, schema suggestions, and a sample of the most recent (max ${DEFAULT_SLOW_QUERY_LOGS_LIMIT}) slow query logs`;
    static operationType: OperationType = "read";
    public argsShape = {
        projectId: AtlasArgs.projectId().describe(
            "Atlas project ID to get performance advisor recommendations. The project ID is a hexadecimal identifier of 24 characters. If the user has only specified the name, use the `atlas-list-projects` tool to retrieve the user's projects with their ids."
        ),
        clusterName: AtlasArgs.clusterName().describe("Atlas cluster name to get performance advisor recommendations"),
        operations: z
            .array(PerformanceAdvisorOperationType)
            .default(PerformanceAdvisorOperationType.options)
            .describe("Operations to get performance advisor recommendations"),
        since: z
            .string()
            .datetime()
            .describe(
                "Date to get slow query logs since. Must be a string in ISO 8601 format. Only relevant for the slowQueryLogs operation."
            )
            .optional(),
        namespaces: z
            .array(z.string())
            .describe("Namespaces to get slow query logs. Only relevant for the slowQueryLogs operation.")
            .optional(),
    };

    protected async execute({
        projectId,
        clusterName,
        operations,
        since,
        namespaces,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        try {
            const [suggestedIndexesResult, dropIndexSuggestionsResult, slowQueryLogsResult, schemaSuggestionsResult] =
                await Promise.allSettled([
                    operations.includes("suggestedIndexes")
                        ? getSuggestedIndexes(this.apiClient, projectId, clusterName)
                        : Promise.resolve(undefined),
                    operations.includes("dropIndexSuggestions")
                        ? getDropIndexSuggestions(this.apiClient, projectId, clusterName)
                        : Promise.resolve(undefined),
                    operations.includes("slowQueryLogs")
                        ? getSlowQueries(
                              this.apiClient,
                              projectId,
                              clusterName,
                              since ? new Date(since) : undefined,
                              namespaces
                          )
                        : Promise.resolve(undefined),
                    operations.includes("schemaSuggestions")
                        ? getSchemaAdvice(this.apiClient, projectId, clusterName)
                        : Promise.resolve(undefined),
                ]);

            const hasSuggestedIndexes =
                suggestedIndexesResult.status === "fulfilled" &&
                suggestedIndexesResult.value?.suggestedIndexes &&
                suggestedIndexesResult.value.suggestedIndexes.length > 0;
            const hasDropIndexSuggestions =
                dropIndexSuggestionsResult.status === "fulfilled" &&
                dropIndexSuggestionsResult.value?.hiddenIndexes &&
                dropIndexSuggestionsResult.value?.redundantIndexes &&
                dropIndexSuggestionsResult.value?.unusedIndexes &&
                (dropIndexSuggestionsResult.value.hiddenIndexes.length > 0 ||
                    dropIndexSuggestionsResult.value.redundantIndexes.length > 0 ||
                    dropIndexSuggestionsResult.value.unusedIndexes.length > 0);
            const hasSlowQueryLogs =
                slowQueryLogsResult.status === "fulfilled" &&
                slowQueryLogsResult.value?.slowQueryLogs &&
                slowQueryLogsResult.value.slowQueryLogs.length > 0;
            const hasSchemaSuggestions =
                schemaSuggestionsResult.status === "fulfilled" &&
                schemaSuggestionsResult.value?.recommendations &&
                schemaSuggestionsResult.value.recommendations.length > 0;

            // Inserts the performance advisor data with the relevant section header if it exists
            const performanceAdvisorData = [
                `## Suggested Indexes\n${
                    hasSuggestedIndexes
                        ? `${SUGGESTED_INDEXES_COPY}\n${JSON.stringify(suggestedIndexesResult.value?.suggestedIndexes)}`
                        : "No suggested indexes found."
                }`,
                `## Drop Index Suggestions\n${hasDropIndexSuggestions ? JSON.stringify(dropIndexSuggestionsResult.value) : "No drop index suggestions found."}`,
                `## Slow Query Logs\n${hasSlowQueryLogs ? `${SLOW_QUERY_LOGS_COPY}\n${JSON.stringify(slowQueryLogsResult.value?.slowQueryLogs)}` : "No slow query logs found."}`,
                `## Schema Suggestions\n${hasSchemaSuggestions ? JSON.stringify(schemaSuggestionsResult.value?.recommendations) : "No schema suggestions found."}`,
            ];

            if (performanceAdvisorData.length === 0) {
                return {
                    content: [{ type: "text", text: "No performance advisor recommendations found." }],
                };
            }

            return {
                content: formatUntrustedData("Performance advisor data", performanceAdvisorData.join("\n\n")),
            };
        } catch (error) {
            return {
                content: [
                    {
                        type: "text",
                        text: `Error retrieving performance advisor data: ${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
            };
        }
    }

    protected override resolveTelemetryMetadata(
        args: ToolArgs<typeof this.argsShape>,
        { result }: { result: CallToolResult }
    ): PerfAdvisorToolMetadata {
        return {
            ...super.resolveTelemetryMetadata(args, { result }),
            operations: args.operations,
        };
    }
}
