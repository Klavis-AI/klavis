import { z as z4 } from "zod/v4";
import {
    type ConfigFieldMeta,
    commaSeparatedToArray,
    getExportsPath,
    getLogPath,
    oneWayOverride,
    onlyLowerThanBaseValueOverride,
    onlySubsetOfBaseValueOverride,
    parseBoolean,
} from "./configUtils.js";
import { previewFeatureValues, similarityValues } from "../schemas.js";
import { CliOptionsSchema as MongoshCliOptionsSchema } from "@mongosh/arg-parser/arg-parser";
import { TRANSPORT_PAYLOAD_LIMITS } from "../../transports/constants.js";

export const configRegistry = z4.registry<ConfigFieldMeta>();

const ServerConfigSchema = z4.object({
    apiBaseUrl: z4
        .string()
        .default("https://cloud.mongodb.com/")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    apiClientId: z4
        .string()
        .optional()
        .describe("Atlas API client ID for authentication. Required for running Atlas tools.")
        .register(configRegistry, { isSecret: true, overrideBehavior: "not-allowed" }),
    apiClientSecret: z4
        .string()
        .optional()
        .describe("Atlas API client secret for authentication. Required for running Atlas tools.")
        .register(configRegistry, { isSecret: true, overrideBehavior: "not-allowed" }),
    connectionString: z4
        .string()
        .optional()
        .describe(
            "MongoDB connection string for direct database connections. Optional, if not set, you'll need to call the connect tool before interacting with MongoDB data."
        )
        .register(configRegistry, { isSecret: true, overrideBehavior: "not-allowed" }),
    loggers: z4
        .preprocess(
            (val: string | string[] | undefined) => commaSeparatedToArray(val),
            z4.array(z4.enum(["stderr", "disk", "mcp"]))
        )
        .check(
            z4.minLength(1, "Cannot be an empty array"),
            z4.refine((val) => new Set(val).size === val.length, {
                message: "Duplicate loggers found in config",
            })
        )
        .default(["disk", "mcp"])
        .describe("An array of logger types.")
        .register(configRegistry, {
            defaultValueDescription: '`"disk,mcp"` see below*',
            overrideBehavior: "not-allowed",
        }),
    logPath: z4
        .string()
        .default(getLogPath())
        .describe("Folder to store logs.")
        .register(configRegistry, { defaultValueDescription: "see below*", overrideBehavior: "not-allowed" }),
    disabledTools: z4
        .preprocess((val: string | string[] | undefined) => commaSeparatedToArray(val), z4.array(z4.string()))
        .default([])
        .describe("An array of tool names, operation types, and/or categories of tools that will be disabled.")
        .register(configRegistry, { overrideBehavior: "merge" }),
    confirmationRequiredTools: z4
        .preprocess((val: string | string[] | undefined) => commaSeparatedToArray(val), z4.array(z4.string()))
        .default([
            "atlas-create-access-list",
            "atlas-create-db-user",
            "drop-database",
            "drop-collection",
            "delete-many",
            "drop-index",
        ])
        .describe(
            "An array of tool names that require user confirmation before execution. Requires the client to support elicitation."
        )
        .register(configRegistry, { overrideBehavior: "merge" }),
    readOnly: z4
        .preprocess(parseBoolean, z4.boolean())
        .default(false)
        .describe(
            "When set to true, only allows read, connect, and metadata operation types, disabling create/update/delete operations."
        )
        .register(configRegistry, {
            overrideBehavior: oneWayOverride(true),
        }),
    indexCheck: z4
        .preprocess(parseBoolean, z4.boolean())
        .default(false)
        .describe(
            "When set to true, enforces that query operations must use an index, rejecting queries that perform a collection scan."
        )
        .register(configRegistry, {
            overrideBehavior: oneWayOverride(true),
        }),
    telemetry: z4
        .enum(["enabled", "disabled"])
        .default("enabled")
        .describe("When set to disabled, disables telemetry collection.")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    transport: z4
        .enum(["stdio", "http"])
        .default("stdio")
        .describe("Either 'stdio' or 'http'.")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    httpPort: z4.coerce
        .number()
        .int()
        .min(0, "Invalid httpPort: must be at least 0")
        .max(65535, "Invalid httpPort: must be at most 65535")
        .default(3000)
        .describe("Port number for the HTTP server (only used when transport is 'http'). Use 0 for a random port.")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    httpHost: z4
        .string()
        .default("127.0.0.1")
        .describe("Host address to bind the HTTP server to (only used when transport is 'http').")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    httpHeaders: z4
        .object({})
        .loose()
        .default({})
        .describe(
            "Header that the HTTP server will validate when making requests (only used when transport is 'http')."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    httpBodyLimit: z4.coerce
        .number()
        .int()
        .min(
            TRANSPORT_PAYLOAD_LIMITS.http,
            `Invalid httpBodyLimit: must be at least ${TRANSPORT_PAYLOAD_LIMITS.http} bytes`
        )
        .default(TRANSPORT_PAYLOAD_LIMITS.http)
        .describe(
            "Maximum size of the HTTP request body in bytes (only used when transport is 'http'). This value is passed as the optional limit parameter to the Express.js json() middleware."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    idleTimeoutMs: z4.coerce
        .number()
        .default(600_000)
        .describe("Idle timeout for a client to disconnect (only applies to http transport).")
        .register(configRegistry, { overrideBehavior: onlyLowerThanBaseValueOverride() }),
    notificationTimeoutMs: z4.coerce
        .number()
        .default(540_000)
        .describe("Notification timeout for a client to be aware of disconnect (only applies to http transport).")
        .register(configRegistry, { overrideBehavior: onlyLowerThanBaseValueOverride() }),
    maxBytesPerQuery: z4.coerce
        .number()
        .default(16_777_216)
        .describe(
            "The maximum size in bytes for results from a find or aggregate tool call. This serves as an upper bound for the responseBytesLimit parameter in those tools."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    maxDocumentsPerQuery: z4.coerce
        .number()
        .default(100)
        .describe(
            "The maximum number of documents that can be returned by a find or aggregate tool call. For the find tool, the effective limit will be the smaller of this value and the tool's limit parameter."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    exportsPath: z4
        .string()
        .default(getExportsPath())
        .describe("Folder to store exported data files.")
        .register(configRegistry, { defaultValueDescription: "see below*", overrideBehavior: "not-allowed" }),
    exportTimeoutMs: z4.coerce
        .number()
        .default(300_000)
        .describe("Time in milliseconds after which an export is considered expired and eligible for cleanup.")
        .register(configRegistry, { overrideBehavior: onlyLowerThanBaseValueOverride() }),
    exportCleanupIntervalMs: z4.coerce
        .number()
        .default(120_000)
        .describe("Time in milliseconds between export cleanup cycles that remove expired export files.")
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    atlasTemporaryDatabaseUserLifetimeMs: z4.coerce
        .number()
        .default(14_400_000)
        .describe(
            "Time in milliseconds that temporary database users created when connecting to MongoDB Atlas clusters will remain active before being automatically deleted."
        )
        .register(configRegistry, { overrideBehavior: onlyLowerThanBaseValueOverride() }),
    voyageApiKey: z4
        .string()
        .default("")
        .describe(
            "API key for Voyage AI embeddings service (required for vector search operations with text-to-embedding conversion)."
        )
        .register(configRegistry, { isSecret: true, overrideBehavior: "not-allowed" }),
    embeddingsValidation: z4
        .preprocess(parseBoolean, z4.boolean())
        .default(true)
        .describe("When set to false, disables validation of embeddings dimensions.")
        .register(configRegistry, { overrideBehavior: oneWayOverride(true) }),
    vectorSearchDimensions: z4.coerce
        .number()
        .default(1024)
        .describe("Default number of dimensions for vector search embeddings.")
        .register(configRegistry, { overrideBehavior: "override" }),
    vectorSearchSimilarityFunction: z4
        .enum(similarityValues)
        .default("euclidean")
        .describe("Default similarity function for vector search: 'euclidean', 'cosine', or 'dotProduct'.")
        .register(configRegistry, { overrideBehavior: "override" }),
    previewFeatures: z4
        .preprocess(
            (val: string | string[] | undefined) => commaSeparatedToArray(val),
            z4.array(z4.enum(previewFeatureValues))
        )
        .default([])
        .describe("An array of preview features that are enabled.")
        .register(configRegistry, { overrideBehavior: onlySubsetOfBaseValueOverride() }),
    allowRequestOverrides: z4
        .preprocess(parseBoolean, z4.boolean())
        .default(false)
        .describe(
            "When set to true, allows configuration values to be overridden via request headers and query parameters."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    dryRun: z4
        .boolean()
        .default(false)
        .describe(
            "When true, runs the server in dry mode: dumps configuration and enabled tools, then exits without starting the server."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    externallyManagedSessions: z4
        .boolean()
        .default(false)
        .describe(
            "When true, the HTTP transport allows requests with a session ID supplied externally through the 'mcp-session-id' header. When an external ID is supplied, the initialization request is optional."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
    httpResponseType: z4
        .enum(["sse", "json"])
        .default("sse")
        .describe(
            "The HTTP response type for tool responses: 'sse' for Server-Sent Events, 'json' for standard JSON responses."
        )
        .register(configRegistry, { overrideBehavior: "not-allowed" }),
});

export const UserConfigSchema = z4.object({
    ...MongoshCliOptionsSchema.shape,
    ...ServerConfigSchema.shape,
});

export type UserConfig = z4.infer<typeof UserConfigSchema>;

export const ALL_CONFIG_KEYS: (keyof UserConfig)[] = Object.keys(UserConfigSchema.shape) as (keyof UserConfig)[];
