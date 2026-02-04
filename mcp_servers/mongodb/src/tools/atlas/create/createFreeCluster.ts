import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasToolBase } from "../atlasTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { ClusterDescription20240805 } from "../../../common/atlas/openapi.js";
import { ensureCurrentIpInAccessList } from "../../../common/atlas/accessListUtils.js";

export class CreateFreeClusterTool extends AtlasToolBase {
    public name = "atlas-create-free-cluster";
    protected description = "Create a free MongoDB Atlas cluster";
    public operationType: OperationType = "create";
    protected argsShape = {
        projectId: z.string().describe("Atlas project ID to create the cluster in"),
        name: z.string().describe("Name of the cluster"),
        region: z.string().describe("Region of the cluster").default("US_EAST_1"),
    };

    protected async execute({ projectId, name, region }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const input = {
            groupId: projectId,
            name,
            clusterType: "REPLICASET",
            replicationSpecs: [
                {
                    zoneName: "Zone 1",
                    regionConfigs: [
                        {
                            providerName: "TENANT",
                            backingProviderName: "AWS",
                            regionName: region,
                            electableSpecs: {
                                instanceSize: "M0",
                            },
                        },
                    ],
                },
            ],
            terminationProtectionEnabled: false,
        } as unknown as ClusterDescription20240805;

        await ensureCurrentIpInAccessList(this.session.apiClient, projectId);
        await this.session.apiClient.createCluster({
            params: {
                path: {
                    groupId: projectId,
                },
            },
            body: input,
        });

        return {
            content: [
                { type: "text", text: `Cluster "${name}" has been created in region "${region}".` },
                { type: "text", text: `Double check your access lists to enable your current IP.` },
            ],
        };
    }
}
