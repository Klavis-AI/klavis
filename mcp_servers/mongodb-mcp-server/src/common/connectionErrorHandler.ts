import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { ErrorCodes, type MongoDBError } from "./errors.js";
import type { AnyConnectionState } from "./connectionManager.js";
import type { ToolBase } from "../tools/tool.js";

export type ConnectionErrorHandler = (
    error: MongoDBError<ErrorCodes.NotConnectedToMongoDB | ErrorCodes.MisconfiguredConnectionString>,
    additionalContext: ConnectionErrorHandlerContext
) => ConnectionErrorUnhandled | ConnectionErrorHandled;

export type ConnectionErrorHandlerContext = { availableTools: ToolBase[]; connectionState: AnyConnectionState };
export type ConnectionErrorUnhandled = { errorHandled: false };
export type ConnectionErrorHandled = { errorHandled: true; result: CallToolResult };

export const connectionErrorHandler: ConnectionErrorHandler = (error, { availableTools, connectionState }) => {
    const connectTools = availableTools
        .filter((t) => t.operationType === "connect" && t.isEnabled())
        .sort((a, b) => a.category.localeCompare(b.category)); // Sort Atlas tools before MongoDB tools

    // Find what Atlas connect tools are available and suggest when the LLM should to use each. If no Atlas tools are found, return a suggestion for the MongoDB connect tool.
    const atlasConnectTool = connectTools?.find((t) => t.category === "atlas");
    const atlasLocalConnectTool = connectTools?.find((t) => t.category === "atlas-local");

    const llmConnectHint = ((): string => {
        const hints: string[] = [];

        if (atlasConnectTool) {
            hints.push(
                `Note to LLM: prefer using the "${atlasConnectTool.name}" tool to connect to an Atlas cluster over using a connection string. Make sure to ask the user to specify a cluster name they want to connect to or ask them if they want to use the "list-clusters" tool to list all their clusters. Do not invent cluster names or connection strings unless the user has explicitly specified them. If they've previously connected to MongoDB using MCP, you can ask them if they want to reconnect using the same cluster/connection.`
            );
        }

        if (atlasLocalConnectTool) {
            hints.push(
                `Note to LLM: For MongoDB Atlas Local deployments, ask the user to either provide a connection string, specify a deployment name, or use "atlas-local-list-deployments" to show available local deployments. If a deployment name is provided, prefer using the "${atlasLocalConnectTool.name}" tool. If a connection string is provided, prefer using the "connect" tool. Do not invent deployment names or connection strings unless the user has explicitly specified them. If they've previously connected to a MongoDB Atlas Local deployment using MCP, you can ask them if they want to reconnect using the same deployment.`
            );
        }

        return hints.length > 0
            ? hints.join("\n")
            : "Note to LLM: do not invent connection strings and explicitly ask the user to provide one. If they have previously connected to MongoDB using MCP, you can ask them if they want to reconnect using the same connection string.";
    })();

    const connectToolsNames = connectTools?.map((t) => `"${t.name}"`).join(", ");
    const additionalPromptForConnectivity: { type: "text"; text: string }[] = [];

    if (connectionState.tag === "connecting" && connectionState.oidcConnectionType) {
        additionalPromptForConnectivity.push({
            type: "text",
            text: `The user needs to finish their OIDC connection by opening '${connectionState.oidcLoginUrl}' in the browser and use the following user code: '${connectionState.oidcUserCode}'`,
        });
    } else {
        additionalPromptForConnectivity.push({
            type: "text",
            text: connectToolsNames
                ? `Please use one of the following tools: ${connectToolsNames} to connect to a MongoDB instance or update the MCP server configuration to include a connection string. ${llmConnectHint}`
                : "There are no tools available to connect. Please update the configuration to include a connection string and restart the server.",
        });
    }

    switch (error.code) {
        case ErrorCodes.NotConnectedToMongoDB:
            return {
                errorHandled: true,
                result: {
                    content: [
                        {
                            type: "text",
                            text: "You need to connect to a MongoDB instance before you can access its data.",
                        },
                        ...additionalPromptForConnectivity,
                    ],
                    isError: true,
                },
            };
        case ErrorCodes.MisconfiguredConnectionString:
            return {
                errorHandled: true,
                result: {
                    content: [
                        {
                            type: "text",
                            text: "The configured connection string is not valid. Please check the connection string and confirm it points to a valid MongoDB instance.",
                        },
                        {
                            type: "text",
                            text: connectTools
                                ? `Alternatively, you can use one of the following tools: ${connectToolsNames} to connect to a MongoDB instance. ${llmConnectHint}`
                                : "Please update the configuration to use a valid connection string and restart the server.",
                        },
                    ],
                    isError: true,
                },
            };

        default:
            return { errorHandled: false };
    }
};
