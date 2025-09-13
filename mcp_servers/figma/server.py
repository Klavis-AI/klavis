import os
import json
import logging
import asyncio
from typing import Any, Dict

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from tools import (
    figma_token_context,
    get_current_user,
    test_figma_connection,
    get_file,
    get_file_nodes,
    get_file_images,
    get_file_versions,
    get_team_projects,
    get_project_files,
    get_file_comments,
    post_file_comment,
    delete_comment,
    get_local_variables,
    get_published_variables,
    post_variables,
    get_dev_resources,
    post_dev_resources,
    put_dev_resource,
    delete_dev_resource,
    get_team_webhooks,
    post_webhook,
    put_webhook,
    delete_webhook,
    get_library_analytics,
)

# Load env early
load_dotenv()

logger = logging.getLogger("figma-mcp-server")
logging.basicConfig(level=logging.INFO)

FIGMA_API_KEY = os.getenv("FIGMA_API_KEY") or ""

async def run_server(log_level: str = "INFO"):
    """Run the Figma MCP server with stdio transport for Claude Desktop."""
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Set the API key in context
    if FIGMA_API_KEY:
        figma_token_context.set(FIGMA_API_KEY)
        logger.info("Figma API key configured")
    else:
        logger.warning("No Figma API key found in environment")
    
    app = Server("figma-mcp-server")

    # ----------------------------- Tool Registry -----------------------------#
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available Figma tools."""
        tools = [
            # Auth/Account tools
            types.Tool(
                name="figma_test_connection",
                description="Test Figma Connection - verify API authentication is working correctly.",
                inputSchema={"type": "object", "properties": {}}
            ),
            types.Tool(
                name="figma_get_current_user",
                description="Get Current User - retrieve information about the authenticated user.",
                inputSchema={"type": "object", "properties": {}}
            ),
            
            # File management tools
            types.Tool(
                name="figma_get_file",
                description="Get File Content - retrieve the full content of a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "version": {"type": "string", "description": "Specific version to retrieve"},
                        "ids": {"type": "string", "description": "Comma-separated list of node IDs to filter"},
                        "depth": {"type": "integer", "description": "How deep to traverse the document tree", "minimum": 1},
                        "geometry": {"type": "string", "enum": ["paths", "no_geometry"], "description": "Whether to include geometry data"},
                        "plugin_data": {"type": "string", "description": "Plugin data to include"},
                        "branch_data": {"type": "boolean", "description": "Whether to include branch data"}
                    }
                }
            ),
            types.Tool(
                name="figma_get_file_nodes",
                description="Get Specific File Nodes - retrieve specific nodes from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key", "ids"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "ids": {"type": "string", "description": "Comma-separated list of node IDs"},
                        "version": {"type": "string", "description": "Specific version to retrieve"},
                        "depth": {"type": "integer", "description": "How deep to traverse the node tree", "minimum": 1},
                        "geometry": {"type": "string", "enum": ["paths", "no_geometry"], "description": "Whether to include geometry data"},
                        "plugin_data": {"type": "string", "description": "Plugin data to include"}
                    }
                }
            ),
            types.Tool(
                name="figma_get_file_images",
                description="Get File Images - export images from specific nodes in a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key", "ids"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "ids": {"type": "string", "description": "Comma-separated list of node IDs to export"},
                        "scale": {"type": "number", "description": "Scale factor for export", "minimum": 0.01, "maximum": 4},
                        "format": {"type": "string", "enum": ["jpg", "png", "svg", "pdf"], "description": "Export format"},
                        "svg_include_id": {"type": "boolean", "description": "Include node IDs in SVG"},
                        "svg_simplify_stroke": {"type": "boolean", "description": "Simplify strokes in SVG"},
                        "use_absolute_bounds": {"type": "boolean", "description": "Use absolute bounds for export"},
                        "version": {"type": "string", "description": "Specific version to export"}
                    }
                }
            ),
            types.Tool(
                name="figma_get_file_versions",
                description="Get File Versions - retrieve version history for a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"}
                    }
                }
            ),
            
            # Project management tools
            types.Tool(
                name="figma_get_team_projects",
                description="Get Team Projects - retrieve all projects for a team (requires team ID).",
                inputSchema={
                    "type": "object",
                    "required": ["team_id"],
                    "properties": {
                        "team_id": {"type": "string", "description": "The team ID (from Figma team URL)"}
                    }
                }
            ),
            types.Tool(
                name="figma_get_project_files",
                description="Get Project Files - retrieve all files in a project (requires project ID).",
                inputSchema={
                    "type": "object",
                    "required": ["project_id"],
                    "properties": {
                        "project_id": {"type": "string", "description": "The project ID"},
                        "branch_data": {"type": "boolean", "description": "Whether to include branch data"}
                    }
                }
            ),
            
            # Comment management tools
            types.Tool(
                name="figma_get_file_comments",
                description="Get File Comments - retrieve comments from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "as_md": {"type": "boolean", "description": "Return comments as markdown"}
                    }
                }
            ),
            types.Tool(
                name="figma_post_file_comment",
                description="Post File Comment - add a comment to a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key", "message", "client_meta"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "message": {"type": "string", "description": "The comment message"},
                        "client_meta": {"type": "object", "description": "Client metadata including x, y coordinates and node_id"},
                        "comment_id": {"type": "string", "description": "Parent comment ID for replies"}
                    }
                }
            ),
            types.Tool(
                name="figma_delete_comment",
                description="Delete Comment - remove a comment from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["comment_id"],
                    "properties": {
                        "comment_id": {"type": "string", "description": "The comment ID to delete"}
                    }
                }
            ),
            
            # Variables (Design Tokens) management tools
            types.Tool(
                name="figma_get_local_variables",
                description="Get Local Variables - retrieve local variables from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"}
                    }
                }
            ),
            types.Tool(
                name="figma_get_published_variables",
                description="Get Published Variables - retrieve published variables from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"}
                    }
                }
            ),
            types.Tool(
                name="figma_post_variables",
                description="Create/Update Variables - create or update variables in a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key", "variableCollections", "variables"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "variableCollections": {"type": "array", "description": "Array of variable collections to create/update"},
                        "variables": {"type": "array", "description": "Array of variables to create/update"}
                    }
                }
            ),
            
            # Dev Resources management tools
            types.Tool(
                name="figma_get_dev_resources",
                description="Get Dev Resources - retrieve dev resources from a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "node_id": {"type": "string", "description": "Filter by specific node ID"}
                    }
                }
            ),
            types.Tool(
                name="figma_post_dev_resources",
                description="Create Dev Resources - add dev resources to a Figma file.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key", "dev_resources"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key (from Figma URL)"},
                        "dev_resources": {"type": "array", "description": "Array of dev resources to create"}
                    }
                }
            ),
            types.Tool(
                name="figma_put_dev_resource",
                description="Update Dev Resource - modify an existing dev resource.",
                inputSchema={
                    "type": "object",
                    "required": ["dev_resource_id"],
                    "properties": {
                        "dev_resource_id": {"type": "string", "description": "The dev resource ID"},
                        "name": {"type": "string", "description": "New name for the dev resource"},
                        "url": {"type": "string", "description": "New URL for the dev resource"}
                    }
                }
            ),
            types.Tool(
                name="figma_delete_dev_resource",
                description="Delete Dev Resource - remove a dev resource from Figma.",
                inputSchema={
                    "type": "object",
                    "required": ["dev_resource_id"],
                    "properties": {
                        "dev_resource_id": {"type": "string", "description": "The dev resource ID to delete"}
                    }
                }
            ),
            
            # Webhook management tools
            types.Tool(
                name="figma_get_team_webhooks",
                description="Get Team Webhooks - retrieve webhooks for a team (requires team ID).",
                inputSchema={
                    "type": "object",
                    "required": ["team_id"],
                    "properties": {
                        "team_id": {"type": "string", "description": "The team ID (from Figma team URL)"}
                    }
                }
            ),
            types.Tool(
                name="figma_post_webhook",
                description="Create Webhook - create a new webhook for team events.",
                inputSchema={
                    "type": "object",
                    "required": ["team_id", "event_type", "endpoint"],
                    "properties": {
                        "team_id": {"type": "string", "description": "The team ID (from Figma team URL)"},
                        "event_type": {"type": "string", "enum": ["PING", "FILE_UPDATE", "FILE_DELETE", "FILE_VERSION_UPDATE", "LIBRARY_PUBLISH"], "description": "Type of event to listen for"},
                        "endpoint": {"type": "string", "description": "HTTP endpoint to receive webhook notifications"},
                        "passcode": {"type": "string", "description": "Passcode for webhook verification"},
                        "description": {"type": "string", "description": "Description of the webhook"}
                    }
                }
            ),
            types.Tool(
                name="figma_put_webhook",
                description="Update Webhook - modify an existing webhook.",
                inputSchema={
                    "type": "object",
                    "required": ["webhook_id"],
                    "properties": {
                        "webhook_id": {"type": "string", "description": "The webhook ID"},
                        "event_type": {"type": "string", "enum": ["PING", "FILE_UPDATE", "FILE_DELETE", "FILE_VERSION_UPDATE", "LIBRARY_PUBLISH"], "description": "Type of event to listen for"},
                        "endpoint": {"type": "string", "description": "HTTP endpoint to receive webhook notifications"},
                        "passcode": {"type": "string", "description": "Passcode for webhook verification"},
                        "description": {"type": "string", "description": "Description of the webhook"}
                    }
                }
            ),
            types.Tool(
                name="figma_delete_webhook",
                description="Delete Webhook - remove a webhook.",
                inputSchema={
                    "type": "object",
                    "required": ["webhook_id"],
                    "properties": {
                        "webhook_id": {"type": "string", "description": "The webhook ID to delete"}
                    }
                }
            ),
            
            # Library Analytics tools
            types.Tool(
                name="figma_get_library_analytics",
                description="Get Library Analytics - retrieve usage analytics for a published library.",
                inputSchema={
                    "type": "object",
                    "required": ["file_key"],
                    "properties": {
                        "file_key": {"type": "string", "description": "The file key of a published library (from Figma URL)"}
                    }
                }
            ),
        ]
        
        logger.info(f"Returning {len(tools)} tools")
        return tools

    # ---------------------------- Tool Dispatcher ----------------------------#
    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
        logger.info(f"Calling tool: {name}")
        
        try:
            # Auth/Account tools
            if name == "figma_test_connection":
                result = await test_figma_connection()
            elif name == "figma_get_current_user":
                result = await get_current_user()
            
            # File tools
            elif name == "figma_get_file":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_file(
                    file_key=arguments["file_key"],
                    version=arguments.get("version"),
                    ids=arguments.get("ids"),
                    depth=arguments.get("depth"),
                    geometry=arguments.get("geometry"),
                    plugin_data=arguments.get("plugin_data"),
                    branch_data=arguments.get("branch_data")
                )
            elif name == "figma_get_file_nodes":
                if not all([arguments.get("file_key"), arguments.get("ids")]):
                    raise ValueError("Missing required arguments: file_key and ids")
                result = await get_file_nodes(
                    file_key=arguments["file_key"],
                    ids=arguments["ids"],
                    version=arguments.get("version"),
                    depth=arguments.get("depth"),
                    geometry=arguments.get("geometry"),
                    plugin_data=arguments.get("plugin_data")
                )
            elif name == "figma_get_file_images":
                if not all([arguments.get("file_key"), arguments.get("ids")]):
                    raise ValueError("Missing required arguments: file_key and ids")
                result = await get_file_images(
                    file_key=arguments["file_key"],
                    ids=arguments["ids"],
                    scale=arguments.get("scale"),
                    format=arguments.get("format"),
                    svg_include_id=arguments.get("svg_include_id"),
                    svg_simplify_stroke=arguments.get("svg_simplify_stroke"),
                    use_absolute_bounds=arguments.get("use_absolute_bounds"),
                    version=arguments.get("version")
                )
            elif name == "figma_get_file_versions":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_file_versions(arguments["file_key"])
            
            # Project tools
            elif name == "figma_get_team_projects":
                if not arguments.get("team_id"):
                    raise ValueError("Missing required argument: team_id")
                result = await get_team_projects(arguments["team_id"])
            elif name == "figma_get_project_files":
                if not arguments.get("project_id"):
                    raise ValueError("Missing required argument: project_id")
                result = await get_project_files(
                    project_id=arguments["project_id"],
                    branch_data=arguments.get("branch_data")
                )
            
            # Comment tools
            elif name == "figma_get_file_comments":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_file_comments(
                    file_key=arguments["file_key"],
                    as_md=arguments.get("as_md")
                )
            elif name == "figma_post_file_comment":
                required_args = ["file_key", "message", "client_meta"]
                for arg in required_args:
                    if arg not in arguments:
                        raise ValueError(f"Missing required argument: {arg}")
                result = await post_file_comment(
                    file_key=arguments["file_key"],
                    message=arguments["message"],
                    client_meta=arguments["client_meta"],
                    comment_id=arguments.get("comment_id")
                )
            elif name == "figma_delete_comment":
                if not arguments.get("comment_id"):
                    raise ValueError("Missing required argument: comment_id")
                result = await delete_comment(arguments["comment_id"])
            
            # Variables tools
            elif name == "figma_get_local_variables":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_local_variables(arguments["file_key"])
            elif name == "figma_get_published_variables":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_published_variables(arguments["file_key"])
            elif name == "figma_post_variables":
                required_args = ["file_key", "variableCollections", "variables"]
                for arg in required_args:
                    if arg not in arguments:
                        raise ValueError(f"Missing required argument: {arg}")
                result = await post_variables(
                    file_key=arguments["file_key"],
                    variableCollections=arguments["variableCollections"],
                    variables=arguments["variables"]
                )
            
            # Dev Resources tools
            elif name == "figma_get_dev_resources":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_dev_resources(
                    file_key=arguments["file_key"],
                    node_id=arguments.get("node_id")
                )
            elif name == "figma_post_dev_resources":
                if not all([arguments.get("file_key"), arguments.get("dev_resources")]):
                    raise ValueError("Missing required arguments: file_key and dev_resources")
                result = await post_dev_resources(
                    file_key=arguments["file_key"],
                    dev_resources=arguments["dev_resources"]
                )
            elif name == "figma_put_dev_resource":
                if not arguments.get("dev_resource_id"):
                    raise ValueError("Missing required argument: dev_resource_id")
                result = await put_dev_resource(
                    dev_resource_id=arguments["dev_resource_id"],
                    name=arguments.get("name"),
                    url=arguments.get("url")
                )
            elif name == "figma_delete_dev_resource":
                if not arguments.get("dev_resource_id"):
                    raise ValueError("Missing required argument: dev_resource_id")
                result = await delete_dev_resource(arguments["dev_resource_id"])
            
            # Webhook tools
            elif name == "figma_get_team_webhooks":
                if not arguments.get("team_id"):
                    raise ValueError("Missing required argument: team_id")
                result = await get_team_webhooks(arguments["team_id"])
            elif name == "figma_post_webhook":
                required_args = ["team_id", "event_type", "endpoint"]
                for arg in required_args:
                    if arg not in arguments:
                        raise ValueError(f"Missing required argument: {arg}")
                result = await post_webhook(
                    team_id=arguments["team_id"],
                    event_type=arguments["event_type"],
                    endpoint=arguments["endpoint"],
                    passcode=arguments.get("passcode"),
                    description=arguments.get("description")
                )
            elif name == "figma_put_webhook":
                if not arguments.get("webhook_id"):
                    raise ValueError("Missing required argument: webhook_id")
                result = await put_webhook(
                    webhook_id=arguments["webhook_id"],
                    event_type=arguments.get("event_type"),
                    endpoint=arguments.get("endpoint"),
                    passcode=arguments.get("passcode"),
                    description=arguments.get("description")
                )
            elif name == "figma_delete_webhook":
                if not arguments.get("webhook_id"):
                    raise ValueError("Missing required argument: webhook_id")
                result = await delete_webhook(arguments["webhook_id"])
            
            # Library Analytics tools
            elif name == "figma_get_library_analytics":
                if not arguments.get("file_key"):
                    raise ValueError("Missing required argument: file_key")
                result = await get_library_analytics(arguments["file_key"])
            
            else:
                error_msg = f"Unknown tool: {name}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=json.dumps({"error": error_msg}))]

            logger.info(f"Tool {name} executed successfully")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            error_response = {
                "error": f"Tool execution failed: {str(e)}",
                "tool": name,
                "arguments": arguments
            }
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]

    # Run with stdio transport for Claude Desktop
    logger.info("Starting Figma MCP server with stdio transport")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


@click.command()
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
def main(log_level: str) -> int:
    """Figma MCP server with stdio transport for Claude Desktop."""
    try:
        asyncio.run(run_server(log_level))
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    main()