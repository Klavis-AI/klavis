import contextlib
import json
import logging
import os
import asyncio
from collections.abc import AsyncIterator
from typing import Callable, Awaitable, Any

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools.base import init_http_clients, close_http_clients
from tools import (
    get_my_boards,
    create_board,
    get_board_lists,
    get_list_cards,
    create_card,
    update_card,
    delete_card,
    create_checklist,
    add_item_to_checklist,
    update_checklist_item_state,
)

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

TRELLO_MCP_SERVER_PORT = int(os.getenv("TRELLO_MCP_SERVER_PORT", "5002"))

def get_all_tools() -> list[types.Tool]:
    """Returns a list of all tool definitions."""
    return [
        types.Tool(
            name="trello_get_my_boards",
            description="Fetches all boards that the user is a member of.",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="trello_create_board",
            description="Creates a new board in Trello.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the board."
                    },
                    "desc": {
                        "type": "string",
                        "description": "The description of the board."
                    }
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="trello_get_board_lists",
            description="Fetches all lists in a specific board.",
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {
                        "type": "string",
                        "description": "The ID of the board to get the lists from."
                    }
                },
                "required": ["board_id"]
            }
        ),
        types.Tool(
            name="trello_get_list_cards",
            description="Fetches all cards in a specific list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_id": {
                        "type": "string",
                        "description": "The ID of the list to get the cards from."
                    }
                },
                "required": ["list_id"]
            }
        ),
        types.Tool(
            name="trello_create_card",
            description="Creates a new card in a specific list.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idList": {
                        "type": "string",
                        "description": "The ID of the list to create the card in."
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the card."
                    },
                    "desc": {
                        "type": "string",
                        "description": "The description of the card."
                    }
                },
                "required": ["idList", "name"]
            }
        ),
        types.Tool(
            name="trello_update_card",
            description="Updates a card in Trello.",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card to update."
                    },
                    "name": {
                        "type": "string",
                        "description": "The new name of the card."
                    },
                    "desc": {
                        "type": "string",
                        "description": "The new description of the card."
                    },
                    "idList": {
                        "type": "string",
                        "description": "The new list ID for the card."
                    }
                },
                "required": ["card_id"]
            }
        ),
        types.Tool(
            name="trello_delete_card",
            description="Deletes a card in Trello.",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_id": {
                        "type": "string",
                        "description": "The ID of the card to delete."
                    }
                },
                "required": ["card_id"]
            }
        ),
        types.Tool(
            name="trello_create_checklist",
            description="Creates a new checklist on a specific card.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idCard": {
                        "type": "string",
                        "description": "The ID of the card to add the checklist to."
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the checklist."
                    }
                },
                "required": ["idCard", "name"]
            }
        ),
        types.Tool(
            name="trello_add_item_to_checklist",
            description="Adds a new item to a specific checklist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "idChecklist": {
                        "type": "string",
                        "description": "The ID of the checklist to add the item to."
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the checklist item."
                    },
                    "checked": {
                        "type": "boolean",
                        "description": "Whether the item should be checked (default: false)."
                    }
                },
                "required": ["idChecklist", "name"]
            }
        ),
        types.Tool(
            name="trello_update_checklist_item_state",
            description="Updates the state of an item on a checklist (e.g., 'complete' or 'incomplete').",
            inputSchema={
                "type": "object",
                "properties": {
                    "idCard": {
                        "type": "string",
                        "description": "The ID of the card containing the checklist item."
                    },
                    "idCheckItem": {
                        "type": "string",
                        "description": "The ID of the checklist item to update."
                    },
                    "state": {
                        "type": "string",
                        "description": "The new state of the item. Must be 'complete' or 'incomplete'.",
                        "enum": ["complete", "incomplete"]
                    }
                },
                "required": ["idCard", "idCheckItem", "state"]
            }
        ),
    ]

async def call_tool_router(name: str, arguments: dict) -> Any:
    """Unified router for all tool calls."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    tool_map: dict[str, Callable[..., Awaitable[Any]]] = {
        "trello_get_my_boards": get_my_boards,
        "trello_create_board": create_board,
        "trello_get_board_lists": get_board_lists,
        "trello_get_list_cards": get_list_cards,
        "trello_create_card": create_card,
        "trello_update_card": update_card,
        "trello_delete_card": delete_card,
        "trello_create_checklist": create_checklist,
        "trello_add_item_to_checklist": add_item_to_checklist,
        "trello_update_checklist_item_state": update_checklist_item_state,
    }
    
    tool_func = tool_map.get(name)
    if not tool_func:
        raise ValueError(f"Unknown tool: {name}")
        
    return await tool_func(**arguments)

@click.command()
@click.option("--port", default=TRELLO_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
@click.option(
    "--stdio",
    is_flag=True,
    default=False,
    help="Run in stdio mode for Claude Desktop (instead of HTTP server mode)",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
    stdio: bool,
) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if stdio:
        return run_stdio_mode()
    else:
        return run_http_mode(port, json_response)

def run_stdio_mode() -> int:
    """Run the MCP server in stdio mode."""
    logger.info("Trello MCP Server initializing in stdio mode...")
    app = Server("trello-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return get_all_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            await init_http_clients()
            result = await call_tool_router(name, arguments)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            error_response = {"error": str(e), "tool": name}
            return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
        finally:
            await close_http_clients()

    async def run_server():
        logger.info("Starting stdio server...")
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    
    asyncio.run(run_server())
    return 0

def run_http_mode(port: int, json_response: bool) -> int:
    """Run the MCP server in HTTP mode."""
    app = Server("trello-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return get_all_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        try:
            result = await call_tool_router(name, arguments)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        await init_http_clients()
        async with session_manager.run():
            logger.info("Trello MCP Server started in HTTP mode!")
            try:
                yield
            finally:
                logger.info("Trello MCP Server shutting down...")
                await close_http_clients()

    starlette_app = Starlette(
        debug=True,
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on http://0.0.0.0:{port}/mcp")
    import uvicorn
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    main()