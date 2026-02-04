import { calculateObjectSize } from "bson";
import type { AggregationCursor, FindCursor } from "mongodb";

export function getResponseBytesLimit(
    toolResponseBytesLimit: number | undefined | null,
    configuredMaxBytesPerQuery: unknown
): {
    cappedBy: "config.maxBytesPerQuery" | "tool.responseBytesLimit" | undefined;
    limit: number;
} {
    const configuredLimit: number = parseInt(String(configuredMaxBytesPerQuery), 10);

    // Setting configured maxBytesPerQuery to negative, zero or nullish is
    // equivalent to disabling the max limit applied on documents
    const configuredLimitIsNotApplicable = Number.isNaN(configuredLimit) || configuredLimit <= 0;

    // It's possible to have tool parameter responseBytesLimit as null or
    // negative values in which case we consider that no limit is to be
    // applied from tool call perspective unless we have a maxBytesPerQuery
    // configured.
    const toolResponseLimitIsNotApplicable = typeof toolResponseBytesLimit !== "number" || toolResponseBytesLimit <= 0;

    if (configuredLimitIsNotApplicable) {
        return {
            cappedBy: toolResponseLimitIsNotApplicable ? undefined : "tool.responseBytesLimit",
            limit: toolResponseLimitIsNotApplicable ? 0 : toolResponseBytesLimit,
        };
    }

    if (toolResponseLimitIsNotApplicable) {
        return { cappedBy: "config.maxBytesPerQuery", limit: configuredLimit };
    }

    return {
        cappedBy: configuredLimit < toolResponseBytesLimit ? "config.maxBytesPerQuery" : "tool.responseBytesLimit",
        limit: Math.min(toolResponseBytesLimit, configuredLimit),
    };
}

/**
 * This function attempts to put a guard rail against accidental memory overflow
 * on the MCP server.
 *
 * The cursor is iterated until we can predict that fetching next doc won't
 * exceed the derived limit on number of bytes for the tool call. The derived
 * limit takes into account the limit provided from the Tool's interface and the
 * configured maxBytesPerQuery for the server.
 */
export async function collectCursorUntilMaxBytesLimit<T = unknown>({
    cursor,
    toolResponseBytesLimit,
    configuredMaxBytesPerQuery,
    abortSignal,
}: {
    cursor: FindCursor<T> | AggregationCursor<T>;
    toolResponseBytesLimit: number | undefined | null;
    configuredMaxBytesPerQuery: unknown;
    abortSignal?: AbortSignal;
}): Promise<{ cappedBy: "config.maxBytesPerQuery" | "tool.responseBytesLimit" | undefined; documents: T[] }> {
    const { limit: maxBytesPerQuery, cappedBy } = getResponseBytesLimit(
        toolResponseBytesLimit,
        configuredMaxBytesPerQuery
    );

    // It's possible to have no limit on the cursor response by setting both the
    // config.maxBytesPerQuery and tool.responseBytesLimit to nullish or
    // negative values.
    if (maxBytesPerQuery <= 0) {
        return {
            cappedBy,
            documents: await cursor.toArray(),
        };
    }

    let wasCapped: boolean = false;
    let totalBytes = 0;
    const bufferedDocuments: T[] = [];
    while (true) {
        if (abortSignal?.aborted) {
            break;
        }

        // If the cursor is empty then there is nothing for us to do anymore.
        const nextDocument = await cursor.tryNext();
        if (!nextDocument) {
            break;
        }

        const nextDocumentSize = calculateObjectSize(nextDocument);
        if (totalBytes + nextDocumentSize >= maxBytesPerQuery) {
            wasCapped = true;
            break;
        }

        totalBytes += nextDocumentSize;
        bufferedDocuments.push(nextDocument);
    }

    return {
        cappedBy: wasCapped ? cappedBy : undefined,
        documents: bufferedDocuments,
    };
}
