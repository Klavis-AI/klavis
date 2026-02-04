import z from "zod";
import { ObjectId } from "bson";
import type { AggregationCursor, FindCursor } from "mongodb";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type { OperationType, ToolArgs, ToolExecutionContext } from "../../tool.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import { FindArgs } from "./find.js";
import { jsonExportFormat } from "../../../common/exportsManager.js";
import { getAggregateArgs } from "./aggregate.js";

export class ExportTool extends MongoDBToolBase {
    public name = "export";
    public description = "Export a query or aggregation results in the specified EJSON format.";
    public argsShape = {
        ...DbOperationArgs,
        exportTitle: z.string().describe("A short description to uniquely identify the export."),
        // Note: Although it is not required to wrap the discriminated union in
        // an array here because we only expect exactly one exportTarget to be
        // provided here, we unfortunately cannot use the discriminatedUnion as
        // is because Cursor is unable to construct payload for tool calls where
        // the input schema contains a discriminated union without such
        // wrapping. This is a workaround for enabling the tool calls on Cursor.
        exportTarget: z
            .array(
                z.discriminatedUnion("name", [
                    z.object({
                        name: z
                            .literal("find")
                            .describe("The literal name 'find' to represent a find cursor as target."),
                        arguments: z
                            .object({
                                ...FindArgs,
                                limit: FindArgs.limit.removeDefault(),
                            })
                            .describe("The arguments for 'find' operation."),
                    }),
                    z.object({
                        name: z
                            .literal("aggregate")
                            .describe("The literal name 'aggregate' to represent an aggregation cursor as target."),
                        arguments: z
                            .object(getAggregateArgs(this.isFeatureEnabled("search")))
                            .describe("The arguments for 'aggregate' operation."),
                    }),
                ])
            )
            .describe("The export target along with its arguments."),
        jsonExportFormat: jsonExportFormat
            .default("relaxed")
            .describe(
                [
                    "The format to be used when exporting collection data as EJSON with default being relaxed.",
                    "relaxed: A string format that emphasizes readability and interoperability at the expense of type preservation. That is, conversion from relaxed format to BSON can lose type information.",
                    "canonical: A string format that emphasizes type preservation at the expense of readability and interoperability. That is, conversion from canonical to BSON will generally preserve type information except in certain specific cases.",
                ].join("\n")
            ),
    };
    static operationType: OperationType = "read";

    protected async execute(
        { database, collection, jsonExportFormat, exportTitle, exportTarget: target }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const exportTarget = target[0];
        if (!exportTarget) {
            throw new Error("Export target not provided. Expected one of the following: `aggregate`, `find`");
        }

        let cursor: FindCursor | AggregationCursor;
        if (exportTarget.name === "find") {
            const { filter, projection, sort, limit } = exportTarget.arguments;
            cursor = provider.find(database, collection, filter ?? {}, {
                projection,
                sort,
                limit,
                promoteValues: false,
                bsonRegExp: true,
                // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                signal,
            });
        } else {
            const { pipeline } = exportTarget.arguments;
            cursor = provider.aggregate(database, collection, pipeline, {
                promoteValues: false,
                bsonRegExp: true,
                allowDiskUse: true,
                // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                signal,
            });
        }

        const exportName = `${new ObjectId().toString()}.json`;

        const { exportURI, exportPath } = await this.session.exportsManager.createJSONExport({
            input: cursor,
            exportName,
            exportTitle:
                exportTitle ||
                `Export for namespace ${database}.${collection} requested on ${new Date().toLocaleString()}`,
            jsonExportFormat,
        });
        const toolCallContent: CallToolResult["content"] = [
            // Not all the clients as of this commit understands how to
            // parse a resource_link so we provide a text result for them to
            // understand what to do with the result.
            {
                type: "text",
                text: `Data for namespace ${database}.${collection} is being exported and will be made available under resource URI - "${exportURI}".`,
            },
            {
                type: "resource_link",
                name: exportName,
                uri: exportURI,
                description: "Resource URI for fetching exported data once it is ready.",
                mimeType: "application/json",
            },
        ];

        // This special case is to make it easier to work with exported data for
        // clients that still cannot reference resources (Cursor).
        // More information here: https://jira.mongodb.org/browse/MCP-104
        if (this.isServerRunningLocally()) {
            toolCallContent.push({
                type: "text",
                text: `Optionally, when the export is finished, the exported data can also be accessed under path - "${exportPath}"`,
            });
        }

        return {
            content: toolCallContent,
        };
    }

    private isServerRunningLocally(): boolean {
        return this.config.transport === "stdio" || ["127.0.0.1", "localhost"].includes(this.config.httpHost);
    }
}
