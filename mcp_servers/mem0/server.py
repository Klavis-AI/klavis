import argparse
import json
import logging
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server.sse import SseServerTransport
from mcp.server import Server

from tools import (
    add_memory,
    get_all_memories,
    search_memories
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastMCP server for mem0 tools
mcp = FastMCP("mem0-mcp")

@mcp.tool(
    description="""Add a new memory to mem0 for long-term storage. This tool stores code snippets, implementation details,
    and programming knowledge for future reference. When storing information, you should include:
    - Complete code with all necessary imports and dependencies
    - Language/framework version information (e.g., "Python 3.9", "React 18")
    - Full implementation context and any required setup/configuration
    - Detailed comments explaining the logic, especially for complex sections
    - Example usage or test cases demonstrating the code
    - Any known limitations, edge cases, or performance considerations
    - Related patterns or alternative approaches
    - Links to relevant documentation or resources
    - Environment setup requirements (if applicable)
    - Error handling and debugging tips
    The memory will be indexed for semantic search and can be retrieved later using natural language queries."""
)
async def mem0_add_memory(content: str, user_id: str = None) -> str:
    """Add a new memory to mem0 for persistent storage.

    This tool stores code snippets, implementation patterns, programming knowledge, and technical information.
    When storing information, it's recommended to include:
    - Complete code with imports and dependencies
    - Language/framework information
    - Setup instructions if needed
    - Documentation and comments
    - Example usage

    Args:
        content: The content to store in memory, including code, documentation, and context
        user_id: Optional user ID. If not provided, uses the default user ID.
    """
    try:
        result = await add_memory(content, user_id)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error adding memory: {e}")
        return f"Error adding memory: {str(e)}"

@mcp.tool(
    description="""Retrieve all stored memories for the user. Call this tool when you need 
    complete context of all previously stored information. This is useful when:
    - You need to analyze all available code patterns and knowledge
    - You want to check all stored implementation examples
    - You need to review the full history of stored solutions
    - You want to ensure no relevant information is missed
    Returns a comprehensive list of:
    - Code snippets and implementation patterns
    - Programming knowledge and best practices
    - Technical documentation and examples
    - Setup and configuration guides
    Results are returned in JSON format with metadata."""
)
async def mem0_get_all_memories(user_id: str = None, page: int = 1, page_size: int = 50) -> str:
    """Get all memories for a user.

    Returns a JSON formatted list of all stored memories, including:
    - Code implementations and patterns
    - Technical documentation
    - Programming best practices
    - Setup guides and examples
    Each memory includes metadata about when it was created and its content type.
    
    Args:
        user_id: Optional user ID. If not provided, uses the default user ID.
        page: Page number for pagination (default: 1).
        page_size: Number of memories per page (default: 50).
    """
    try:
        result = await get_all_memories(user_id, page, page_size)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error getting memories: {e}")
        return f"Error getting memories: {str(e)}"

@mcp.tool(
    description="""Search through stored memories using semantic search. This tool should be called 
    for user queries to find relevant code and implementation details. It helps find:
    - Specific code implementations or patterns
    - Solutions to programming problems
    - Best practices and coding standards
    - Setup and configuration guides
    - Technical documentation and examples
    The search uses natural language understanding to find relevant matches, so you can
    describe what you're looking for in plain English. Search the memories to 
    leverage existing knowledge before providing answers."""
)
async def mem0_search_memories(query: str, user_id: str = None, limit: int = 20) -> str:
    """Search memories using semantic search.

    The search is powered by natural language understanding, allowing you to find:
    - Code implementations and patterns
    - Programming solutions and techniques
    - Technical documentation and guides
    - Best practices and standards
    Results are ranked by relevance to your query.

    Args:
        query: Search query string describing what you're looking for. Can be natural language
              or specific technical terms.
        user_id: Optional user ID. If not provided, uses the default user ID.
        limit: Maximum number of results to return (default: 20).
    """
    try:
        result = await search_memories(query, user_id, limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error searching memories: {e}")
        return f"Error searching memories: {str(e)}"

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

def main():
    """Main entry point for the mem0 MCP server."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run mem0 MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    parser.add_argument('--log-level', default='INFO', help='Logging level')
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get the MCP server instance from FastMCP
    mcp_server = mcp._mcp_server

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    logger.info(f"Server starting on port {args.port}")
    logger.info(f"  - SSE endpoint: http://localhost:{args.port}/sse")

    uvicorn.run(starlette_app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
