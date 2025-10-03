import contextlib
import logging
import os
import json
import base64
from collections.abc import AsyncIterator
from typing import Any, Dict

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

from tools.base import OpenRouterToolExecutionError, auth_token_context

# Import tools
from tools import models as model_tools
from tools import chat as chat_tools
from tools import usage as usage_tools
from tools import comparison as comparison_tools

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()

OPENROUTER_MCP_SERVER_PORT = int(os.getenv("OPENROUTER_MCP_SERVER_PORT", "5000"))


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
@click.option("--port", default=OPENROUTER_MCP_SERVER_PORT, help="Port to listen on for HTTP")
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
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = Server("openrouter-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="openrouter_list_models",
                description="List available models on OpenRouter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of models to return (1-100, default 50)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "next_page_token": {
                            "type": "string",
                            "description": "Token for pagination",
                        },
                    },
                    "required": [],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_search_models",
                description="Search for models based on various criteria",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of models to return (1-100, default 20)",
                            "minimum": 1,
                            "maximum": 100,
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by model category (e.g., 'chat', 'completion', 'embedding')",
                        },
                        "provider": {
                            "type": "string",
                            "description": "Filter by provider (e.g., 'anthropic', 'openai', 'meta-llama')",
                        },
                    },
                    "required": ["query"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_model_pricing",
                description="Get pricing information for a specific model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "The ID of the model to get pricing for",
                        },
                    },
                    "required": ["model_id"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
            
            types.Tool(
                name="openrouter_create_chat_completion",
                description="Create a chat completion using OpenRouter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "The model to use for completion",
                        },
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {
                                        "type": "string",
                                        "enum": ["system", "user", "assistant"],
                                        "description": "The role of the message sender",
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the message",
                                    },
                                },
                                "required": ["role", "content"],
                            },
                            "description": "List of message objects with 'role' and 'content'",
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum number of tokens to generate",
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Sampling temperature (0.0 to 2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                        },
                        "top_p": {
                            "type": "number",
                            "description": "Nucleus sampling parameter (0.0 to 1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "n": {
                            "type": "integer",
                            "description": "Number of completions to generate (1 to 10)",
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "stream": {
                            "type": "boolean",
                            "description": "Whether to stream the response",
                            "default": False,
                        },
                        "stop": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Stop sequences",
                        },
                        "presence_penalty": {
                            "type": "number",
                            "description": "Presence penalty (-2.0 to 2.0)",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "frequency_penalty": {
                            "type": "number",
                            "description": "Frequency penalty (-2.0 to 2.0)",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "logit_bias": {
                            "type": "object",
                            "description": "Logit bias dictionary",
                        },
                        "user": {
                            "type": "string",
                            "description": "User identifier",
                        },
                    },
                    "required": ["model", "messages"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_CHAT_COMPLETION"}),
            ),
            types.Tool(
                name="openrouter_create_chat_completion_stream",
                description="Create a streaming chat completion using OpenRouter",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "The model to use for completion",
                        },
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {
                                        "type": "string",
                                        "enum": ["system", "user", "assistant"],
                                    },
                                    "content": {
                                        "type": "string",
                                    },
                                },
                                "required": ["role", "content"],
                            },
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum number of tokens to generate",
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 2.0,
                        },
                        "top_p": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "stop": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "presence_penalty": {
                            "type": "number",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "frequency_penalty": {
                            "type": "number",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "logit_bias": {
                            "type": "object",
                        },
                        "user": {
                            "type": "string",
                        },
                    },
                    "required": ["model", "messages"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_CHAT_COMPLETION"}),
            ),
            types.Tool(
                name="openrouter_create_completion",
                description="Create a text completion using OpenRouter (legacy completion endpoint)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "The model to use for completion",
                        },
                        "prompt": {
                            "type": "string",
                            "description": "The text prompt to complete",
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum number of tokens to generate",
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 2.0,
                        },
                        "top_p": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "n": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "stream": {
                            "type": "boolean",
                            "default": False,
                        },
                        "stop": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "presence_penalty": {
                            "type": "number",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "frequency_penalty": {
                            "type": "number",
                            "minimum": -2.0,
                            "maximum": 2.0,
                        },
                        "logit_bias": {
                            "type": "object",
                        },
                        "user": {
                            "type": "string",
                        },
                    },
                    "required": ["model", "prompt"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_CHAT_COMPLETION"}),
            ),
            
            types.Tool(
                name="openrouter_get_usage",
                description="Get usage statistics for the authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (defaults to 30 days ago)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (defaults to today)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return (1-1000, default 100)",
                            "minimum": 1,
                            "maximum": 1000,
                        },
                    },
                    "required": [],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_USAGE", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_user_profile",
                description="Get the current user's profile information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_USER", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_credits",
                description="Get the current user's credit balance",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_METADATA", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_api_key_info",
                description="Get information about the current API key",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_METADATA", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_cost_estimate",
                description="Estimate the cost for a specific model and token usage",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "The model ID to estimate costs for",
                        },
                        "input_tokens": {
                            "type": "integer",
                            "description": "Number of input tokens",
                            "minimum": 0,
                        },
                        "output_tokens": {
                            "type": "integer",
                            "description": "Number of output tokens (optional, defaults to 0)",
                            "minimum": 0,
                        },
                    },
                    "required": ["model", "input_tokens"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_USAGE", "readOnlyHint": True}),
            ),
            
            types.Tool(
                name="openrouter_compare_models",
                description="Compare multiple models by running the same prompt through each",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "models": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of model IDs to compare (2-5 models)",
                            "minItems": 2,
                            "maxItems": 5,
                        },
                        "test_prompt": {
                            "type": "string",
                            "description": "The prompt to test with all models",
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate (default 100)",
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Sampling temperature (default 0.7)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                        },
                    },
                    "required": ["models", "test_prompt"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_analyze_model_performance",
                description="Analyze the performance of a single model across multiple test prompts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "The model ID to analyze",
                        },
                        "test_prompts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of test prompts to use (max 10)",
                            "maxItems": 10,
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate (default 100)",
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Sampling temperature (default 0.7)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                        },
                    },
                    "required": ["model", "test_prompts"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
            types.Tool(
                name="openrouter_get_model_recommendations",
                description="Get model recommendations based on use case and constraints",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "use_case": {
                            "type": "string",
                            "description": "Description of the intended use case",
                        },
                        "budget_constraint": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "unlimited"],
                            "description": "Budget constraint",
                        },
                        "performance_priority": {
                            "type": "string",
                            "enum": ["speed", "quality", "balanced"],
                            "description": "Performance priority",
                        },
                    },
                    "required": ["use_case"],
                },
                annotations=types.ToolAnnotations(**{"category": "OPENROUTER_MODEL", "readOnlyHint": True}),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        try:
            if name == "openrouter_list_models":
                result = await model_tools.list_models(**arguments)

            elif name == "openrouter_search_models":
                result = await model_tools.search_models(**arguments)
            elif name == "openrouter_get_model_pricing":
                result = await model_tools.get_model_pricing(**arguments)
            
            elif name == "openrouter_create_chat_completion":
                result = await chat_tools.create_chat_completion(**arguments)
            elif name == "openrouter_create_chat_completion_stream":
                result = await chat_tools.create_chat_completion_stream(**arguments)
            elif name == "openrouter_create_completion":
                result = await chat_tools.create_completion(**arguments)
            
            elif name == "openrouter_get_usage":
                result = await usage_tools.get_usage(**arguments)
            elif name == "openrouter_get_user_profile":
                result = await usage_tools.get_user_profile(**arguments)
            elif name == "openrouter_get_credits":
                result = await usage_tools.get_credits(**arguments)
            elif name == "openrouter_get_api_key_info":
                result = await usage_tools.get_api_key_info(**arguments)
            elif name == "openrouter_get_cost_estimate":
                result = await usage_tools.get_cost_estimate(**arguments)
            
            elif name == "openrouter_compare_models":
                result = await comparison_tools.compare_models(**arguments)
            elif name == "openrouter_analyze_model_performance":
                result = await comparison_tools.analyze_model_performance(**arguments)
            elif name == "openrouter_get_model_recommendations":
                result = await comparison_tools.get_model_recommendations(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        except OpenRouterToolExecutionError as e:
            logger.error(f"Retryable error in {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "retry_after_ms": e.retry_after_ms,
                        "additional_prompt_content": e.additional_prompt_content,
                        "developer_message": e.developer_message,
                    }, indent=2)
                )
            ]
        except Exception as e:
            logger.exception(f"Error in {name}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}, indent=2)
                )
            ]

    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        
        # Extract API key from headers
        api_key = extract_api_key(request)
        
        # Set the API key in context for this request
        token = auth_token_context.set(api_key)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            auth_token_context.reset(token)
        
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
        token = auth_token_context.set(api_key)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            auth_token_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

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

    try:
        uvicorn.run(
            starlette_app,
            host="0.0.0.0",
            port=port,
            log_level=log_level.lower(),
        )
        return 0
    except Exception as e:
        logger.exception(f"Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 