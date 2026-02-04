// Based on -

import type z from "zod";
import { ErrorCodes, MongoDBError } from "../common/errors.js";
import type { VectorSearchStage } from "../tools/mongodb/mongodbSchemas.js";
import { type CompositeLogger, LogId } from "../common/logger.js";

// https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#mongodb-vector-search-pre-filter
const ALLOWED_LOGICAL_OPERATORS = ["$not", "$nor", "$and", "$or"];

export type SearchIndex = VectorSearchIndex | AtlasSearchIndex;

type VectorSearchIndex = {
    name: string;
    latestDefinition: {
        fields: Array<
            | {
                  type: "vector";
              }
            | {
                  type: "filter";
                  path: string;
              }
        >;
    };
    type: "vectorSearch";
};

type AtlasSearchIndex = {
    name: string;
    latestDefinition: unknown;
    type: "search";
};

export function assertVectorSearchFilterFieldsAreIndexed({
    searchIndexes,
    pipeline,
    logger,
}: {
    searchIndexes: SearchIndex[];
    pipeline: Record<string, unknown>[];
    logger: CompositeLogger;
}): void {
    const searchIndexesWithFilterFields = searchIndexes
        // Ensure we only process vector search indexes and not lexical search ones
        .filter((index) => index.type === "vectorSearch")
        .reduce<Record<string, string[]>>((indexFieldMap, searchIndex) => {
            const filterFields = searchIndex.latestDefinition.fields
                .map<string | undefined>((field) => {
                    return field.type === "filter" ? field.path : undefined;
                })
                .filter((filterField) => filterField !== undefined);

            indexFieldMap[searchIndex.name] = filterFields;
            return indexFieldMap;
        }, {});
    for (const stage of pipeline) {
        if ("$vectorSearch" in stage) {
            const { $vectorSearch: vectorSearchStage } = stage as z.infer<typeof VectorSearchStage>;
            const allowedFilterFields = searchIndexesWithFilterFields[vectorSearchStage.index];
            if (!allowedFilterFields) {
                logger.warning({
                    id: LogId.toolValidationError,
                    context: "aggregate tool",
                    message: `Could not assert if filter fields are indexed - No filter fields found for index ${vectorSearchStage.index}`,
                });
                return;
            }

            const filterFieldsInStage = collectFieldsFromVectorSearchFilter(vectorSearchStage.filter);
            const filterFieldsNotIndexed = filterFieldsInStage.filter((field) => !allowedFilterFields.includes(field));
            if (filterFieldsNotIndexed.length) {
                throw new MongoDBError(
                    ErrorCodes.AtlasVectorSearchInvalidQuery,
                    `Vector search stage contains filter on fields that are not indexed by index ${vectorSearchStage.index} - ${filterFieldsNotIndexed.join(", ")}`
                );
            }
        }
    }
}

export function collectFieldsFromVectorSearchFilter(filter: unknown): string[] {
    if (!filter || typeof filter !== "object" || !Object.keys(filter).length) {
        return [];
    }

    const collectedFields = Object.entries(filter).reduce<string[]>((collectedFields, [maybeField, fieldMQL]) => {
        if (ALLOWED_LOGICAL_OPERATORS.includes(maybeField) && Array.isArray(fieldMQL)) {
            return fieldMQL.flatMap((mql) => collectFieldsFromVectorSearchFilter(mql));
        }

        if (!ALLOWED_LOGICAL_OPERATORS.includes(maybeField)) {
            collectedFields.push(maybeField);
        }
        return collectedFields;
    }, []);

    return Array.from(new Set(collectedFields));
}
