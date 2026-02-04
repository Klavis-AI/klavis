import { ReactiveResource } from "../resource.js";
import type { Telemetry } from "../../telemetry/telemetry.js";
import type { Session, UserConfig } from "../../lib.js";
import type { AtlasClusterConnectionInfo, ConnectionStateErrored } from "../../common/connectionManager.js";
import type { ConnectionStringInfo } from "../../common/connectionInfo.js";

type ConnectionStateDebuggingInformation = {
    readonly tag: "connected" | "connecting" | "disconnected" | "errored";
    readonly connectionStringInfo?: ConnectionStringInfo;
    readonly errorReason?: string;
    readonly connectedAtlasCluster?: AtlasClusterConnectionInfo;
};

export class DebugResource extends ReactiveResource<
    ConnectionStateDebuggingInformation,
    readonly ["connect", "disconnect", "close", "connection-error"]
> {
    constructor(session: Session, config: UserConfig, telemetry: Telemetry) {
        super({
            resourceConfiguration: {
                name: "debug-mongodb",
                uri: "debug://mongodb",
                config: {
                    description:
                        "Debugging information for MongoDB connectivity issues. Tracks the last connectivity attempt and error information.",
                },
            },
            options: {
                initial: { tag: "disconnected" },
                events: ["connect", "disconnect", "close", "connection-error"],
            },
            session,
            config,
            telemetry,
        });
    }
    reduce(
        eventName: "connect" | "disconnect" | "close" | "connection-error",
        event: ConnectionStateErrored | undefined
    ): ConnectionStateDebuggingInformation {
        switch (eventName) {
            case "connect":
                return { tag: "connected" };
            case "connection-error": {
                return {
                    tag: "errored",
                    connectionStringInfo: event?.connectionStringInfo,
                    connectedAtlasCluster: event?.connectedAtlasCluster,
                    errorReason:
                        event?.errorReason ??
                        "Could not find a reason. This might be a bug in the MCP Server. Please open an issue in https://github.com/mongodb-js/mongodb-mcp-server.",
                };
            }
            case "disconnect":
            case "close":
                return { tag: "disconnected" };
        }
    }

    async toOutput(): Promise<string> {
        let result = "";

        switch (this.current.tag) {
            case "connected": {
                const searchIndexesSupported = await this.session.isSearchSupported();
                result += `The user is connected to the MongoDB cluster${searchIndexesSupported ? " with support for search indexes" : " without any support for search indexes"}.`;
                break;
            }
            case "errored":
                result += `The user is not connected to a MongoDB cluster because of an error.\n`;
                if (this.current.connectedAtlasCluster) {
                    result += `Attempted connecting to Atlas Cluster "${this.current.connectedAtlasCluster.clusterName}" in project with id "${this.current.connectedAtlasCluster.projectId}".\n`;
                }

                if (this.current.connectionStringInfo?.authType !== undefined) {
                    result += `The inferred authentication mechanism is "${this.current.connectionStringInfo.authType}".\n`;
                }
                result += `<error>${this.current.errorReason}</error>`;
                break;
            case "connecting":
            case "disconnected":
                result += "The user is not connected to a MongoDB cluster.";
                break;
        }

        return result;
    }
}
