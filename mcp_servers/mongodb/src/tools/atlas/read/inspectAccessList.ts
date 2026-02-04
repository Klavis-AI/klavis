import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { type OperationType, type ToolArgs, formatUntrustedData } from "../../tool.js";
import { AtlasToolBase } from "../atlasTool.js";
import { AtlasArgs } from "../../args.js";

export const InspectAccessListArgs = {
    projectId: AtlasArgs.projectId().describe("Atlas project ID"),
};

export class InspectAccessListTool extends AtlasToolBase {
    public name = "atlas-inspect-access-list";
    public description = "Inspect Ip/CIDR ranges with access to your MongoDB Atlas clusters.";
    static operationType: OperationType = "read";
    public argsShape = {
        ...InspectAccessListArgs,
    };

    protected async execute({ projectId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const accessList = await this.apiClient.listAccessListEntries({
            params: {
                path: {
                    groupId: projectId,
                },
            },
        });

        const results = accessList.results ?? [];

        if (!results.length) {
            return {
                content: [{ type: "text", text: "No access list entries found." }],
            };
        }

        const entries = results.map((entry) => ({
            ipAddress: entry.ipAddress,
            cidrBlock: entry.cidrBlock,
            comment: entry.comment,
        }));

        return {
            content: formatUntrustedData(`Found ${results.length} access list entries`, JSON.stringify(entries)),
        };
    }
}
