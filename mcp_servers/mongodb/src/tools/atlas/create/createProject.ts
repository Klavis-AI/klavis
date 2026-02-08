import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasToolBase } from "../atlasTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { Group } from "../../../common/atlas/openapi.js";

export class CreateProjectTool extends AtlasToolBase {
    public name = "atlas-create-project";
    protected description = "Create a MongoDB Atlas project";
    public operationType: OperationType = "create";
    protected argsShape = {
        projectName: z.string().optional().describe("Name for the new project"),
        organizationId: z.string().optional().describe("Organization ID for the new project"),
    };

    protected async execute({ projectName, organizationId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        let assumedOrg = false;

        if (!projectName) {
            projectName = "Atlas Project";
        }

        if (!organizationId) {
            try {
                const organizations = await this.session.apiClient.listOrganizations();
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

        const group = await this.session.apiClient.createProject({
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
