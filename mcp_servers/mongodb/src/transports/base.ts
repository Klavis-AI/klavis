import { UserConfig } from "../common/config.js";
import { packageInfo } from "../common/packageInfo.js";
import { Server } from "../server.js";
import { Session } from "../common/session.js";
import { Telemetry } from "../telemetry/telemetry.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

export abstract class TransportRunnerBase {
    protected setupServer(userConfig: UserConfig): Server {
        const session = new Session({
            apiBaseUrl: userConfig.apiBaseUrl,
            apiClientId: userConfig.apiClientId,
            apiClientSecret: userConfig.apiClientSecret,
        });

        const telemetry = Telemetry.create(session, userConfig);

        const mcpServer = new McpServer({
            name: packageInfo.mcpServerName,
            version: packageInfo.version,
        });

        return new Server({
            mcpServer,
            session,
            telemetry,
            userConfig,
        });
    }

    abstract start(): Promise<void>;

    abstract close(): Promise<void>;
}
