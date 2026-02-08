/**
 * Result type constants for telemetry events
 */
export type TelemetryResult = "success" | "failure";
export type ServerCommand = "start" | "stop";
export type TelemetryBoolSet = "true" | "false";

/**
 * Base interface for all events
 */
export type TelemetryEvent<T> = {
    timestamp: string;
    source: "mdbmcp";
    properties: T & {
        component: string;
        duration_ms: number;
        result: TelemetryResult;
        category: string;
    };
};

export type BaseEvent = TelemetryEvent<unknown>;

/**
 * Interface for tool events
 */
export type ToolEventProperties = {
    command: string;
    error_code?: string;
    error_type?: string;
    project_id?: string;
    org_id?: string;
    cluster_name?: string;
    is_atlas?: boolean;
};

export type ToolEvent = TelemetryEvent<ToolEventProperties>;
/**
 * Interface for server events
 */
export type ServerEventProperties = {
    command: ServerCommand;
    reason?: string;
    startup_time_ms?: number;
    runtime_duration_ms?: number;
    read_only_mode?: boolean;
    disabled_tools?: string[];
};

export type ServerEvent = TelemetryEvent<ServerEventProperties>;

/**
 * Interface for static properties, they can be fetched once and reused.
 */
export type CommonStaticProperties = {
    mcp_server_version: string;
    mcp_server_name: string;
    platform: string;
    arch: string;
    os_type: string;
    os_version?: string;
};

/**
 * Common properties for all events that might change.
 */
export type CommonProperties = {
    device_id?: string;
    is_container_env?: boolean;
    mcp_client_version?: string;
    mcp_client_name?: string;
    transport?: "stdio" | "http";
    config_atlas_auth?: TelemetryBoolSet;
    config_connection_string?: TelemetryBoolSet;
    session_id?: string;
} & CommonStaticProperties;
