import { z, type ZodRawShape, type ZodNever, AnyZodObject } from "zod";
import type { RegisteredTool, ToolCallback } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult, ToolAnnotations } from "@modelcontextprotocol/sdk/types.js";
import { Session } from "../common/session.js";
import logger, { LogId } from "../common/logger.js";
import { Telemetry } from "../telemetry/telemetry.js";
import { type ToolEvent } from "../telemetry/types.js";
import { UserConfig } from "../common/config.js";
import { Server } from "../server.js";

export type ToolArgs<Args extends ZodRawShape> = z.objectOutputType<Args, ZodNever>;

export type OperationType = "metadata" | "read" | "create" | "delete" | "update" | "connect";
export type ToolCategory = "mongodb" | "atlas";
export type TelemetryToolMetadata = {
    projectId?: string;
    orgId?: string;
};

export abstract class ToolBase {
    public abstract name: string;

    public abstract category: ToolCategory;

    public abstract operationType: OperationType;

    protected abstract description: string;

    protected abstract argsShape: ZodRawShape;

    protected get annotations(): ToolAnnotations {
        const annotations: ToolAnnotations = {
            title: this.name,
        };

        switch (this.operationType) {
            case "read":
            case "metadata":
            case "connect":
                annotations.readOnlyHint = true;
                annotations.destructiveHint = false;
                break;
            case "delete":
                annotations.readOnlyHint = false;
                annotations.destructiveHint = true;
                break;
            case "create":
            case "update":
                annotations.destructiveHint = false;
                annotations.readOnlyHint = false;
                break;
            default:
                break;
        }

        return annotations;
    }

    protected abstract execute(...args: Parameters<ToolCallback<typeof this.argsShape>>): Promise<CallToolResult>;

    constructor(
        protected readonly session: Session,
        protected readonly config: UserConfig,
        protected readonly telemetry: Telemetry
    ) {}

    public register(server: Server): boolean {
        if (!this.verifyAllowed()) {
            return false;
        }

        const callback: ToolCallback<typeof this.argsShape> = async (...args) => {
            const startTime = Date.now();
            try {
                logger.debug(LogId.toolExecute, "tool", `Executing tool ${this.name}`);

                const result = await this.execute(...args);
                await this.emitToolEvent(startTime, result, ...args).catch(() => {});
                return result;
            } catch (error: unknown) {
                logger.error(LogId.toolExecuteFailure, "tool", `Error executing ${this.name}: ${error as string}`);
                const toolResult = await this.handleError(error, args[0] as ToolArgs<typeof this.argsShape>);
                await this.emitToolEvent(startTime, toolResult, ...args).catch(() => {});
                return toolResult;
            }
        };

        server.mcpServer.tool(this.name, this.description, this.argsShape, this.annotations, callback);

        // This is very similar to RegisteredTool.update, but without the bugs around the name.
        // In the upstream update method, the name is captured in the closure and not updated when
        // the tool name changes. This means that you only get one name update before things end up
        // in a broken state.
        // See https://github.com/modelcontextprotocol/typescript-sdk/issues/414 for more details.
        this.update = (updates: { name?: string; description?: string; inputSchema?: AnyZodObject }) => {
            const tools = server.mcpServer["_registeredTools"] as { [toolName: string]: RegisteredTool };
            const existingTool = tools[this.name];

            if (!existingTool) {
                logger.warning(LogId.toolUpdateFailure, "tool", `Tool ${this.name} not found in update`);
                return;
            }

            existingTool.annotations = this.annotations;

            if (updates.name && updates.name !== this.name) {
                existingTool.annotations.title = updates.name;
                delete tools[this.name];
                this.name = updates.name;
                tools[this.name] = existingTool;
            }

            if (updates.description) {
                existingTool.description = updates.description;
                this.description = updates.description;
            }

            if (updates.inputSchema) {
                existingTool.inputSchema = updates.inputSchema;
            }

            server.mcpServer.sendToolListChanged();
        };

        return true;
    }

    protected update?: (updates: { name?: string; description?: string; inputSchema?: AnyZodObject }) => void;

    // Checks if a tool is allowed to run based on the config
    protected verifyAllowed(): boolean {
        let errorClarification: string | undefined;

        // Check read-only mode first
        if (this.config.readOnly && !["read", "metadata"].includes(this.operationType)) {
            errorClarification = `read-only mode is enabled, its operation type, \`${this.operationType}\`,`;
        } else if (this.config.disabledTools.includes(this.category)) {
            errorClarification = `its category, \`${this.category}\`,`;
        } else if (this.config.disabledTools.includes(this.operationType)) {
            errorClarification = `its operation type, \`${this.operationType}\`,`;
        } else if (this.config.disabledTools.includes(this.name)) {
            errorClarification = `it`;
        }

        if (errorClarification) {
            logger.debug(
                LogId.toolDisabled,
                "tool",
                `Prevented registration of ${this.name} because ${errorClarification} is disabled in the config`
            );

            return false;
        }

        return true;
    }

    // This method is intended to be overridden by subclasses to handle errors
    protected handleError(
        error: unknown,
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        args: ToolArgs<typeof this.argsShape>
    ): Promise<CallToolResult> | CallToolResult {
        return {
            content: [
                {
                    type: "text",
                    text: `Error running ${this.name}: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }

    protected abstract resolveTelemetryMetadata(
        ...args: Parameters<ToolCallback<typeof this.argsShape>>
    ): TelemetryToolMetadata;

    /**
     * Creates and emits a tool telemetry event
     * @param startTime - Start time in milliseconds
     * @param result - Whether the command succeeded or failed
     * @param args - The arguments passed to the tool
     */
    private async emitToolEvent(
        startTime: number,
        result: CallToolResult,
        ...args: Parameters<ToolCallback<typeof this.argsShape>>
    ): Promise<void> {
        if (!this.telemetry.isTelemetryEnabled()) {
            return;
        }
        const duration = Date.now() - startTime;
        const metadata = this.resolveTelemetryMetadata(...args);
        const event: ToolEvent = {
            timestamp: new Date().toISOString(),
            source: "mdbmcp",
            properties: {
                command: this.name,
                category: this.category,
                component: "tool",
                duration_ms: duration,
                result: result.isError ? "failure" : "success",
            },
        };

        if (metadata?.orgId) {
            event.properties.org_id = metadata.orgId;
        }

        if (metadata?.projectId) {
            event.properties.project_id = metadata.projectId;
        }

        await this.telemetry.emitEvents([event]);
    }
}
