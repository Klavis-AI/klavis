import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { AtlasToolBase } from "../atlasTool.js";
import type { ToolArgs, OperationType } from "../../tool.js";
import { formatUntrustedData } from "../../tool.js";
import { AtlasArgs } from "../../args.js";

export const ListDBUsersArgs = {
    projectId: AtlasArgs.projectId().describe("Atlas project ID to filter DB users"),
};

export class ListDBUsersTool extends AtlasToolBase {
    public name = "atlas-list-db-users";
    public description = "List MongoDB Atlas database users";
    public static operationType: OperationType = "read";
    public argsShape = {
        ...ListDBUsersArgs,
    };

    protected async execute({ projectId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const data = await this.apiClient.listDatabaseUsers({
            params: {
                path: {
                    groupId: projectId,
                },
            },
        });

        if (!data?.results?.length) {
            return {
                content: [{ type: "text", text: " No database users found" }],
            };
        }

        const users = data.results.map((user) => ({
            username: user.username,
            roles:
                user.roles?.map((role) => ({
                    roleName: role.roleName,
                    databaseName: role.databaseName,
                    collectionName: role.collectionName,
                })) ?? [],
            scopes:
                user.scopes?.map((scope) => ({
                    type: scope.type,
                    name: scope.name,
                })) ?? [],
        }));

        return {
            content: formatUntrustedData(
                `Found ${data.results.length} database users in project ${projectId}`,
                JSON.stringify(users)
            ),
        };
    }
}
