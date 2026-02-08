import { z } from "zod";
import { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasToolBase } from "../atlasTool.js";
import { ToolArgs, OperationType } from "../../tool.js";
import { DatabaseUserRole, UserScope } from "../../../common/atlas/openapi.js";

export class ListDBUsersTool extends AtlasToolBase {
    public name = "atlas-list-db-users";
    protected description = "List MongoDB Atlas database users";
    public operationType: OperationType = "read";
    protected argsShape = {
        projectId: z.string().describe("Atlas project ID to filter DB users"),
    };

    protected async execute({ projectId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const data = await this.session.apiClient.listDatabaseUsers({
            params: {
                path: {
                    groupId: projectId,
                },
            },
        });

        if (!data?.results?.length) {
            throw new Error("No database users found.");
        }

        const output =
            `Username | Roles | Scopes
----------------|----------------|----------------
` +
            data.results
                .map((user) => {
                    return `${user.username} | ${formatRoles(user.roles)} | ${formatScopes(user.scopes)}`;
                })
                .join("\n");
        return {
            content: [{ type: "text", text: output }],
        };
    }
}

function formatRoles(roles?: DatabaseUserRole[]) {
    if (!roles?.length) {
        return "N/A";
    }
    return roles
        .map(
            (role) =>
                `${role.roleName}${role.databaseName ? `@${role.databaseName}${role.collectionName ? `:${role.collectionName}` : ""}` : ""}`
        )
        .join(", ");
}

function formatScopes(scopes?: UserScope[]) {
    if (!scopes?.length) {
        return "All";
    }
    return scopes.map((scope) => `${scope.type}:${scope.name}`).join(", ");
}
