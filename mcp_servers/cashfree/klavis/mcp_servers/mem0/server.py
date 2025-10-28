import os
import base64
import logging
import contextlib
import json
from collections.abc import AsyncIterator

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    mem0_api_key_context,
    add_memory,
    get_all_memories,
    search_memories,
    update_memory,
    delete_memory,
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mem0-mcp-server")

MEM0_MCP_SERVER_PORT = int(os.getenv("MEM0_MCP_SERVER_PORT", "5000"))

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
        if hasattr(request_or_scope, 'headers'):
            # SSE request object
            auth_data = request_or_scope.headers.get(b'x-auth-data')
            if auth_data and isinstance(auth_data, bytes):
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
            # StreamableHTTP scope object
            headers = dict(request_or_scope.get("headers", []))
            auth_data = headers.get(b'x-auth-data')
            if auth_data:
                auth_data = base64.b64decode(auth_data).decode('utf-8')
        else:
            auth_data = None
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""

@click.command()
@click.option("--port", default=MEM0_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create the MCP server instance
    app = Server("mem0-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="mem0_add_memory",
                description="Add a new memory to mem0 for long-term storage. This tool stores code snippets, implementation details, and programming knowledge for future reference. When storing information, you should include: complete code with all necessary imports and dependencies, language/framework version information, full implementation context and any required setup/configuration, detailed comments explaining the logic, example usage or test cases, any known limitations or performance considerations, related patterns or alternative approaches, links to relevant documentation or resources, environment setup requirements, and error handling tips. The memory will be indexed for semantic search and can be retrieved later using natural language queries.",
                inputSchema={
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to store in memory, including code, documentation, and context."
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID. If not provided, uses the default user ID."
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
            types.Tool(
                name="mem0_get_all_memories",
                description="Retrieve all stored memories for the user. Call this tool when you need complete context of all previously stored information. This is useful when you need to analyze all available code patterns and knowledge, check all stored implementation examples, review the full history of stored solutions, or ensure no relevant information is missed. Returns a comprehensive list of code snippets and implementation patterns, programming knowledge and best practices, technical documentation and examples, and setup and configuration guides. Results are returned in JSON format with metadata.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID. If not provided, uses the default user ID."
                        },
                        "page": {
                            "type": "integer",
                            "description": "Page number for pagination (default: 1).",
                            "default": 1
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "Number of memories per page (default: 50).",
                            "default": 50
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True})
            ),
            types.Tool(
                name="mem0_search_memories",
                description="Search through stored memories using semantic search. This tool should be called for user queries to find relevant code and implementation details. It helps find specific code implementations or patterns, solutions to programming problems, best practices and coding standards, setup and configuration guides, and technical documentation and examples. The search uses natural language understanding to find relevant matches, so you can describe what you're looking for in plain English. Search the memories to leverage existing knowledge before providing answers.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string describing what you're looking for. Can be natural language or specific technical terms."
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID. If not provided, uses the default user ID."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 20).",
                            "default": 20
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY", "readOnlyHint": True})
            ),
            types.Tool(
                name="mem0_update_memory",
                description="Update an existing memory with new data. This tool allows you to modify the content of a previously stored memory while maintaining its unique identifier. Use this when you need to correct, enhance, or completely replace the content of an existing memory entry.",
                inputSchema={
                    "type": "object",
                    "required": ["memory_id", "data"],
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "The unique identifier of the memory to update."
                        },
                        "data": {
                            "type": "string",
                            "description": "The new content to replace the existing memory data."
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID. If not provided, uses the default user ID."
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
            types.Tool(
                name="mem0_delete_memory",
                description="Delete a specific memory by ID or delete all memories for a user. This tool provides options to remove individual memories or clear all stored memories for a user. Use with caution as deleted memories cannot be recovered.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "The unique identifier of the memory to delete. Required if delete_all is false."
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID. If not provided, uses the default user ID."
                        },
                        "delete_all": {
                            "type": "boolean",
                            "description": "If true, deletes all memories for the user. If false, deletes specific memory by ID.",
                            "default": False
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "MEM0_MEMORY"})
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "mem0_add_memory":
            content = arguments.get("content")
            user_id = arguments.get("user_id")
            if not content:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: content parameter is required",
                    )
                ]
            try:
                result = await add_memory(content, user_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_get_all_memories":
            user_id = arguments.get("user_id")
            page = arguments.get("page", 1)
            page_size = arguments.get("page_size", 50)
            try:
                result = await get_all_memories(user_id, page, page_size)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_search_memories":
            query = arguments.get("query")
            user_id = arguments.get("user_id")
            limit = arguments.get("limit", 20)
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            try:
                result = await search_memories(query, user_id, limit)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_update_memory":
            memory_id = arguments.get("memory_id")
            data = arguments.get("data")
            user_id = arguments.get("user_id")
            if not memory_id or not data:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: memory_id and data parameters are required",
                    )
                ]
            try:
                result = await update_memory(memory_id, data, user_id)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        elif name == "mem0_delete_memory":
            memory_id = arguments.get("memory_id")
            user_id = arguments.get("user_id")
            delete_all = arguments.get("delete_all", False)
            if not delete_all and not memory_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: memory_id parameter is required when delete_all is false",
                    )
                ]
            try:
                result = await delete_memory(memory_id, user_id, delete_all)
                return [
                    types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2),
                    )
                ]
            except Exception as e:
                logger.exception(f"Error executing tool {name}: {e}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {str(e)}",
                    )
                ]
        
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"Unknown tool: {name}",
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        # Set the API key in context for this request
        token = mem0_api_key_context.set(api_key or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            mem0_api_key_context.reset(token)
        
        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode - can be changed to use an event store
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")
        
        # Extract API key from headers
        api_key = extract_api_key(scope)
        
        # Set the API key in context for this request
        token = mem0_api_key_context.set(api_key or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            mem0_api_key_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
