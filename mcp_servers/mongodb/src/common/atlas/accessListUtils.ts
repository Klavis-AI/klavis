import { ApiClient } from "./apiClient.js";
import logger, { LogId } from "../logger.js";
import { ApiClientError } from "./apiClientError.js";

export const DEFAULT_ACCESS_LIST_COMMENT = "Added by MongoDB MCP Server to enable tool access";

export async function makeCurrentIpAccessListEntry(
    apiClient: ApiClient,
    projectId: string,
    comment: string = DEFAULT_ACCESS_LIST_COMMENT
) {
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
 */
export async function ensureCurrentIpInAccessList(apiClient: ApiClient, projectId: string): Promise<void> {
    const entry = await makeCurrentIpAccessListEntry(apiClient, projectId, DEFAULT_ACCESS_LIST_COMMENT);
    try {
        await apiClient.createProjectIpAccessList({
            params: { path: { groupId: projectId } },
            body: [entry],
        });
        logger.debug(
            LogId.atlasIpAccessListAdded,
            "accessListUtils",
            `IP access list created: ${JSON.stringify(entry)}`
        );
    } catch (err) {
        if (err instanceof ApiClientError && err.response?.status === 409) {
            // 409 Conflict: entry already exists, log info
            logger.debug(
                LogId.atlasIpAccessListAdded,
                "accessListUtils",
                `IP address ${entry.ipAddress} is already present in the access list for project ${projectId}.`
            );
            return;
        }
        logger.warning(
            LogId.atlasIpAccessListAddFailure,
            "accessListUtils",
            `Error adding IP access list: ${err instanceof Error ? err.message : String(err)}`
        );
    }
}
