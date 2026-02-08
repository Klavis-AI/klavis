import path from "path";
import os from "os";
import argv from "yargs-parser";

import { ReadConcernLevel, ReadPreferenceMode, W } from "mongodb";

/**
 * Extracts connection string from the x-auth-data header.
 * The header value should be a base64-encoded JSON string containing
 * a `connection_string` field.
 *
 * Logic follows the same pattern as the resend MCP server's extractApiKey function:
 * 1. First check if CONNECTION_STRING env var is set - return it directly if present
 * 2. If not, check for x-auth-data header
 * 3. Decode from base64 to UTF-8
 * 4. Parse as JSON
 * 5. Return the connection_string field
 *
 * @param headers - Request headers containing x-auth-data
 * @returns The connection string if found, undefined otherwise
 */
export function extractConnectionStringFromAuthData(
    headers?: Record<string, string | string[] | undefined>
): string | undefined {
    // First check environment variable
    let authData = process.env.CONNECTION_STRING;

    if (authData) {
        return authData;
    }

    // If no env var, check for x-auth-data header
    if (!authData && headers?.["x-auth-data"]) {
        try {
            const headerValue = Array.isArray(headers["x-auth-data"])
                ? headers["x-auth-data"][0]
                : headers["x-auth-data"];
            authData = Buffer.from(headerValue as string, "base64").toString("utf8");
        } catch (error) {
            console.error("Error decoding x-auth-data base64:", error);
            return undefined;
        }
    }

    if (!authData) {
        return undefined;
    }

    try {
        const authDataJson = JSON.parse(authData);
        return authDataJson.connection_string ?? authDataJson.connectionString ?? undefined;
    } catch (error) {
        console.error("Error parsing x-auth-data JSON:", error);
        return undefined;
    }
}

export interface ConnectOptions {
    readConcern: ReadConcernLevel;
    readPreference: ReadPreferenceMode;
    writeConcern: W;
    timeoutMS: number;
}

// If we decide to support non-string config options, we'll need to extend the mechanism for parsing
// env variables.
export interface UserConfig {
    apiBaseUrl: string;
    apiClientId?: string;
    apiClientSecret?: string;
    telemetry: "enabled" | "disabled";
    logPath: string;
    connectionString?: string;
    connectOptions: ConnectOptions;
    disabledTools: Array<string>;
    readOnly?: boolean;
    indexCheck?: boolean;
    transport: "stdio" | "http";
    httpPort: number;
    httpHost: string;
    loggers: Array<"stderr" | "disk" | "mcp">;
    idleTimeoutMs: number;
    notificationTimeoutMs: number;
}

const defaults: UserConfig = {
    apiBaseUrl: "https://cloud.mongodb.com/",
    logPath: getLogPath(),
    connectOptions: {
        readConcern: "local",
        readPreference: "secondaryPreferred",
        writeConcern: "majority",
        timeoutMS: 30_000,
    },
    disabledTools: [],
    telemetry: "enabled",
    readOnly: false,
    indexCheck: false,
    transport: "stdio",
    httpPort: 3000,
    httpHost: "127.0.0.1",
    loggers: ["disk", "mcp"],
    idleTimeoutMs: 600000, // 10 minutes
    notificationTimeoutMs: 540000, // 9 minutes
};

export const config = {
    ...defaults,
    ...getEnvConfig(),
    ...getCliConfig(),
};

function getLogPath(): string {
    const localDataPath =
        process.platform === "win32"
            ? path.join(process.env.LOCALAPPDATA || process.env.APPDATA || os.homedir(), "mongodb")
            : path.join(os.homedir(), ".mongodb");

    const logPath = path.join(localDataPath, "mongodb-mcp", ".app-logs");

    return logPath;
}

// Gets the config supplied by the user as environment variables. The variable names
// are prefixed with `MDB_MCP_` and the keys match the UserConfig keys, but are converted
// to SNAKE_UPPER_CASE.
function getEnvConfig(): Partial<UserConfig> {
    function setValue(obj: Record<string, unknown>, path: string[], value: string): void {
        const currentField = path.shift();
        if (!currentField) {
            return;
        }
        if (path.length === 0) {
            const numberValue = Number(value);
            if (!isNaN(numberValue)) {
                obj[currentField] = numberValue;
                return;
            }

            const booleanValue = value.toLocaleLowerCase();
            if (booleanValue === "true" || booleanValue === "false") {
                obj[currentField] = booleanValue === "true";
                return;
            }

            // Try to parse an array of values
            if (value.indexOf(",") !== -1) {
                obj[currentField] = value.split(",").map((v) => v.trim());
                return;
            }

            obj[currentField] = value;
            return;
        }

        if (!obj[currentField]) {
            obj[currentField] = {};
        }

        setValue(obj[currentField] as Record<string, unknown>, path, value);
    }

    const result: Record<string, unknown> = {};
    const mcpVariables = Object.entries(process.env).filter(
        ([key, value]) => value !== undefined && key.startsWith("MDB_MCP_")
    ) as [string, string][];
    for (const [key, value] of mcpVariables) {
        const fieldPath = key
            .replace("MDB_MCP_", "")
            .split(".")
            .map((part) => SNAKE_CASE_toCamelCase(part));

        setValue(result, fieldPath, value);
    }

    return result;
}

function SNAKE_CASE_toCamelCase(str: string): string {
    return str.toLowerCase().replace(/([-_][a-z])/g, (group) => group.toUpperCase().replace("_", ""));
}

// Reads the cli args and parses them into a UserConfig object.
function getCliConfig() {
    return argv(process.argv.slice(2), {
        array: ["disabledTools", "loggers"],
    }) as unknown as Partial<UserConfig>;
}
