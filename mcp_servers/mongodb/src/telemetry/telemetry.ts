import type { Session } from "../common/session.js";
import type { BaseEvent, CommonProperties } from "./types.js";
import type { UserConfig } from "../common/config/userConfig.js";
import { LogId } from "../common/logger.js";
import type { ApiClient } from "../common/atlas/apiClient.js";
import { MACHINE_METADATA } from "./constants.js";
import { EventCache } from "./eventCache.js";
import { detectContainerEnv } from "../helpers/container.js";
import type { DeviceId } from "../helpers/deviceId.js";
import { EventEmitter } from "events";
import { redact } from "mongodb-redact";

type EventResult = {
    success: boolean;
    error?: Error;
};

export interface TelemetryEvents {
    "events-emitted": [];
    "events-send-failed": [];
    "events-skipped": [];
}

export class Telemetry {
    private isBufferingEvents: boolean = true;
    /** Resolves when the setup is complete or a timeout occurs */
    public setupPromise: Promise<[string, boolean]> | undefined;
    public readonly events: EventEmitter<TelemetryEvents> = new EventEmitter();

    private eventCache: EventCache;
    private deviceId: DeviceId;

    private constructor(
        private readonly session: Session,
        private readonly userConfig: UserConfig,
        private readonly commonProperties: CommonProperties,
        { eventCache, deviceId }: { eventCache: EventCache; deviceId: DeviceId }
    ) {
        this.eventCache = eventCache;
        this.deviceId = deviceId;
    }

    static create(
        session: Session,
        userConfig: UserConfig,
        deviceId: DeviceId,
        {
            commonProperties = {},
            eventCache = EventCache.getInstance(),
        }: {
            commonProperties?: Partial<CommonProperties>;
            eventCache?: EventCache;
        } = {}
    ): Telemetry {
        const mergedProperties = {
            ...MACHINE_METADATA,
            ...commonProperties,
        };
        const instance = new Telemetry(session, userConfig, mergedProperties, {
            eventCache,
            deviceId,
        });

        void instance.setup();
        return instance;
    }

    private async setup(): Promise<void> {
        if (!this.isTelemetryEnabled()) {
            this.session.logger.info({
                id: LogId.telemetryEmitFailure,
                context: "telemetry",
                message: "Telemetry is disabled.",
                noRedaction: true,
            });
            return;
        }

        this.setupPromise = Promise.all([this.deviceId.get(), detectContainerEnv()]);
        const [deviceIdValue, containerEnv] = await this.setupPromise;

        this.commonProperties.device_id = deviceIdValue;
        this.commonProperties.is_container_env = containerEnv ? "true" : "false";

        this.isBufferingEvents = false;
    }

    public async close(): Promise<void> {
        this.isBufferingEvents = false;

        this.session.logger.debug({
            id: LogId.telemetryClose,
            message: `Closing telemetry and flushing ${this.eventCache.size} events`,
            context: "telemetry",
        });

        // Wait up to 5 seconds for events to be sent before closing, but don't throw if it times out
        const flushMaxWaitTime = 5000;
        let flushTimeout: NodeJS.Timeout | undefined;
        await Promise.race([
            new Promise<void>((resolve) => {
                flushTimeout = setTimeout(() => {
                    this.session.logger.debug({
                        id: LogId.telemetryClose,
                        message: `Failed to flush remaining events within ${flushMaxWaitTime}ms timeout`,
                        context: "telemetry",
                    });
                    resolve();
                }, flushMaxWaitTime);
                // This is Node-specific and can cause issues when running in electron otherwise. See https://github.com/electron/electron/issues/21162
                if (typeof flushTimeout.unref === "function") {
                    flushTimeout.unref();
                }
            }),
            this.emit([]),
        ]);

        clearTimeout(flushTimeout);
    }

    /**
     * Emits events through the telemetry pipeline
     * @param events - The events to emit
     */
    public emitEvents(events: BaseEvent[]): void {
        if (!this.isTelemetryEnabled()) {
            this.events.emit("events-skipped");
            return;
        }
        // Don't wait for events to be sent - we should not block regular server
        // operations on telemetry
        void this.emit(events);
    }

    /**
     * Gets the common properties for events
     * @returns Object containing common properties for all events
     */
    public getCommonProperties(): CommonProperties {
        return {
            ...this.commonProperties,
            transport: this.userConfig.transport,
            mcp_client_version: this.session.mcpClient?.version,
            mcp_client_name: this.session.mcpClient?.name,
            session_id: this.session.sessionId,
            config_atlas_auth: this.session.apiClient?.isAuthConfigured() ? "true" : "false",
            config_connection_string: this.userConfig.connectionString ? "true" : "false",
        };
    }

    /**
     * Checks if telemetry is currently enabled
     * This is a method rather than a constant to capture runtime config changes
     *
     * Follows the Console Do Not Track standard (https://consoledonottrack.com/)
     * by respecting the DO_NOT_TRACK environment variable
     */
    public isTelemetryEnabled(): boolean {
        // Check if telemetry is explicitly disabled in config
        if (this.userConfig.telemetry === "disabled") {
            return false;
        }

        const doNotTrack = "DO_NOT_TRACK" in process.env;
        return !doNotTrack;
    }

    /**
     * Attempts to emit events through authenticated and unauthenticated clients
     * Falls back to caching if both attempts fail
     */
    private async emit(events: BaseEvent[]): Promise<void> {
        if (this.isBufferingEvents) {
            this.eventCache.appendEvents(events);
            return;
        }

        // If no API client is available, cache the events
        if (!this.session.apiClient) {
            this.eventCache.appendEvents(events);
            return;
        }

        try {
            const cachedEvents = this.eventCache.getEvents();
            const allEvents = [...cachedEvents.map((e) => e.event), ...events];

            this.session.logger.debug({
                id: LogId.telemetryEmitStart,
                context: "telemetry",
                message: `Attempting to send ${allEvents.length} events (${cachedEvents.length} cached)`,
            });

            const result = await this.sendEvents(this.session.apiClient, allEvents);
            if (result.success) {
                this.eventCache.removeEvents(cachedEvents.map((e) => e.id));
                this.session.logger.debug({
                    id: LogId.telemetryEmitSuccess,
                    context: "telemetry",
                    message: `Sent ${allEvents.length} events successfully: ${JSON.stringify(allEvents)}`,
                });
                this.events.emit("events-emitted");
                return;
            }

            this.session.logger.debug({
                id: LogId.telemetryEmitFailure,
                context: "telemetry",
                message: `Error sending event to client: ${result.error instanceof Error ? result.error.message : String(result.error)}`,
            });
            this.eventCache.appendEvents(events);
            this.events.emit("events-send-failed");
        } catch (error) {
            this.session.logger.debug({
                id: LogId.telemetryEmitFailure,
                context: "telemetry",
                message: `Error emitting telemetry events: ${error instanceof Error ? error.message : String(error)}`,
                noRedaction: true,
            });
            this.events.emit("events-send-failed");
        }
    }

    /**
     * Attempts to send events through the provided API client.
     * Events are redacted before being sent to ensure no sensitive data is transmitted
     */
    private async sendEvents(client: ApiClient, events: BaseEvent[]): Promise<EventResult> {
        try {
            await client.sendEvents(
                events.map((event) => ({
                    ...event,
                    properties: {
                        ...redact(this.getCommonProperties(), this.session.keychain.allSecrets),
                        ...redact(event.properties, this.session.keychain.allSecrets),
                    },
                }))
            );
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error : new Error(String(error)),
            };
        }
    }
}
