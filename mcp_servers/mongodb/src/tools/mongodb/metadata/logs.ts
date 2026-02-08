import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { MongoDBToolBase } from "../mongodbTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { z } from "zod";

export class LogsTool extends MongoDBToolBase {
    public name = "mongodb-logs";
    protected description = "Returns the most recent logged mongod events";
    protected argsShape = {
        type: z
            .enum(["global", "startupWarnings"])
            .optional()
            .default("global")
            .describe(
                "The type of logs to return. Global returns all recent log entries, while startupWarnings returns only warnings and errors from when the process started."
            ),
        limit: z
            .number()
            .int()
            .max(1024)
            .min(1)
            .optional()
            .default(50)
            .describe("The maximum number of log entries to return."),
    };

    public operationType: OperationType = "metadata";

    protected async execute({ type, limit }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const provider = await this.ensureConnected();

        const result = await provider.runCommandWithCheck("admin", {
            getLog: type,
        });

        const logs = (result.log as string[]).slice(0, limit);

        return {
            content: [
                {
                    text: `Found: ${result.totalLinesWritten} messages`,
                    type: "text",
                },

                ...logs.map(
                    (log) =>
                        ({
                            text: log,
                            type: "text",
                        }) as const
                ),
            ],
        };
    }
}
