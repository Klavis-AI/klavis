import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasLocalToolBase } from "../atlasLocalTool.js";
import type { OperationType, ToolArgs } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import type { Deployment } from "@mongodb-js/atlas-local";
import type { Client } from "@mongodb-js/atlas-local";

export class ListDeploymentsTool extends AtlasLocalToolBase {
    public name = "atlas-local-list-deployments";
    public description = "List MongoDB Atlas local deployments";
    static operationType: OperationType = "read";
    public argsShape = {};

    protected async executeWithAtlasLocalClient(
        _args: ToolArgs<typeof this.argsShape>,
        { client }: { client: Client }
    ): Promise<CallToolResult> {
        // List the deployments
        const deployments = await client.listDeployments();

        // Format the deployments
        return this.formatDeploymentsTable(deployments);
    }

    private formatDeploymentsTable(deployments: Deployment[]): CallToolResult {
        // Check if deployments are absent
        if (!deployments?.length) {
            return {
                content: [{ type: "text", text: "No deployments found." }],
            };
        }

        // Filter out the fields we want to return to the user
        // We don't want to return the entire deployment object because it contains too much data
        const deploymentsJson = deployments.map((deployment) => {
            return {
                name: deployment.name,
                state: deployment.state,
                mongodbVersion: deployment.mongodbVersion,
            };
        });

        return {
            content: formatUntrustedData(`Found ${deployments.length} deployments`, JSON.stringify(deploymentsJson)),
        };
    }
}
