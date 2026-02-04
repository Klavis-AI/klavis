import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { DbOperationArgs, MongoDBToolBase } from "../mongodbTool.js";
import type { ToolArgs, OperationType, ToolExecutionContext } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import { z } from "zod";
import type { Document } from "mongodb";
import { getAggregateArgs } from "../read/aggregate.js";
import { FindArgs } from "../read/find.js";
import { CountArgs } from "../read/count.js";

export class ExplainTool extends MongoDBToolBase {
    public name = "explain";
    public description =
        "Returns statistics describing the execution of the winning plan chosen by the query optimizer for the evaluated method";

    public argsShape = {
        ...DbOperationArgs,
        // Note: Although it is not required to wrap the discriminated union in
        // an array here because we only expect exactly one method to be
        // provided here, we unfortunately cannot use the discriminatedUnion as
        // is because Cursor is unable to construct payload for tool calls where
        // the input schema contains a discriminated union without such
        // wrapping. This is a workaround for enabling the tool calls on Cursor.
        method: z
            .array(
                z.discriminatedUnion("name", [
                    z.object({
                        name: z.literal("aggregate"),
                        arguments: z.object(getAggregateArgs(this.isFeatureEnabled("search"))),
                    }),
                    z.object({
                        name: z.literal("find"),
                        arguments: z.object(FindArgs),
                    }),
                    z.object({
                        name: z.literal("count"),
                        arguments: z.object(CountArgs),
                    }),
                ])
            )
            .describe("The method and its arguments to run"),
        verbosity: z
            .enum(["queryPlanner", "queryPlannerExtended", "executionStats", "allPlansExecution"])
            .optional()
            .default("queryPlanner")
            .describe(
                "The verbosity of the explain plan, defaults to queryPlanner. If the user wants to know how fast is a query in execution time, use executionStats. It supports all verbosities as defined in the MongoDB Driver."
            ),
    };

    static operationType: OperationType = "metadata";

    protected async execute(
        { database, collection, method: methods, verbosity }: ToolArgs<typeof this.argsShape>,
        { signal }: ToolExecutionContext
    ): Promise<CallToolResult> {
        const provider = await this.ensureConnected();
        const method = methods[0];

        if (!method) {
            throw new Error("No method provided. Expected one of the following: `aggregate`, `find`, or `count`");
        }

        let result: Document;
        switch (method.name) {
            case "aggregate": {
                const { pipeline } = method.arguments;
                result = await provider
                    .aggregate(
                        database,
                        collection,
                        pipeline,
                        {
                            // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                            signal,
                        },
                        {
                            writeConcern: undefined,
                        }
                    )
                    .explain(verbosity);
                break;
            }
            case "find": {
                const { filter, ...rest } = method.arguments;
                result = await provider
                    .find(database, collection, filter as Document, {
                        ...rest,
                        // @ts-expect-error signal is available in the driver but not NodeDriverServiceProvider MONGOSH-3142
                        signal,
                    })
                    .explain(verbosity);
                break;
            }
            case "count": {
                const { query } = method.arguments;
                result = await provider.runCommandWithCheck(
                    database,
                    {
                        explain: {
                            count: collection,
                            query,
                        },
                        verbosity,
                    },
                    {
                        signal,
                    }
                );
                break;
            }
        }

        return {
            content: formatUntrustedData(
                `Here is some information about the winning plan chosen by the query optimizer for running the given \`${method.name}\` operation in "${database}.${collection}". The execution plan was run with the following verbosity: "${verbosity}". This information can be used to understand how the query was executed and to optimize the query performance.`,
                JSON.stringify(result)
            ),
        };
    }
}
