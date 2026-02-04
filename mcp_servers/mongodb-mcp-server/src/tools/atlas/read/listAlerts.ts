import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { type OperationType, type ToolArgs, formatUntrustedData } from "../../tool.js";
import { AtlasToolBase } from "../atlasTool.js";
import { AtlasArgs } from "../../args.js";

export const ListAlertsArgs = {
    projectId: AtlasArgs.projectId().describe("Atlas project ID to list alerts for"),
};

export class ListAlertsTool extends AtlasToolBase {
    public name = "atlas-list-alerts";
    public description = "List MongoDB Atlas alerts";
    static operationType: OperationType = "read";
    public argsShape = {
        ...ListAlertsArgs,
    };

    protected async execute({ projectId }: ToolArgs<typeof this.argsShape>): Promise<CallToolResult> {
        const data = await this.apiClient.listAlerts({
            params: {
                path: {
                    groupId: projectId,
                },
            },
        });

        if (!data?.results?.length) {
            return { content: [{ type: "text", text: "No alerts found in your MongoDB Atlas project." }] };
        }

        const alerts = data.results.map((alert) => ({
            id: alert.id,
            status: alert.status,
            created: alert.created ? new Date(alert.created).toISOString() : "N/A",
            updated: alert.updated ? new Date(alert.updated).toISOString() : "N/A",
            eventTypeName: alert.eventTypeName,
            acknowledgementComment: alert.acknowledgementComment ?? "N/A",
        }));

        return {
            content: formatUntrustedData(
                `Found ${data.results.length} alerts in project ${projectId}`,
                JSON.stringify(alerts)
            ),
        };
    }
}
