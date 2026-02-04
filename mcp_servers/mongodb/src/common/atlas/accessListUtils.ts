import type { ApiClient } from "./apiClient.js";
import { LogId } from "../logger.js";
import { ApiClientError } from "./apiClientError.js";

export const DEFAULT_ACCESS_LIST_COMMENT = "Added by MongoDB MCP Server to enable tool access";

export async function makeCurrentIpAccessListEntry(
    apiClient: ApiClient,
    projectId: string,
    comment: string = DEFAULT_ACCESS_LIST_COMMENT
): Promise<{ groupId: string; ipAddress: string; comment: string }> {
    const { currentIpv4Address } = await apiClient.getIpInfo();
    return {
        groupId: projectId,
        ipAddress: currentIpv4Address,
        comment,
    };
}

/**
 * Ensures the current public IP is in the access list for the given Atlas project.
 * If the IP is already present, this is a no-op.
 * @param apiClient The Atlas API client instance
 * @param projectId The Atlas project ID
 * @returns Promise<boolean> - true if a new IP access list entry was created, false if it already existed
 */
export async function ensureCurrentIpInAccessList(apiClient: ApiClient, projectId: string): Promise<boolean> {
    const entry = await makeCurrentIpAccessListEntry(apiClient, projectId, DEFAULT_ACCESS_LIST_COMMENT);
    try {
        await apiClient.createAccessListEntry({
            params: { path: { groupId: projectId } },
            body: [entry],
        });
        apiClient.logger.debug({
            id: LogId.atlasIpAccessListAdded,
            context: "accessListUtils",
            message: `IP access list created: ${JSON.stringify(entry)}`,
        });
        return true;
    } catch (err) {
        if (err instanceof ApiClientError && err.response?.status === 409) {
            // 409 Conflict: entry already exists, log info
            apiClient.logger.debug({
                id: LogId.atlasIpAccessListAdded,
                context: "accessListUtils",
                message: `IP address ${entry.ipAddress} is already present in the access list for project ${projectId}.`,
            });
            return false;
        }
        apiClient.logger.warning({
            id: LogId.atlasIpAccessListAddFailure,
            context: "accessListUtils",
            message: `Error adding IP access list: ${err instanceof Error ? err.message : String(err)}`,
        });
    }
    return false;
}
