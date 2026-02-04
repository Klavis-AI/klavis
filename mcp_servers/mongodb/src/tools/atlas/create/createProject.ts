import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { type OperationType, type ToolArgs } from "../../tool.js";
import { AtlasToolBase } from "../atlasTool.js";
import type { Group } from "../../../common/atlas/openapi.js";
import { AtlasArgs } from "../../args.js";

export class CreateProjectTool extends AtlasToolBase {
    public name = "atlas-create-project";
    public description = "Create a MongoDB Atlas project";
    static operationType: OperationType = "create";
    public argsShape = {
        projectName: AtlasArgs.projectName().optional().describe("Name for the new project"),
        organizationId: AtlasArgs.organizationId().optional().describe("Organization ID for the new project"),
    };

    protected async execute({ projectName, organizationId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        let assumedOrg = false;

        if (!projectName) {
            projectName = "Atlas Project";
        }

        if (!organizationId) {
            try {
                const organizations = await this.apiClient.listOrgs();
                if (!organizations?.results?.length) {
                    throw new Error(
                        "No organizations were found in your MongoDB Atlas account. Please create an organization first."
                    );
                }
                const firstOrg = organizations.results[0];
                if (!firstOrg?.id) {
                    throw new Error(
                        "The first organization found does not have an ID. Please check your Atlas account."
                    );
                }
                organizationId = firstOrg.id;
                assumedOrg = true;
            } catch {
                throw new Error(
                    "Could not search for organizations in your MongoDB Atlas account, please provide an organization ID or create one first."
                );
            }
        }

        const input = {
            name: projectName,
            orgId: organizationId,
        } as Group;

        const group = await this.apiClient.createGroup({
            body: input,
        });

        if (!group?.id) {
            throw new Error("Failed to create project");
        }

        return {
            content: [
                {
                    type: "text",
                    text: `Project "${projectName}" created successfully${assumedOrg ? ` (using organizationId ${organizationId}).` : ""}.`,
                },
            ],
        };
    }
}
