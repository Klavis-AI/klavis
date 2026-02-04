import type {
    ClusterConnectionStrings,
    ClusterDescription20240805,
    FlexClusterDescription20241113,
} from "./openapi.js";
import type { ApiClient } from "./apiClient.js";
import { LogId } from "../logger.js";
import { ConnectionString } from "mongodb-connection-string-url";

type AtlasProcessId = `${string}:${number}`;

function extractProcessIds(connectionString: string): Array<AtlasProcessId> {
    if (!connectionString) {
        return [];
    }
    const connectionStringUrl = new ConnectionString(connectionString);
    return connectionStringUrl.hosts as Array<AtlasProcessId>;
}
export interface Cluster {
    name?: string;
    instanceType: "FREE" | "DEDICATED" | "FLEX";
    instanceSize?: string;
    state?: "IDLE" | "CREATING" | "UPDATING" | "DELETING" | "REPAIRING";
    mongoDBVersion?: string;
    connectionStrings?: ClusterConnectionStrings;
    processIds?: Array<string>;
}

export function formatFlexCluster(cluster: FlexClusterDescription20241113): Cluster {
    return {
        name: cluster.name,
        instanceType: "FLEX",
        instanceSize: undefined,
        state: cluster.stateName,
        mongoDBVersion: cluster.mongoDBVersion,
        connectionStrings: cluster.connectionStrings,
        processIds: extractProcessIds(cluster.connectionStrings?.standard ?? ""),
    };
}

export function formatCluster(cluster: ClusterDescription20240805): Cluster {
    const regionConfigs = (cluster.replicationSpecs || [])
        .map(
            (replicationSpec) =>
                (replicationSpec.regionConfigs || []) as {
                    providerName: string;
                    electableSpecs?: {
                        instanceSize: string;
                    };
                    readOnlySpecs?: {
                        instanceSize: string;
                    };
                    analyticsSpecs?: {
                        instanceSize: string;
                    };
                }[]
        )
        .flat()
        .map((regionConfig) => {
            return {
                providerName: regionConfig.providerName,
                instanceSize:
                    regionConfig.electableSpecs?.instanceSize ||
                    regionConfig.readOnlySpecs?.instanceSize ||
                    regionConfig.analyticsSpecs?.instanceSize,
            };
        });

    const instanceSize = regionConfigs[0]?.instanceSize ?? "UNKNOWN";
    const clusterInstanceType = instanceSize === "M0" ? "FREE" : "DEDICATED";

    return {
        name: cluster.name,
        instanceType: clusterInstanceType,
        instanceSize: clusterInstanceType === "DEDICATED" ? instanceSize : undefined,
        state: cluster.stateName,
        mongoDBVersion: cluster.mongoDBVersion,
        connectionStrings: cluster.connectionStrings,
        processIds: extractProcessIds(cluster.connectionStrings?.standard ?? ""),
    };
}

export async function inspectCluster(apiClient: ApiClient, projectId: string, clusterName: string): Promise<Cluster> {
    try {
        const cluster = await apiClient.getCluster({
            params: {
                path: {
                    groupId: projectId,
                    clusterName,
                },
            },
        });
        return formatCluster(cluster);
    } catch (error) {
        try {
            const cluster = await apiClient.getFlexCluster({
                params: {
                    path: {
                        groupId: projectId,
                        name: clusterName,
                    },
                },
            });
            return formatFlexCluster(cluster);
        } catch (flexError) {
            const err = flexError instanceof Error ? flexError : new Error(String(flexError));
            apiClient.logger.error({
                id: LogId.atlasInspectFailure,
                context: "inspect-cluster",
                message: `error inspecting cluster: ${err.message}`,
            });
            throw error;
        }
    }
}

/**
 * Returns a connection string for the specified connectionType.
 * For "privateEndpoint", it returns the first private endpoint connection string available.
 */
export function getConnectionString(
    connectionStrings: ClusterConnectionStrings,
    connectionType: "standard" | "private" | "privateEndpoint"
): string | undefined {
    switch (connectionType) {
        case "standard":
            return connectionStrings.standardSrv || connectionStrings.standard;
        case "private":
            return connectionStrings.privateSrv || connectionStrings.private;
        case "privateEndpoint":
            return (
                connectionStrings.privateEndpoint?.[0]?.srvConnectionString ||
                connectionStrings.privateEndpoint?.[0]?.connectionString
            );
    }
}

export async function getProcessIdsFromCluster(
    apiClient: ApiClient,
    projectId: string,
    clusterName: string
): Promise<Array<string>> {
    try {
        const cluster = await inspectCluster(apiClient, projectId, clusterName);
        return cluster.processIds || [];
    } catch (error) {
        throw new Error(
            `Failed to get processIds from cluster: ${error instanceof Error ? error.message : String(error)}`
        );
    }
}
