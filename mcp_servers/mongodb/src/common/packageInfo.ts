import packageJson from "../../package.json" with { type: "json" };

export const packageInfo = {
    version: packageJson.version,
    mcpServerName: "MongoDB MCP Server",
};
