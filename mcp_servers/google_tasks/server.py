"""
An MCP server for Google Tasks.

This script sets up and runs the Starlette web server, defines the tool
menu for the MCP client, and dispatches tool calls to the implementations
located in the 'tools' module.
"""
import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator

import click
import mcp.types as types
from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# Import the tool implementations from our tools file
import tools

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-tasks-mcp-server")
PORT = int(os.getenv("PORT", "8000"))


# --- MCP Server ---

@click.command()
@click.option("--port", default=PORT, help="Port to listen on for HTTP")
def main(port: int) -> int:
    """Main function to configure and run the MCP server."""
    app = Server(
        "google-tasks-mcp-server",
        instructions="An agent for managing Google Tasks. You can manage task lists and the tasks within them.",
    )

    # --- Tool Menu Definition ---
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        logger.info("Client requested tool list")
        return [
            types.Tool(
                name="list_task_lists",
                description="List all of your Google Tasks lists to find their IDs.",
                inputSchema={"type": "object", "properties": {
                    "max_results": {"type": "integer", "description": "Maximum number of lists to return."}
                }},
            ),
            types.Tool(
                name="create_task_list",
                description="Create a new task list.",
                inputSchema={"type": "object", "required": ["title"], "properties": {
                    "title": {"type": "string", "description": "The title for the new task list."}
                }},
            ),
            types.Tool(
                name="list_tasks",
                description="List tasks in a specific task list. Use '@default' for the default list.",
                inputSchema={"type": "object", "required": ["list_id"], "properties": {
                    "list_id": {"type": "string", "description": "ID of the task list or '@default'."},
                    "show_completed": {"type": "boolean", "description": "Set to false to hide completed tasks."},
                    "max_results": {"type": "integer", "description": "Maximum number of tasks to return."}
                }},
            ),
            types.Tool(
                name="create_task",
                description="Create a new task in a list.",
                inputSchema={"type": "object", "required": ["list_id", "title"], "properties": {
                    "list_id": {"type": "string", "description": "ID of the task list to add the task to."},
                    "title": {"type": "string", "description": "The title of the task."},
                    "notes": {"type": "string", "description": "Optional detailed notes for the task."}
                }},
            ),
            types.Tool(
                name="update_task",
                description="Update a task's title, notes, or status.",
                inputSchema={"type": "object", "required": ["list_id", "task_id"], "properties": {
                    "list_id": {"type": "string", "description": "ID of the task's list."},
                    "task_id": {"type": "string", "description": "ID of the task to update."},
                    "title": {"type": "string", "description": "The new title for the task."},
                    "notes": {"type": "string", "description": "The new notes for the task."},
                    "status": {"type": "string", "enum": ["needsAction", "completed"], "description": "Set to 'completed' or 'needsAction'."}
                }},
            ),
            types.Tool(
                name="delete_task",
                description="Delete a task by its list ID and task ID.",
                inputSchema={"type": "object", "required": ["list_id", "task_id"], "properties": {
                    "list_id": {"type": "string", "description": "The ID of the list containing the task."},
                    "task_id": {"type": "string", "description": "The ID of the task to delete."}
                }},
            ),
        ]

    # --- Tool Dispatcher ---
    tool_implementations = {
        "list_task_lists": tools.list_task_lists,
        "create_task_list": tools.create_task_list,
        "list_tasks": tools.list_tasks,
        "create_task": tools.create_task,
        "update_task": tools.update_task,
        "delete_task": tools.delete_task,
    }

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        logger.info(f"Tool call: {name} with args: {arguments}")
        tool_func = tool_implementations.get(name)
        if not tool_func:
            result = tools._error_response(f"Unknown tool name: '{name}'")
        else:
            try:
                # Call the function from the tools module
                result = tool_func(**arguments)
            except (TypeError, FileNotFoundError, ConnectionError) as e:
                logger.error(f"Error executing tool '{name}': {e}")
                result = tools._error_response(str(e), 500)
            except Exception:
                logger.exception(f"An unexpected error occurred in tool '{name}'")
                result = tools._error_response("An unexpected internal error occurred.", 500)
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    # --- Starlette Server Setup ---
    session_manager = StreamableHTTPSessionManager(app=app, stateless=True)

    @contextlib.asynccontextmanager
    async def lifespan(app_instance: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("MCP Session Manager started.")
            yield
        logger.info("MCP Session Manager stopped.")
    
    async def healthz(request):
        return JSONResponse({"ok": True})

    starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=session_manager.handle_request),
            Route("/healthz", healthz),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Starting Google Tasks MCP server on http://localhost:{port}")
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    main()
