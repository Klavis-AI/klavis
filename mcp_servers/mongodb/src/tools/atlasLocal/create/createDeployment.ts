import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasLocalToolBase } from "../atlasLocalTool.js";
import type { OperationType, ToolArgs } from "../../tool.js";
import type { Client, CreateDeploymentOptions } from "@mongodb-js/atlas-local";
import { CommonArgs } from "../../args.js";
import z from "zod";

export class CreateDeploymentTool extends AtlasLocalToolBase {
    public name = "atlas-local-create-deployment";
    public description = "Create a MongoDB Atlas local deployment";
    static operationType: OperationType = "create";
    public argsShape = {
        deploymentName: CommonArgs.string().describe("Name of the deployment to create").optional(),
        loadSampleData: z.boolean().describe("Load sample data into the deployment").optional().default(false),
    };

    protected async executeWithAtlasLocalClient(
        { deploymentName, loadSampleData }: ToolArgs<typeof this.argsShape>,
        { client }: { client: Client }
    ): Promise<CallToolResult> {
        const deploymentOptions: CreateDeploymentOptions = {
            name: deploymentName,
            creationSource: {
                type: "MCPServer",
                source: "MCPServer",
            },
            loadSampleData,
            doNotTrack: !this.telemetry.isTelemetryEnabled(),
        };
        // Create the deployment
        const deployment = await client.createDeployment(deploymentOptions);

        return {
            content: [
                {
                    type: "text",
                    text: `Deployment with container ID "${deployment.containerId}" and name "${deployment.name}" created.`,
                },
            ],
            _meta: {
                ...(await this.lookupTelemetryMetadata(client, deployment.containerId)),
            },
        };
    }
}
