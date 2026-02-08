import { Document } from "mongodb";
import { NodeDriverServiceProvider } from "@mongosh/service-provider-node-driver";
import { ErrorCodes, MongoDBError } from "../common/errors.js";

/**
 * Check if the query plan uses an index
 * @param explainResult The result of the explain query
 * @returns true if an index is used, false if it's a full collection scan
 */
export function usesIndex(explainResult: Document): boolean {
    const queryPlanner = explainResult?.queryPlanner as Document | undefined;
    const winningPlan = queryPlanner?.winningPlan as Document | undefined;
    const stage = winningPlan?.stage as string | undefined;
    const inputStage = winningPlan?.inputStage as Document | undefined;

    // Check for index scan stages (including MongoDB 8.0+ stages)
    const indexScanStages = [
        "IXSCAN",
        "COUNT_SCAN",
        "EXPRESS_IXSCAN",
        "EXPRESS_CLUSTERED_IXSCAN",
        "EXPRESS_UPDATE",
        "EXPRESS_DELETE",
        "IDHACK",
    ];

    if (stage && indexScanStages.includes(stage)) {
        return true;
    }

    if (inputStage && inputStage.stage && indexScanStages.includes(inputStage.stage as string)) {
        return true;
    }

    // Recursively check deeper stages
    if (inputStage && inputStage.inputStage) {
        return usesIndex({ queryPlanner: { winningPlan: inputStage } });
    }

    if (stage === "COLLSCAN") {
        return false;
    }

    // Default to false (conservative approach)
    return false;
}

/**
 * Generate an error message for index check failure
 */
export function getIndexCheckErrorMessage(database: string, collection: string, operation: string): string {
    return `Index check failed: The ${operation} operation on "${database}.${collection}" performs a collection scan (COLLSCAN) instead of using an index. Consider adding an index for better performance. Use 'explain' tool for query plan analysis or 'collection-indexes' to view existing indexes. To disable this check, set MDB_MCP_INDEX_CHECK to false.`;
}

/**
 * Generic function to perform index usage check
 */
export async function checkIndexUsage(
    provider: NodeDriverServiceProvider,
    database: string,
    collection: string,
    operation: string,
    explainCallback: () => Promise<Document>
): Promise<void> {
    try {
        const explainResult = await explainCallback();

        if (!usesIndex(explainResult)) {
            throw new MongoDBError(
                ErrorCodes.ForbiddenCollscan,
                getIndexCheckErrorMessage(database, collection, operation)
            );
        }
    } catch (error) {
        if (error instanceof MongoDBError && error.code === ErrorCodes.ForbiddenCollscan) {
            throw error;
        }

        // If explain itself fails, log but do not prevent query execution
        // This avoids blocking normal queries in special cases (e.g., permission issues)
        console.warn(`Index check failed to execute explain for ${operation} on ${database}.${collection}:`, error);
    }
}
