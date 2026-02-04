import { getDeviceId } from "@mongodb-js/device-id";
import type { LoggerBase } from "../common/logger.js";
import { LogId } from "../common/logger.js";

export const DEVICE_ID_TIMEOUT = 3000;

export class DeviceId {
    private static readonly UnknownDeviceId = Promise.resolve("unknown");

    private deviceIdPromise: Promise<string>;
    private abortController: AbortController;
    private logger: LoggerBase;
    private readonly getMachineId: () => Promise<string>;
    private timeout: number;

    private constructor(logger: LoggerBase, timeout: number = DEVICE_ID_TIMEOUT) {
        this.logger = logger;
        this.timeout = timeout;
        this.getMachineId = async (): Promise<string> => {
            const nodeMachineId = await import("node-machine-id");
            const machineId = nodeMachineId.default?.machineId || nodeMachineId.machineId;
            return machineId(true);
        };
        this.abortController = new AbortController();

        this.deviceIdPromise = DeviceId.UnknownDeviceId;
    }

    private initialize(): void {
        this.deviceIdPromise = getDeviceId({
            getMachineId: this.getMachineId,
            onError: (reason, error) => {
                this.handleDeviceIdError(reason, String(error));
            },
            timeout: this.timeout,
            abortSignal: this.abortController.signal,
        });
    }

    public static create(logger: LoggerBase, timeout?: number): DeviceId {
        const instance = new DeviceId(logger, timeout ?? DEVICE_ID_TIMEOUT);
        instance.initialize();

        return instance;
    }

    /**
     * Closes the device ID calculation promise and abort controller.
     */
    public close(): void {
        this.abortController.abort();
    }

    /**
     * Gets the device ID, waiting for the calculation to complete if necessary.
     * @returns Promise that resolves to the device ID string
     */
    public get(): Promise<string> {
        return this.deviceIdPromise;
    }

    private handleDeviceIdError(reason: string, error: string): void {
        this.deviceIdPromise = DeviceId.UnknownDeviceId;

        switch (reason) {
            case "resolutionError":
                this.logger.debug({
                    id: LogId.deviceIdResolutionError,
                    context: "deviceId",
                    message: `Resolution error: ${String(error)}`,
                });
                break;
            case "timeout":
                this.logger.debug({
                    id: LogId.deviceIdTimeout,
                    context: "deviceId",
                    message: "Device ID retrieval timed out",
                    noRedaction: true,
                });
                break;
            case "abort":
                // No need to log in the case of 'abort' errors
                break;
        }
    }
}
