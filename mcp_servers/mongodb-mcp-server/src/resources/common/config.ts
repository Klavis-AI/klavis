import { ReactiveResource } from "../resource.js";
import type { UserConfig } from "../../common/config/userConfig.js";
import type { Telemetry } from "../../telemetry/telemetry.js";
import type { Session } from "../../lib.js";
import { generateConnectionInfoFromCliArgs } from "@mongosh/arg-parser";

export class ConfigResource extends ReactiveResource<UserConfig, readonly []> {
    constructor(session: Session, config: UserConfig, telemetry: Telemetry) {
        super({
            resourceConfiguration: {
                name: "config",
                uri: "config://config",
                config: {
                    description:
                        "Server configuration, supplied by the user either as environment variables or as startup arguments",
                },
            },
            options: {
                initial: { ...config },
                events: [],
            },
            session,
            config,
            telemetry,
        });
    }
    reduce(eventName: undefined, event: undefined): UserConfig {
        void eventName;
        void event;

        return this.current;
    }

    toOutput(): string {
        const connectionInfo = generateConnectionInfoFromCliArgs(this.current);
        const result = {
            telemetry: this.current.telemetry,
            logPath: this.current.logPath,
            connectionString: connectionInfo.connectionString
                ? "set; access to MongoDB tools are currently available to use"
                : "not set; before using any MongoDB tool, you need to configure a connection string, alternatively you can setup MongoDB Atlas access, more info at 'https://github.com/mongodb-js/mongodb-mcp-server'.",
            connectOptions: connectionInfo.driverOptions,
            atlas:
                this.current.apiClientId && this.current.apiClientSecret
                    ? "set; MongoDB Atlas tools are currently available to use"
                    : "not set; MongoDB Atlas tools are currently unavailable, to have access to MongoDB Atlas tools like creating clusters or connecting to clusters make sure to setup credentials, more info at 'https://github.com/mongodb-js/mongodb-mcp-server'.",
        };

        return JSON.stringify(result);
    }
}
