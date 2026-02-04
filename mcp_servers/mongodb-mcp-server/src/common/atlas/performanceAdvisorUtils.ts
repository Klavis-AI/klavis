import { LogId } from "../logger.js";
import type { ApiClient } from "./apiClient.js";
import { getProcessIdsFromCluster } from "./cluster.js";
import type { components } from "./openapi.js";

export type SuggestedIndex = components["schemas"]["PerformanceAdvisorIndex"];
export type DropIndexSuggestion = components["schemas"]["DropIndexSuggestionsIndex"];
export type SlowQueryLog = components["schemas"]["PerformanceAdvisorSlowQuery"];

export const DEFAULT_SLOW_QUERY_LOGS_LIMIT = 50;

export const SUGGESTED_INDEXES_COPY = `Note: The "Weight" field is measured in bytes, and represents the estimated number of bytes saved in disk reads per executed read query that would be saved by implementing an index suggestion. Please convert this to MB or GB for easier readability.`;
export const SLOW_QUERY_LOGS_COPY = `Please notify the user that the MCP server tool limits slow query logs to the most recent ${DEFAULT_SLOW_QUERY_LOGS_LIMIT} slow query logs. This is a limitation of the MCP server tool only. More slow query logs and performance suggestions can be seen in the Atlas UI. Please give to the user the following docs about the performance advisor: https://www.mongodb.com/docs/atlas/performance-advisor/.`;

interface SuggestedIndexesResponse {
    content: components["schemas"]["PerformanceAdvisorResponse"];
}
interface DropIndexesResponse {
    content: components["schemas"]["DropIndexSuggestionsResponse"];
}
interface SchemaAdviceResponse {
    content: components["schemas"]["SchemaAdvisorResponse"];
}
export type SchemaRecommendation = components["schemas"]["SchemaAdvisorItemRecommendation"];

export async function getSuggestedIndexes(
    apiClient: ApiClient,
    projectId: string,
    clusterName: string
): Promise<{ suggestedIndexes: Array<SuggestedIndex> }> {
    try {
        const response = await apiClient.listClusterSuggestedIndexes({
            params: {
                path: {
                    groupId: projectId,
                    clusterName,
                },
            },
        });
        return {
            suggestedIndexes: (response as SuggestedIndexesResponse).content.suggestedIndexes ?? [],
        };
    } catch (err) {
        apiClient.logger.debug({
            id: LogId.atlasPaSuggestedIndexesFailure,
            context: "performanceAdvisorUtils",
            message: `Failed to list suggested indexes: ${err instanceof Error ? err.message : String(err)}`,
        });
        throw new Error(`Failed to list suggested indexes: ${err instanceof Error ? err.message : String(err)}`);
    }
}

export async function getDropIndexSuggestions(
    apiClient: ApiClient,
    projectId: string,
    clusterName: string
): Promise<{
    hiddenIndexes: Array<DropIndexSuggestion>;
    redundantIndexes: Array<DropIndexSuggestion>;
    unusedIndexes: Array<DropIndexSuggestion>;
}> {
    try {
        const response = await apiClient.listDropIndexSuggestions({
            params: {
                path: {
                    groupId: projectId,
                    clusterName,
                },
            },
        });
        return {
            hiddenIndexes: (response as DropIndexesResponse).content.hiddenIndexes ?? [],
            redundantIndexes: (response as DropIndexesResponse).content.redundantIndexes ?? [],
            unusedIndexes: (response as DropIndexesResponse).content.unusedIndexes ?? [],
        };
    } catch (err) {
        apiClient.logger.debug({
            id: LogId.atlasPaDropIndexSuggestionsFailure,
            context: "performanceAdvisorUtils",
            message: `Failed to list drop index suggestions: ${err instanceof Error ? err.message : String(err)}`,
        });
        throw new Error(`Failed to list drop index suggestions: ${err instanceof Error ? err.message : String(err)}`);
    }
}

export async function getSchemaAdvice(
    apiClient: ApiClient,
    projectId: string,
    clusterName: string
): Promise<{ recommendations: Array<SchemaRecommendation> }> {
    try {
        const response = await apiClient.listSchemaAdvice({
            params: {
                path: {
                    groupId: projectId,
                    clusterName,
                },
            },
        });
        return { recommendations: (response as SchemaAdviceResponse).content.recommendations ?? [] };
    } catch (err) {
        apiClient.logger.debug({
            id: LogId.atlasPaSchemaAdviceFailure,
            context: "performanceAdvisorUtils",
            message: `Failed to list schema advice: ${err instanceof Error ? err.message : String(err)}`,
        });
        throw new Error(`Failed to list schema advice: ${err instanceof Error ? err.message : String(err)}`);
    }
}

export async function getSlowQueries(
    apiClient: ApiClient,
    projectId: string,
    clusterName: string,
    since?: Date,
    namespaces?: Array<string>
): Promise<{ slowQueryLogs: Array<SlowQueryLog> }> {
    try {
        const processIds = await getProcessIdsFromCluster(apiClient, projectId, clusterName);

        if (processIds.length === 0) {
            return { slowQueryLogs: [] };
        }

        const slowQueryPromises = processIds.map((processId) =>
            apiClient.listSlowQueryLogs({
                params: {
                    path: {
                        groupId: projectId,
                        processId,
                    },
                    query: {
                        ...(since && { since: since.getTime() }),
                        ...(namespaces && { namespaces: namespaces }),
                        nLogs: DEFAULT_SLOW_QUERY_LOGS_LIMIT,
                    },
                },
            })
        );

        const responses = await Promise.allSettled(slowQueryPromises);

        const allSlowQueryLogs = responses.reduce((acc, response) => {
            return acc.concat(response.status === "fulfilled" ? (response.value.slowQueries ?? []) : []);
        }, [] as Array<SlowQueryLog>);

        return { slowQueryLogs: allSlowQueryLogs };
    } catch (err) {
        apiClient.logger.debug({
            id: LogId.atlasPaSlowQueryLogsFailure,
            context: "performanceAdvisorUtils",
            message: `Failed to list slow query logs: ${err instanceof Error ? err.message : String(err)}`,
        });
        throw new Error(`Failed to list slow query logs: ${err instanceof Error ? err.message : String(err)}`);
    }
}
