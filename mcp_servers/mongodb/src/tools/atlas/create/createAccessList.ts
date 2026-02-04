import { z } from "zod";
import { type OperationType, type ToolArgs } from "../../tool.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasToolBase } from "../atlasTool.js";
import { makeCurrentIpAccessListEntry, DEFAULT_ACCESS_LIST_COMMENT } from "../../../common/atlas/accessListUtils.js";
import { AtlasArgs, CommonArgs } from "../../args.js";

export const CreateAccessListArgs = {
    projectId: AtlasArgs.projectId().describe("Atlas project ID"),
    ipAddresses: z.array(AtlasArgs.ipAddress()).describe("IP addresses to allow access from").optional(),
    cidrBlocks: z.array(AtlasArgs.cidrBlock()).describe("CIDR blocks to allow access from").optional(),
    currentIpAddress: z.boolean().describe("Add the current IP address").default(false),
    comment: CommonArgs.string()
        .describe("Comment for the access list entries")
        .default(DEFAULT_ACCESS_LIST_COMMENT)
        .optional(),
};

export class CreateAccessListTool extends AtlasToolBase {
    public name = "atlas-create-access-list";
    public description = "Allow Ip/CIDR ranges to access your MongoDB Atlas clusters.";
    static operationType: OperationType = "create";
    public argsShape = {
        ...CreateAccessListArgs,
    };

    protected async execute({
        projectId,
        ipAddresses,
        cidrBlocks,
        comment,
        currentIpAddress,
    }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        if (!ipAddresses?.length && !cidrBlocks?.length && !currentIpAddress) {
            throw new Error("One of  ipAddresses, cidrBlocks, currentIpAddress must be provided.");
        }

        const ipInputs = (ipAddresses || []).map((ipAddress) => ({
            groupId: projectId,
            ipAddress,
            comment: comment || DEFAULT_ACCESS_LIST_COMMENT,
        }));

        if (currentIpAddress) {
            const input = await makeCurrentIpAccessListEntry(
                this.apiClient,
                projectId,
                comment || DEFAULT_ACCESS_LIST_COMMENT
            );
            ipInputs.push(input);
        }

        const cidrInputs = (cidrBlocks || []).map((cidrBlock) => ({
            groupId: projectId,
            cidrBlock,
            comment: comment || DEFAULT_ACCESS_LIST_COMMENT,
        }));

        const inputs = [...ipInputs, ...cidrInputs];

        await this.apiClient.createAccessListEntry({
            params: {
                path: {
                    groupId: projectId,
                },
            },
            body: inputs,
        });

        return {
            content: [
                {
                    type: "text",
                    text: `IP/CIDR ranges added to access list for project ${projectId}.`,
                },
            ],
        };
    }

    protected getConfirmationMessage({
        projectId,
        ipAddresses,
        cidrBlocks,
        comment,
        currentIpAddress,
    }: ToolArgs<typeof this.argsShape>): string {
        const accessDescription = [];
        if (ipAddresses?.length) {
            accessDescription.push(`- **IP addresses**: ${ipAddresses.join(", ")}`);
        }
        if (cidrBlocks?.length) {
            accessDescription.push(`- **CIDR blocks**: ${cidrBlocks.join(", ")}`);
        }
        if (currentIpAddress) {
            accessDescription.push("- **Current IP address**");
        }

        return (
            `You are about to add the following entries to the access list for Atlas project "${projectId}":\n\n` +
            accessDescription.join("\n") +
            `\n\n**Comment**: ${comment || DEFAULT_ACCESS_LIST_COMMENT}\n\n` +
            "This will allow network access to your MongoDB Atlas clusters from these IP addresses/ranges. " +
            "Do you want to proceed?"
        );
    }
}
