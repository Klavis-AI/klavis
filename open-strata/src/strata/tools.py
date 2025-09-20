"""Shared tool implementations for Strata MCP Router."""

import json
import logging
from typing import List

import mcp.types as types

from .mcp_client_manager import MCPClientManager
from .utils.shared_search import UniversalToolSearcher

logger = logging.getLogger(__name__)

# Tool Names
TOOL_DISCOVER_SERVER_ACTIONS = "discover_server_actions"
TOOL_GET_ACTION_DETAILS = "get_action_details"
TOOL_EXECUTE_ACTION = "execute_action"
TOOL_SEARCH_DOCUMENTATION = "search_documentation"
TOOL_HANDLE_AUTH_FAILURE = "handle_auth_failure"


def get_tool_definitions(user_available_servers: List[str]) -> List[types.Tool]:
    """Get tool definitions for the available servers."""
    return [
        types.Tool(
            name=TOOL_DISCOVER_SERVER_ACTIONS,
            description="**PREFERRED STARTING POINT**: Discover available actions from servers based on user query.",
            inputSchema={
                "type": "object",
                "required": ["user_query", "server_names"],
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "Natural language user query to filter results.",
                    },
                    "server_names": {
                        "type": "array",
                        "items": {"type": "string", "enum": user_available_servers},
                        "description": "List of server names to discover actions from.",
                    },
                },
            },
        ),
        types.Tool(
            name=TOOL_GET_ACTION_DETAILS,
            description="Get detailed information about a specific action.",
            inputSchema={
                "type": "object",
                "required": ["server_name", "action_name"],
                "properties": {
                    "server_name": {
                        "type": "string",
                        "enum": user_available_servers,
                        "description": "The name of the server",
                    },
                    "action_name": {
                        "type": "string",
                        "description": "The name of the action/operation",
                    },
                },
            },
        ),
        types.Tool(
            name=TOOL_EXECUTE_ACTION,
            description="Execute a specific action with the provided parameters.",
            inputSchema={
                "type": "object",
                "required": ["server_name", "action_name"],
                "properties": {
                    "server_name": {
                        "type": "string",
                        "enum": user_available_servers,
                        "description": "The name of the server",
                    },
                    "action_name": {
                        "type": "string",
                        "description": "The name of the action/operation to execute",
                    },
                    "path_params": {
                        "type": "string",
                        "description": "JSON string containing path parameters",
                    },
                    "query_params": {
                        "type": "string",
                        "description": "JSON string containing query parameters",
                    },
                    "body_schema": {
                        "type": "string",
                        "description": "JSON string containing request body",
                        "default": "{}",
                    },
                },
            },
        ),
        types.Tool(
            name=TOOL_SEARCH_DOCUMENTATION,
            description="Search for server action documentations by keyword matching.",
            inputSchema={
                "type": "object",
                "required": ["query", "server_name"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords",
                    },
                    "server_name": {
                        "type": "string",
                        "enum": user_available_servers,
                        "description": "Name of the server to search within.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return. Default: 10",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name=TOOL_HANDLE_AUTH_FAILURE,
            description="Handle authentication failures that occur when executing actions.",
            inputSchema={
                "type": "object",
                "required": ["server_name", "intention"],
                "properties": {
                    "server_name": {
                        "type": "string",
                        "enum": user_available_servers,
                        "description": "The name of the server",
                    },
                    "intention": {
                        "type": "string",
                        "enum": ["get_auth_url", "save_auth_data"],
                        "description": "Action to take for authentication",
                    },
                    "auth_data": {
                        "type": "object",
                        "description": "Authentication data when saving",
                    },
                },
            },
        ),
    ]


async def execute_tool(
    name: str, arguments: dict, client_manager: MCPClientManager
) -> List[types.ContentBlock]:
    """Execute a tool with the given arguments."""
    try:
        result = None

        if name == TOOL_DISCOVER_SERVER_ACTIONS:
            user_query = arguments.get("user_query")
            server_names = arguments.get("server_names")

            # If no server names provided, use all available servers
            if not server_names:
                server_names = list(client_manager.active_clients.keys())

            # Discover actions from specified servers
            discovery_result = {}
            for server_name in server_names:
                try:
                    client = client_manager.get_client(server_name)
                    tools = await client.list_tools()

                    # Filter tools based on user query if provided
                    if user_query and tools:
                        tools_map = {server_name: tools}
                        searcher = UniversalToolSearcher(tools_map)
                        search_results = searcher.search(user_query, max_results=50)

                        filtered_action_names = []
                        for result_item in search_results:
                            for tool in tools:
                                if tool["name"] == result_item["name"]:
                                    filtered_action_names.append(tool["name"])
                                    break
                        discovery_result[server_name] = {
                            "action_count": len(filtered_action_names),
                            "actions": filtered_action_names,
                        }
                    else:
                        # Return only action count if no query
                        tool_list = tools or []
                        discovery_result[server_name] = {
                            "action_count": len(tool_list),
                            "actions": [tool["name"] for tool in tool_list],
                        }
                except KeyError:
                    discovery_result[server_name] = {
                        "error": f"Server '{server_name}' not found or not connected"
                    }
                except Exception as e:
                    logger.error(
                        f"Error discovering actions from {server_name}: {str(e)}"
                    )
                    discovery_result[server_name] = {"error": str(e)}

            result = {"servers": discovery_result}

        elif name == TOOL_GET_ACTION_DETAILS:
            server_name = arguments.get("server_name")
            action_name = arguments.get("action_name")

            if not server_name or not action_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Both server_name and action_name are required",
                    )
                ]

            try:
                client = client_manager.get_client(server_name)
                tools = await client.list_tools()

                action_found = None
                for tool in tools or []:
                    if tool["name"] == action_name:
                        action_found = tool
                        break

                if action_found:
                    result = {
                        "server": server_name,
                        "action": {
                            "name": action_found["name"],
                            "description": action_found["description"],
                            "inputSchema": action_found["inputSchema"],
                        },
                    }
                else:
                    result = {
                        "error": f"Action '{action_name}' not found in server '{server_name}'"
                    }
            except KeyError:
                result = {"error": f"Server '{server_name}' not found or not connected"}
            except Exception as e:
                logger.error(f"Error getting action details: {str(e)}")
                result = {"error": f"Error getting action details: {str(e)}"}

        elif name == TOOL_EXECUTE_ACTION:
            server_name = arguments.get("server_name")
            action_name = arguments.get("action_name")
            path_params = arguments.get("path_params")
            query_params = arguments.get("query_params")
            body_schema = arguments.get("body_schema", "{}")

            if not server_name or not action_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: server_name and action_name are required",
                    )
                ]

            try:
                client = client_manager.get_client(server_name)
                action_params = {}

                # Parse parameters if they're JSON strings
                for param_name, param_value in [
                    ("path_params", path_params),
                    ("query_params", query_params),
                    ("body_schema", body_schema),
                ]:
                    if param_value and param_value != "{}":
                        try:
                            if isinstance(param_value, str):
                                action_params.update(json.loads(param_value))
                            else:
                                action_params.update(param_value)
                        except json.JSONDecodeError:
                            return [
                                types.TextContent(
                                    type="text",
                                    text=f"Error: Invalid JSON in {param_name}",
                                )
                            ]

                # Call the tool on the MCP server
                return await client.call_tool(action_name, action_params)

            except KeyError:
                result = {"error": f"Server '{server_name}' not found or not connected"}
            except Exception as e:
                logger.error(f"Error executing action: {str(e)}")
                result = {"error": f"Error executing action: {str(e)}"}

        elif name == TOOL_SEARCH_DOCUMENTATION:
            query = arguments.get("query")
            server_name = arguments.get("server_name")
            max_results = arguments.get("max_results", 10)

            if not query or not server_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Both query and server_name are required",
                    )
                ]

            try:
                client = client_manager.get_client(server_name)
                tools = await client.list_tools()

                tools_map = {server_name: tools if tools else []}
                searcher = UniversalToolSearcher(tools_map)
                result = searcher.search(query, max_results=max_results)
            except KeyError:
                result = [
                    {"error": f"Server '{server_name}' not found or not connected"}
                ]
            except Exception as e:
                logger.error(f"Error searching documentation: {str(e)}")
                result = [{"error": f"Error searching documentation: {str(e)}"}]

        elif name == TOOL_HANDLE_AUTH_FAILURE:
            server_name = arguments.get("server_name")
            intention = arguments.get("intention")
            auth_data = arguments.get("auth_data")

            if not server_name or not intention:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Both server_name and intention are required",
                    )
                ]

            try:
                if intention == "get_auth_url":
                    result = {
                        "server": server_name,
                        "message": f"Authentication required for server '{server_name}'",
                        "instructions": "Please provide authentication credentials",
                        "required_fields": {"token": "Authentication token or API key"},
                    }
                elif intention == "save_auth_data":
                    if not auth_data:
                        return [
                            types.TextContent(
                                type="text",
                                text="Error: auth_data is required when intention is 'save_auth_data'",
                            )
                        ]
                    result = {
                        "server": server_name,
                        "status": "success",
                        "message": f"Authentication data saved for server '{server_name}'",
                    }
                else:
                    result = {"error": f"Invalid intention: '{intention}'"}
            except Exception as e:
                logger.error(f"Error handling auth failure: {str(e)}")
                result = {"error": f"Error handling auth failure: {str(e)}"}

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        # Convert result to TextContent
        return [
            types.TextContent(
                type="text",
                text=(
                    json.dumps(result, separators=(",", ":"))
                    if isinstance(result, (dict, list))
                    else str(result)
                ),
            )
        ]

    except Exception as e:
        logger.exception(f"Error executing tool {name}: {e}")
        return [
            types.TextContent(
                type="text", text=f"Error executing tool '{name}': {str(e)}"
            )
        ]
