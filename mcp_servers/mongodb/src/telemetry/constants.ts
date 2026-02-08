import { packageInfo } from "../common/packageInfo.js";
import { type CommonStaticProperties } from "./types.js";

/**
 * Machine-specific metadata formatted for telemetry
 */
export const MACHINE_METADATA: CommonStaticProperties = {
    mcp_server_version: packageInfo.version,
    mcp_server_name: packageInfo.mcpServerName,
    platform: process.platform,
    arch: process.arch,
    os_type: process.platform,
    os_version: process.version,
} as const;
