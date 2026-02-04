import type { Server } from "../server.js";
import type { Session } from "../common/session.js";
import type { UserConfig } from "../common/config/userConfig.js";
import type { Telemetry } from "../telemetry/telemetry.js";
import type { SessionEvents } from "../common/session.js";
import type { ReadResourceCallback, ResourceMetadata } from "@modelcontextprotocol/sdk/server/mcp.js";
import { LogId } from "../common/logger.js";

type PayloadOf<K extends keyof SessionEvents> = SessionEvents[K][0];

export type ResourceConfiguration = {
    name: string;
    uri: string;
    config: ResourceMetadata;
};

export type ReactiveResourceOptions<Value, RelevantEvents extends readonly (keyof SessionEvents)[]> = {
    initial: Value;
    events: RelevantEvents;
};

export abstract class ReactiveResource<Value, RelevantEvents extends readonly (keyof SessionEvents)[]> {
    protected server?: Server;
    protected session: Session;
    protected config: UserConfig;
    protected telemetry: Telemetry;

    protected current: Value;
    protected readonly name: string;
    protected readonly uri: string;
    protected readonly resourceConfig: ResourceMetadata;
    protected readonly events: RelevantEvents;

    constructor({
        resourceConfiguration,
        options,
        session,
        config,
        telemetry,
        current,
    }: {
        resourceConfiguration: ResourceConfiguration;
        options: ReactiveResourceOptions<Value, RelevantEvents>;
        session: Session;
        config: UserConfig;
        telemetry: Telemetry;
        current?: Value;
    }) {
        this.session = session;
        this.config = config;
        this.telemetry = telemetry;

        this.name = resourceConfiguration.name;
        this.uri = resourceConfiguration.uri;
        this.resourceConfig = resourceConfiguration.config;
        this.events = options.events;
        this.current = current ?? options.initial;

        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        for (const event of this.events) {
            this.session.on(event, (...args: SessionEvents[typeof event]) => {
                this.reduceApply(event, (args as unknown[])[0] as PayloadOf<typeof event>);
                void this.triggerUpdate();
            });
        }
    }

    public register(server: Server): void {
        this.server = server;
        this.server.mcpServer.registerResource(this.name, this.uri, this.resourceConfig, this.resourceCallback);
    }

    private resourceCallback: ReadResourceCallback = async (uri) => ({
        contents: [
            {
                text: await this.toOutput(),
                mimeType: "application/json",
                uri: uri.href,
            },
        ],
    });

    private triggerUpdate(): void {
        try {
            this.server?.sendResourceListChanged();
            this.server?.sendResourceUpdated(this.uri);
        } catch (error: unknown) {
            this.session.logger.warning({
                id: LogId.resourceUpdateFailure,
                context: "resource",
                message: `Could not send the latest resources to the client: ${error as string}`,
            });
        }
    }

    public reduceApply(eventName: RelevantEvents[number], ...event: PayloadOf<RelevantEvents[number]>[]): void {
        this.current = this.reduce(eventName, ...event);
    }

    protected abstract reduce(eventName: RelevantEvents[number], ...event: PayloadOf<RelevantEvents[number]>[]): Value;
    public abstract toOutput(): string | Promise<string>;
}
