import { Session } from "../common/session.js";
import { BaseEvent, CommonProperties } from "./types.js";
import { UserConfig } from "../common/config.js";
import logger, { LogId } from "../common/logger.js";
import { ApiClient } from "../common/atlas/apiClient.js";
import { MACHINE_METADATA } from "./constants.js";
import { EventCache } from "./eventCache.js";
import nodeMachineId from "node-machine-id";
import { getDeviceId } from "@mongodb-js/device-id";
import { detectContainerEnv } from "../helpers/container.js";

type EventResult = {
    success: boolean;
    error?: Error;
};

export const DEVICE_ID_TIMEOUT = 3000;

export class Telemetry {
    private isBufferingEvents: boolean = true;
    /** Resolves when the setup is complete or a timeout occurs */
    public setupPromise: Promise<[string, boolean]> | undefined;
    private deviceIdAbortController = new AbortController();
    private eventCache: EventCache;
    private getRawMachineId: () => Promise<string>;

    private constructor(
        private readonly session: Session,
        private readonly userConfig: UserConfig,
        private readonly commonProperties: CommonProperties,
        { eventCache, getRawMachineId }: { eventCache: EventCache; getRawMachineId: () => Promise<string> }
    ) {
        this.eventCache = eventCache;
        this.getRawMachineId = getRawMachineId;
    }

    static create(
        session: Session,
        userConfig: UserConfig,
        {
            commonProperties = { ...MACHINE_METADATA },
            eventCache = EventCache.getInstance(),
            getRawMachineId = () => nodeMachineId.machineId(true),
        }: {
            eventCache?: EventCache;
            getRawMachineId?: () => Promise<string>;
            commonProperties?: CommonProperties;
        } = {}
    ): Telemetry {
        const instance = new Telemetry(session, userConfig, commonProperties, { eventCache, getRawMachineId });

        void instance.setup();
        return instance;
    }

    private async setup(): Promise<void> {
        if (!this.isTelemetryEnabled()) {
            return;
        }
        this.setupPromise = Promise.all([
            getDeviceId({
                getMachineId: () => this.getRawMachineId(),
                onError: (reason, error) => {
                    switch (reason) {
                        case "resolutionError":
                            logger.debug(LogId.telemetryDeviceIdFailure, "telemetry", String(error));
                            break;
                        case "timeout":
                            logger.debug(LogId.telemetryDeviceIdTimeout, "telemetry", "Device ID retrieval timed out");
                            break;
                        case "abort":
                            // No need to log in the case of aborts
                            break;
                    }
                },
                abortSignal: this.deviceIdAbortController.signal,
            }),
            detectContainerEnv(),
        ]);

        const [deviceId, containerEnv] = await this.setupPromise;

        this.commonProperties.device_id = deviceId;
        this.commonProperties.is_container_env = containerEnv;

        this.isBufferingEvents = false;
    }

    public async close(): Promise<void> {
        this.deviceIdAbortController.abort();
        this.isBufferingEvents = false;
        await this.emitEvents(this.eventCache.getEvents());
    }

    /**
     * Emits events through the telemetry pipeline
     * @param events - The events to emit
     */
    public async emitEvents(events: BaseEvent[]): Promise<void> {
        try {
            if (!this.isTelemetryEnabled()) {
                logger.info(LogId.telemetryEmitFailure, "telemetry", `Telemetry is disabled.`);
                return;
            }

            await this.emit(events);
        } catch {
            logger.debug(LogId.telemetryEmitFailure, "telemetry", `Error emitting telemetry events.`);
        }
    }

    /**
     * Gets the common properties for events
     * @returns Object containing common properties for all events
     */
    public getCommonProperties(): CommonProperties {
        return {
            ...this.commonProperties,
            transport: this.userConfig.transport,
            mcp_client_version: this.session.agentRunner?.version,
            mcp_client_name: this.session.agentRunner?.name,
            session_id: this.session.sessionId,
            config_atlas_auth: this.session.apiClient.hasCredentials() ? "true" : "false",
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

        const cachedEvents = this.eventCache.getEvents();
        const allEvents = [...cachedEvents, ...events];

        logger.debug(
            LogId.telemetryEmitStart,
            "telemetry",
            `Attempting to send ${allEvents.length} events (${cachedEvents.length} cached)`
        );

        const result = await this.sendEvents(this.session.apiClient, allEvents);
        if (result.success) {
            this.eventCache.clearEvents();
            logger.debug(
                LogId.telemetryEmitSuccess,
                "telemetry",
                `Sent ${allEvents.length} events successfully: ${JSON.stringify(allEvents, null, 2)}`
            );
            return;
        }

        logger.debug(
            LogId.telemetryEmitFailure,
            "telemetry",
            `Error sending event to client: ${result.error instanceof Error ? result.error.message : String(result.error)}`
        );
        this.eventCache.appendEvents(events);
    }

    /**
     * Attempts to send events through the provided API client
     */
    private async sendEvents(client: ApiClient, events: BaseEvent[]): Promise<EventResult> {
        try {
            await client.sendEvents(
                events.map((event) => ({
                    ...event,
                    properties: { ...this.getCommonProperties(), ...event.properties },
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
