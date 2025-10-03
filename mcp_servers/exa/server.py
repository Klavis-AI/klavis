import contextlib
import base64
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import List
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

from tools import (
    auth_token_context,
    exa_search,
    exa_get_contents,
    exa_find_similar,
    exa_answer,
    exa_research
)

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

EXA_MCP_SERVER_PORT = int(os.getenv("EXA_MCP_SERVER_PORT", "5000"))

# Context variable to store the API key for each request
api_key_context: ContextVar[str] = ContextVar('api_key')

def extract_api_key(request_or_scope) -> str:
    """Extract API key from headers or environment."""
    api_key = os.getenv("API_KEY")
    auth_data = None
    
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
        
        if auth_data:
            try:
                # Parse the JSON auth data to extract token
                auth_json = json.loads(auth_data)
                api_key = auth_json.get('token') or auth_json.get('api_key') or ''
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse auth data JSON: {e}")
                api_key = ""
    
    return api_key or ""

def get_api_key() -> str:
    """Get the API key from context."""
    try:
        return api_key_context.get()
    except LookupError:
        raise RuntimeError("API key not found in request context")

@click.command()
@click.option("--port", default=EXA_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    app = Server("exa-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="exa_search",
                description="""
                Search the web for content using AI-powered semantic search or traditional keyword search.
                
                Use this tool when you need to find web pages, articles, or content related to a topic.
                Exa's neural search understands meaning and context, making it excellent for research and content discovery.
                Returns search results with URLs, titles, scores, and optional content text.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Required. The search query to find relevant web content."
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (max 1000, default 10)."
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to include in search results (e.g., ['reddit.com', 'stackoverflow.com'])."
                        },
                        "exclude_domains": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "List of domains to exclude from search results."
                        },
                        "start_crawl_date": {
                            "type": "string",
                            "description": "Start date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "end_crawl_date": {
                            "type": "string",
                            "description": "End date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "start_published_date": {
                            "type": "string",
                            "description": "Start date for published date filter (YYYY-MM-DD format)."
                        },
                        "end_published_date": {
                            "type": "string",
                            "description": "End date for published date filter (YYYY-MM-DD format)."
                        },
                        "use_autoprompt": {
                            "type": "boolean",
                            "description": "Whether to use Exa's autoprompt feature to optimize the search query (default true)."
                        },
                        "type": {
                            "type": "string",
                            "enum": ["neural", "keyword"],
                            "description": "Search type: 'neural' for AI-powered semantic search or 'keyword' for traditional keyword search."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category filter for results (e.g., 'news', 'research', 'company')."
                        },
                        "include_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns that must be included in the results."
                        },
                        "exclude_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns to exclude from the results."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(**{"category": "EXA_SEARCH", "readOnlyHint": True})
            ),

            types.Tool(
                name="exa_get_contents",
                description="""
                Get the full text content of web pages using their Exa search result IDs.
                
                Use this tool after performing a search to retrieve the actual text content from specific results.
                Returns clean, parsed content with optional highlighting and summarization features.
                Essential for reading the full content of interesting search results.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required. List of Exa result IDs to get contents for."
                        },
                        "text": {
                            "type": "boolean",
                            "description": "Whether to include text content (default true)."
                        },
                        "highlights": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "num_sentences": {"type": "integer"}
                            },
                            "description": "Highlighting options with query and number of sentences to highlight."
                        },
                        "summary": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            },
                            "description": "Summary options with query for generating summaries."
                        }
                    },
                    "required": ["ids"]
                },
                annotations=types.ToolAnnotations(**{"category": "EXA_CONTENT", "readOnlyHint": True})
            ),

            types.Tool(
                name="exa_find_similar",
                description="""
                Discover web pages similar in meaning and content to a given URL.
                
                Use this tool when you have a specific webpage and want to find other pages with similar topics,
                themes, or content. Perfect for content discovery, finding related articles, or expanding research
                around a specific source. Returns semantically similar pages with relevance scores.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Required. The URL to find similar pages for."
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of similar results to return (max 1000, default 10)."
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to include in search results."
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to exclude from search results."
                        },
                        "start_crawl_date": {
                            "type": "string",
                            "description": "Start date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "end_crawl_date": {
                            "type": "string",
                            "description": "End date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "start_published_date": {
                            "type": "string",
                            "description": "Start date for published date filter (YYYY-MM-DD format)."
                        },
                        "end_published_date": {
                            "type": "string",
                            "description": "End date for published date filter (YYYY-MM-DD format)."
                        },
                        "exclude_source_domain": {
                            "type": "boolean",
                            "description": "Whether to exclude results from the same domain as the source URL (default true)."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category filter for results."
                        },
                        "include_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns that must be included in the results."
                        },
                        "exclude_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns to exclude from the results."
                        }
                    },
                    "required": ["url"]
                },
                annotations=types.ToolAnnotations(**{"category": "EXA_DISCOVERY", "readOnlyHint": True})
            ),

            types.Tool(
                name="exa_answer",
                description="""
                Get a direct answer to a specific question by searching and analyzing web sources.
                
                Use this tool when you need a focused answer to a specific question rather than general search results.
                The tool searches relevant sources and provides a structured response with citations.
                Ideal for fact-finding, research questions, and getting quick, sourced answers.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Required. The question to get a direct answer for."
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to include in the search for answering."
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to exclude from the search for answering."
                        },
                        "start_crawl_date": {
                            "type": "string",
                            "description": "Start date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "end_crawl_date": {
                            "type": "string",
                            "description": "End date for crawl date filter (YYYY-MM-DD format)."
                        },
                        "start_published_date": {
                            "type": "string",
                            "description": "Start date for published date filter (YYYY-MM-DD format)."
                        },
                        "end_published_date": {
                            "type": "string",
                            "description": "End date for published date filter (YYYY-MM-DD format)."
                        },
                        "use_autoprompt": {
                            "type": "boolean",
                            "description": "Whether to use Exa's autoprompt feature (default true)."
                        },
                        "type": {
                            "type": "string",
                            "enum": ["neural", "keyword"],
                            "description": "Search type: 'neural' for AI-powered search or 'keyword' for traditional search."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category filter for results."
                        },
                        "include_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns that must be included in search sources."
                        },
                        "exclude_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns to exclude from search sources."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(**{"category": "EXA_QA", "readOnlyHint": True})
            ),

            types.Tool(
                name="exa_research",
                description="""
                Conduct comprehensive research on a topic with multiple sources and structured analysis.
                
                Use this tool for in-depth research projects that require gathering information from multiple
                high-quality sources. Returns structured results with detailed content, citations, and analysis.
                Perfect for academic research, market analysis, or thorough investigation of complex topics.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Required. The research topic or question to investigate comprehensively."
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of sources to include in research (max 1000, default 10)."
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to prioritize in research sources."
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of domains to exclude from research sources."
                        },
                        "start_crawl_date": {
                            "type": "string",
                            "description": "Start date for source date filter (YYYY-MM-DD format)."
                        },
                        "end_crawl_date": {
                            "type": "string",
                            "description": "End date for source date filter (YYYY-MM-DD format)."
                        },
                        "start_published_date": {
                            "type": "string",
                            "description": "Start date for published date filter (YYYY-MM-DD format)."
                        },
                        "end_published_date": {
                            "type": "string",
                            "description": "End date for published date filter (YYYY-MM-DD format)."
                        },
                        "use_autoprompt": {
                            "type": "boolean",
                            "description": "Whether to use Exa's autoprompt optimization (default true)."
                        },
                        "type": {
                            "type": "string", 
                            "enum": ["neural", "keyword"],
                            "description": "Research search type: 'neural' for AI-powered or 'keyword' for traditional."
                        },
                        "category": {
                            "type": "string",
                            "description": "Category focus for research sources."
                        },
                        "include_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns that sources must contain."
                        },
                        "exclude_text": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Text patterns to exclude from sources."
                        }
                    },
                    "required": ["query"]
                },
                annotations=types.ToolAnnotations(**{"category": "EXA_RESEARCH", "readOnlyHint": True})
            )
        ]

    @app.call_tool()
    async def call_tool(
            name: str,
            arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "exa_search":
            try:
                result = await exa_search(
                    query=arguments["query"],
                    num_results=arguments.get("num_results", 10),
                    include_domains=arguments.get("include_domains"),
                    exclude_domains=arguments.get("exclude_domains"),
                    start_crawl_date=arguments.get("start_crawl_date"),
                    end_crawl_date=arguments.get("end_crawl_date"),
                    start_published_date=arguments.get("start_published_date"),
                    end_published_date=arguments.get("end_published_date"),
                    use_autoprompt=arguments.get("use_autoprompt", True),
                    type=arguments.get("type", "neural"),
                    category=arguments.get("category"),
                    include_text=arguments.get("include_text"),
                    exclude_text=arguments.get("exclude_text")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in exa_search: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "exa_get_contents":
            try:
                result = await exa_get_contents(
                    ids=arguments["ids"],
                    text=arguments.get("text", True),
                    highlights=arguments.get("highlights"),
                    summary=arguments.get("summary")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in exa_get_contents: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "exa_find_similar":
            try:
                result = await exa_find_similar(
                    url=arguments["url"],
                    num_results=arguments.get("num_results", 10),
                    include_domains=arguments.get("include_domains"),
                    exclude_domains=arguments.get("exclude_domains"),
                    start_crawl_date=arguments.get("start_crawl_date"),
                    end_crawl_date=arguments.get("end_crawl_date"),
                    start_published_date=arguments.get("start_published_date"),
                    end_published_date=arguments.get("end_published_date"),
                    exclude_source_domain=arguments.get("exclude_source_domain", True),
                    category=arguments.get("category"),
                    include_text=arguments.get("include_text"),
                    exclude_text=arguments.get("exclude_text")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in exa_find_similar: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "exa_answer":
            try:
                result = await exa_answer(
                    query=arguments["query"],
                    include_domains=arguments.get("include_domains"),
                    exclude_domains=arguments.get("exclude_domains"),
                    start_crawl_date=arguments.get("start_crawl_date"),
                    end_crawl_date=arguments.get("end_crawl_date"),
                    start_published_date=arguments.get("start_published_date"),
                    end_published_date=arguments.get("end_published_date"),
                    use_autoprompt=arguments.get("use_autoprompt", True),
                    type=arguments.get("type", "neural"),
                    category=arguments.get("category"),
                    include_text=arguments.get("include_text"),
                    exclude_text=arguments.get("exclude_text")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in exa_answer: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        elif name == "exa_research":
            try:
                result = await exa_research(
                    query=arguments["query"],
                    num_results=arguments.get("num_results", 10),
                    include_domains=arguments.get("include_domains"),
                    exclude_domains=arguments.get("exclude_domains"),
                    start_crawl_date=arguments.get("start_crawl_date"),
                    end_crawl_date=arguments.get("end_crawl_date"),
                    start_published_date=arguments.get("start_published_date"),
                    end_published_date=arguments.get("end_published_date"),
                    use_autoprompt=arguments.get("use_autoprompt", True),
                    type=arguments.get("type", "neural"),
                    category=arguments.get("category"),
                    include_text=arguments.get("include_text"),
                    exclude_text=arguments.get("exclude_text")
                )
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.exception(f"Error in exa_research: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        # Set the API key in context for this request
        token = api_key_context.set(api_key)
        try:
            async with sse.connect_sse(
                    request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            api_key_context.reset(token)

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
        token = api_key_context.set(api_key)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            api_key_context.reset(token)

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
