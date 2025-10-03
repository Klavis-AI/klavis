import os
import base64
import logging
import contextlib
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Optional

import click
from dotenv import load_dotenv
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from starlette.requests import Request

from tools import (
    serpapi_token_context,
    search_jobs,
    get_job_details,
    search_jobs_by_company,
    search_remote_jobs,
    get_job_search_suggestions,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-jobs-mcp-server")

GOOGLE_JOBS_MCP_SERVER_PORT = int(os.getenv("GOOGLE_JOBS_MCP_SERVER_PORT", "5000"))

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

@click.command()
@click.option("--port", default=GOOGLE_JOBS_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("google-jobs-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="google_jobs_search",
                description="Search for job listings on Google Jobs. Supports filtering by location, date posted, employment type, salary, company, and more.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Job search query (e.g., 'software engineer', 'marketing manager')"
                        },
                        "location": {
                            "type": "string",
                            "description": "Location to search for jobs (e.g., 'New York, NY', 'Remote', 'San Francisco')"
                        },
                        "date_posted": {
                            "type": "string",
                            "description": "Filter by posting date",
                            "enum": ["today", "3days", "week", "month"]
                        },
                        "employment_type": {
                            "type": "string",
                            "description": "Type of employment",
                            "enum": ["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"]
                        },
                        "salary_min": {
                            "type": "integer",
                            "description": "Minimum annual salary in USD"
                        },
                        "company": {
                            "type": "string",
                            "description": "Filter by specific company name"
                        },
                        "radius": {
                            "type": "integer",
                            "description": "Search radius in miles from the specified location (default: 25)"
                        },
                        "start": {
                            "type": "integer",
                            "description": "Starting position for pagination (default: 0)",
                            "default": 0
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_JOBS_SEARCH", "readOnlyHint": True})
            ),
            types.Tool(
                name="google_jobs_get_details",
                description="Get comprehensive details about a specific job listing including full description, requirements, benefits, and application information.",
                inputSchema={
                    "type": "object",
                    "required": ["job_id"],
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Unique job identifier from search results"
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_JOBS_DETAILS", "readOnlyHint": True})
            ),
            types.Tool(
                name="google_jobs_search_by_company",
                description="Search for all job openings at a specific company. Returns current job listings with location and role information.",
                inputSchema={
                    "type": "object",
                    "required": ["company_name"],
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the company to search for jobs"
                        },
                        "location": {
                            "type": "string",
                            "description": "Optional location filter (e.g., 'New York, NY', 'Remote')"
                        },
                        "employment_type": {
                            "type": "string",
                            "description": "Type of employment",
                            "enum": ["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"]
                        },
                        "start": {
                            "type": "integer",
                            "description": "Starting position for pagination (default: 0)",
                            "default": 0
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_JOBS_SEARCH", "readOnlyHint": True})
            ),
            types.Tool(
                name="google_jobs_search_remote",
                description="Search specifically for remote job opportunities. Filters for jobs that can be done remotely or are explicitly marked as remote positions.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Job search query (e.g., 'software engineer', 'marketing manager')"
                        },
                        "employment_type": {
                            "type": "string",
                            "description": "Type of employment",
                            "enum": ["FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN"]
                        },
                        "date_posted": {
                            "type": "string",
                            "description": "Filter by posting date",
                            "enum": ["today", "3days", "week", "month"]
                        },
                        "salary_min": {
                            "type": "integer",
                            "description": "Minimum annual salary in USD"
                        },
                        "start": {
                            "type": "integer",
                            "description": "Starting position for pagination (default: 0)",
                            "default": 0
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_JOBS_SEARCH", "readOnlyHint": True})
            ),
            types.Tool(
                name="google_jobs_get_suggestions",
                description="Get search suggestions and related job titles based on a query. Useful for discovering similar roles or refining search terms.",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Base job query to get suggestions for"
                        }
                    }
                },
                annotations=types.ToolAnnotations(**{"category": "GOOGLE_JOBS_SUGGESTION", "readOnlyHint": True})
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        
        if name == "google_jobs_search":
            query = arguments.get("query")
            location = arguments.get("location")
            date_posted = arguments.get("date_posted")
            employment_type = arguments.get("employment_type")
            salary_min = arguments.get("salary_min")
            company = arguments.get("company")
            radius = arguments.get("radius")
            start = arguments.get("start", 0)
            
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            try:
                result = await search_jobs(
                    query=query,
                    location=location,
                    date_posted=date_posted,
                    employment_type=employment_type,
                    salary_min=salary_min,
                    company=company,
                    radius=radius,
                    start=start
                )
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
        
        elif name == "google_jobs_get_details":
            job_id = arguments.get("job_id")
            
            if not job_id:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: job_id parameter is required",
                    )
                ]
            try:
                result = await get_job_details(job_id)
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
        
        elif name == "google_jobs_search_by_company":
            company_name = arguments.get("company_name")
            location = arguments.get("location")
            employment_type = arguments.get("employment_type")
            start = arguments.get("start", 0)
            
            if not company_name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: company_name parameter is required",
                    )
                ]
            try:
                result = await search_jobs_by_company(
                    company_name=company_name,
                    location=location,
                    employment_type=employment_type,
                    start=start
                )
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
        
        elif name == "google_jobs_search_remote":
            query = arguments.get("query")
            employment_type = arguments.get("employment_type")
            date_posted = arguments.get("date_posted")
            salary_min = arguments.get("salary_min")
            start = arguments.get("start", 0)
            
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            try:
                result = await search_remote_jobs(
                    query=query,
                    employment_type=employment_type,
                    date_posted=date_posted,
                    salary_min=salary_min,
                    start=start
                )
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
        
        elif name == "google_jobs_get_suggestions":
            query = arguments.get("query")
            
            if not query:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: query parameter is required",
                    )
                ]
            try:
                result = await get_job_search_suggestions(query)
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

    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        """Handle SSE connections."""
        logger.info("Handling SSE connection")
        
        auth_token = extract_api_key(request)
        
        token = serpapi_token_context.set(auth_token or "")
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        except Exception as e:
            logger.exception(f"Error in SSE handler: {e}")
            return Response(f"Internal server error: {str(e)}", status_code=500)
        finally:
            serpapi_token_context.reset(token)
        
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,  # Stateless mode
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Handle StreamableHTTP requests."""
        logger.info(f"Handling StreamableHTTP request: {scope['method']} {scope['path']}")
        
        if scope["method"] != "POST":
            await send({
                "type": "http.response.start",
                "status": 405,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"allow", b"POST"]
                ],
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({
                    "error": "Method not allowed. Only POST requests are supported for MCP endpoints."
                }).encode(),
            })
            return
        
        auth_token = extract_api_key(scope)
        
        token = serpapi_token_context.set(auth_token or "")
        try:
            await session_manager.handle_request(scope, receive, send)
        except Exception as e:
            logger.exception(f"Error in StreamableHTTP handler: {e}")
            try:
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"error": f"Internal server error: {str(e)}"}).encode(),
                })
            except Exception:
                logger.warning("Could not send error response, connection may be closed")
        finally:
            serpapi_token_context.reset(token)

    async def handle_mcp_info(request: Request) -> JSONResponse:
        """Handle GET requests to MCP endpoint with information."""
        return JSONResponse({
            "error": "Method not allowed",
            "message": "This endpoint only accepts POST requests for MCP protocol communication.",
            "supported_methods": ["POST"],
            "usage": "Send MCP protocol messages via POST requests to this endpoint."
        }, status_code=405)

    async def handle_root(request: Request) -> JSONResponse:
        """Handle root endpoint with server info."""
        return JSONResponse({
            "name": "google-jobs-mcp-server",
            "version": "1.0.0",
            "description": "MCP server for Google Jobs search functionality",
            "endpoints": {
                "sse": "/sse",
                "streamable_http": "/mcp",
                "messages": "/messages"
            },
            "tools": [
                "google_jobs_search",
                "google_jobs_get_details", 
                "google_jobs_search_by_company",
                "google_jobs_search_remote",
                "google_jobs_get_suggestions"
            ],
            "status": "running"
        })

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        try:
            async with session_manager.run():
                logger.info("Application started with dual transports!")
                yield
        except Exception as e:
            logger.exception(f"Error in lifespan manager: {e}")
            raise
        finally:
            logger.info("Application shutting down...")

    # Create an ASGI application with routes for both transports
    starlette_app = Starlette(
        debug=True,
        routes=[
            # Root endpoint
            Route("/", endpoint=handle_root, methods=["GET"]),
            
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages", app=sse.handle_post_message),
            
            # StreamableHTTP routes
            Route("/mcp", endpoint=handle_mcp_info, methods=["GET"]),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info(f"Server starting on port {port} with dual transports:")
    logger.info(f"  - Root endpoint: http://localhost:{port}/")
    logger.info(f"  - SSE endpoint: http://localhost:{port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://localhost:{port}/mcp")
    logger.info(f"  - Messages endpoint: http://localhost:{port}/messages")

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0

if __name__ == "__main__":
    main()
    
