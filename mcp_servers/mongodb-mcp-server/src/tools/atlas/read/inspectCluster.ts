import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { type OperationType, type ToolArgs, formatUntrustedData } from "../../tool.js";
import { AtlasToolBase } from "../atlasTool.js";
import type { Cluster } from "../../../common/atlas/cluster.js";
import { inspectCluster } from "../../../common/atlas/cluster.js";
import { AtlasArgs } from "../../args.js";

export const InspectClusterArgs = {
    projectId: AtlasArgs.projectId().describe("Atlas project ID"),
    clusterName: AtlasArgs.clusterName().describe("Atlas cluster name"),
};

export class InspectClusterTool extends AtlasToolBase {
    public name = "atlas-inspect-cluster";
    public description = "Inspect metadata of a MongoDB Atlas cluster";
    static operationType: OperationType = "read";
    public argsShape = {
        ...InspectClusterArgs,
    };

    protected async execute({ projectId, clusterName }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const cluster = await inspectCluster(this.apiClient, projectId, clusterName);

        return this.formatOutput(cluster);
    }

    private formatOutput(formattedCluster: Cluster): CallToolResult {
        const clusterDetails = {
            name: formattedCluster.name || "Unknown",
            instanceType: formattedCluster.instanceType,
            instanceSize: formattedCluster.instanceSize || "N/A",
            state: formattedCluster.state || "UNKNOWN",
            mongoDBVersion: formattedCluster.mongoDBVersion || "N/A",
            connectionStrings: formattedCluster.connectionStrings || {},
        };

        return {
            content: formatUntrustedData("Cluster details:", JSON.stringify(clusterDetails)),
        };
    }
}
