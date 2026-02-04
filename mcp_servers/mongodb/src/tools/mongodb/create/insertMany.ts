import { z } from "zod";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { type ToolArgs, type OperationType, formatUntrustedData } from "../../tool.js";
import { zEJSON } from "../../args.js";
import { type Document } from "bson";
import { zSupportedEmbeddingParameters } from "../mongodbSchemas.js";
import { ErrorCodes, MongoDBError } from "../../../common/errors.js";
import type { ConnectionMetadata, AutoEmbeddingsUsageMetadata } from "../../../telemetry/types.js";
import { setFieldPath } from "../../../helpers/manageNestedFieldPaths.js";

const zSupportedEmbeddingParametersWithInput = zSupportedEmbeddingParameters.extend({
    input: z.array(z.object({}).passthrough()).describe(`\
Array of objects with field paths covered by vector search index field definitions as keys (in dot notation) and the raw text values as values for generating embeddings. \
The index of each object corresponds to the index of the document in the documents array. \
Note to LLM: Ensure that the keys in the the input object are the field paths where vector embeddings are supposed to be stored and are covered by vector search index field definitions (type: 'vector').\
`),
});

const commonArgs = {
    ...DbOperationArgs,
    documents: z
        .array(zEJSON().describe("An individual MongoDB document"))
        .describe(
            "The array of documents to insert, matching the syntax of the document argument of db.collection.insertMany()."
        ),
} as const;

export class InsertManyTool extends MongoDBToolBase {
    public name = "insert-many";
    public description =
        "Insert an array of documents into a MongoDB collection.";
    public argsShape = this.isFeatureEnabled("search")
        ? {
              ...commonArgs,
              embeddingParameters: zSupportedEmbeddingParametersWithInput.optional().describe(
                  `\
The embedding model and its parameters to use for generating embeddings for fields indexed with a vector search index and field definition of type 'vector'. \
Note to LLM: Use the collection-indexes tool to verify which fields have which type of vector search index field definition before deciding whether to provide this parameter. \
DO NOT provide this parameter if the field is covered by a vector index field definition of type 'autoEmbed' or not covered at all. \
If unsure which embedding model to use, ask the user before providing one.\
`
              ),
          }
        : commonArgs;
    static operationType: OperationType = "create";

    protected async execute({
        database,
        collection,
        documents,
        ...conditionalArgs
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        let embeddingParameters: z.infer<typeof zSupportedEmbeddingParametersWithInput> | undefined;
        if ("embeddingParameters" in conditionalArgs) {
            embeddingParameters = conditionalArgs.embeddingParameters;
        }

        // Process documents to replace raw string values with generated embeddings
        documents = await this.replaceRawValuesWithEmbeddingsIfNecessary({
            database,
            collection,
            documents,
            embeddingParameters,
        });

        await this.session.vectorSearchEmbeddingsManager.assertFieldsHaveCorrectEmbeddings(
            { database, collection },
            documents
        );

        const result = await provider.insertMany(database, collection, documents);
        const content = formatUntrustedData(
            "Documents were inserted successfully.",
            `Inserted \`${result.insertedCount}\` document(s) into ${database}.${collection}.`,
            `Inserted IDs: ${Object.values(result.insertedIds).join(", ")}`
        );
        return {
            content,
        };
    }

    private async replaceRawValuesWithEmbeddingsIfNecessary({
        database,
        collection,
        documents,
        embeddingParameters,
    }: {
        database: string;
        collection: string;
        documents: Document[];
        embeddingParameters?: z.infer<typeof zSupportedEmbeddingParametersWithInput>;
    }): Promise<Document[]> {
        // If no embedding parameters or no input specified, return documents as-is
        if (!embeddingParameters?.input || embeddingParameters.input.length === 0) {
            return documents;
        }

        // Get vector search indexes for the collection.
        // Note: embeddingsForNamespace() only returns fields that require manual embedding generation,
        // excluding fields with auto-embedding indexes where MongoDB generates embeddings automatically.
        const vectorIndexes = await this.session.vectorSearchEmbeddingsManager.embeddingsForNamespace({
            database,
            collection,
        });

        // Ensure for inputted fields, the vector search index exists.
        for (const input of embeddingParameters.input) {
            for (const fieldPath of Object.keys(input)) {
                if (!vectorIndexes.some((index) => index.path === fieldPath)) {
                    throw new MongoDBError(
                        ErrorCodes.AtlasVectorSearchInvalidQuery,
                        `Field '${fieldPath}' cannot be used with embeddingParameters because it does not have a classic vector search index (type: 'vector') configured for manual embedding generation in collection ${database}.${collection}. This field either has no vector search index, or it has an auto-embed index (type: 'autoEmbed') where MongoDB automatically generates embeddings at indexing time. Use the collection-indexes tool to verify the index configuration for this field. If it has an auto-embed index, remove it from embeddingParameters and provide the raw text directly in the document instead.`
                    );
                }
            }
        }

        // We make one call to generate embeddings for all documents at once to avoid making too many API calls.
        const flattenedEmbeddingsInput = embeddingParameters.input.flatMap((documentInput, index) =>
            Object.entries(documentInput).map(([fieldPath, rawTextValue]) => ({
                fieldPath,
                rawTextValue,
                documentIndex: index,
            }))
        );

        const generatedEmbeddings = await this.session.vectorSearchEmbeddingsManager.generateEmbeddings({
            rawValues: flattenedEmbeddingsInput.map(({ rawTextValue }) => rawTextValue) as string[],
            embeddingParameters,
            inputType: "document",
        });

        const processedDocuments: Document[] = [...documents];

        for (const [index, { fieldPath, documentIndex }] of flattenedEmbeddingsInput.entries()) {
            if (!processedDocuments[documentIndex]) {
                throw new MongoDBError(ErrorCodes.Unexpected, `Document at index ${documentIndex} does not exist.`);
            }
            setFieldPath(processedDocuments[documentIndex], fieldPath, generatedEmbeddings[index]);
        }

        return processedDocuments;
    }

    protected resolveTelemetryMetadata(
        args: ToolArgs<typeof this.argsShape>,
        { result }: { result: CallToolResult }
    ): ConnectionMetadata | AutoEmbeddingsUsageMetadata {
        if ("embeddingParameters" in args && this.config.voyageApiKey) {
            return {
                ...super.resolveTelemetryMetadata(args, { result }),
                embeddingsGeneratedBy: "mcp",
            };
        } else {
            return super.resolveTelemetryMetadata(args, { result });
        }
    }
}
