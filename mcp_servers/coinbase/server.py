import contextlib
import base64
import json
import logging
import os

from collections.abc import AsyncIterator
from typing import List

import click
import mcp.types as types

from dotenv import load_dotenv
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from tools import (
    auth_token_context,
    coinbase_get_prices,
    coinbase_get_current_exchange_rate,
    coinbase_get_accounts,
    coinbase_get_account_balance,
    coinbase_get_transactions,
    coinbase_get_portfolio_value,
    coinbase_get_product_details,
    coinbase_get_historical_prices,
)

# Configure logging
logger = logging.getLogger(__name__)


load_dotenv()

COINBASE_MCP_SERVER_PORT = int(os.getenv("COINBASE_MCP_SERVER_PORT", "5000"))

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
@click.option(
    "--port",
    default=COINBASE_MCP_SERVER_PORT,
    help="Port to listen on for HTTP"
)
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

    # MCP server instance
    app = Server("coinbase-mcp-server")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            # Market Data Tools (Coinbase APP)
            types.Tool(
                name="coinbase_get_prices",
                description="""
                Get current prices for specific cryptocurrencies.
                Rate limited: Conservative rate limits apply.

                Typical use: get current prices for specific cryptocurrencies.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required. List of cryptocurrency symbols in BASE-QUOTE format(e.g., ['BTC-USD', 'ETH-USD']). Must be valid Coinbase trading pairs."
                        }
                    },
                    "required": ["symbols"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_MARKET", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="coinbase_get_current_exchange_rate",
                description="""
                Get current exchange rate for specific cryptocurrencies.
                Rate limited: Conservative rate limits apply.

                Typical use: get current exchange rate for specific cryptocurrencies.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required. List of cryptocurrency symbols (e.g., ['BTC', 'ETH'])."
                        }
                    },
                    "required": ["symbols"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_MARKET", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="coinbase_get_historical_prices",
                description="""
                Get historical price data for cryptocurrencies.
                Rate limited: Conservative rate limits apply.

                Typical use: get price history with different timeframes for analysis and charts.
                Returns OHLCV (Open, High, Low, Close, Volume) candlestick data.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Required. Trading pair symbol (e.g., 'BTC-USD')."
                        },
                        "start": {
                            "type": "string",
                            "description": "Required. Start time in ISO 8601 format (e.g., '2024-01-01T00:00:00Z')."
                        },
                        "end": {
                            "type": "string",
                            "description": "Required. End time in ISO 8601 format (e.g., '2024-12-31T23:59:59Z')."
                        },
                        "granularity": {
                            "type": "integer",
                            "description": "Candle granularity in seconds. Options: 60, 300, 900, 3600, 21600, 86400."
                        }
                    },
                    "required": ["symbol", "start", "end"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_MARKET", "readOnlyHint": True}
                ),
            ),
            # Account & Portfolio Tools (requires API key)
            types.Tool(
                name="coinbase_get_accounts",
                description="""
                List user's cryptocurrency accounts.
                Rate limited: Conservative rate limits for account endpoints.

                Requires Coinbase API authentication.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_ACCOUNT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="coinbase_get_account_balance",
                description="""
                Get balance for a specific account.
                Rate limited: Conservative rate limits for account endpoints.

                Requires Coinbase API authentication.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Required. The account ID to get balance for."
                        }
                    },
                    "required": ["account_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_ACCOUNT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="coinbase_get_transactions",
                description="""
                Get transaction history for an account.
                Pagination: Use 'before' and 'after' cursors for navigation.
                Rate limited: Conservative rate limits for account endpoints.

                Requires Coinbase API authentication.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Required. The account ID to get transactions for."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of transactions to return (max 100, default 25)."
                        },
                        "before": {
                            "type": "string",
                            "description": "Optional. Return transactions before this cursor."
                        },
                        "after": {
                            "type": "string",
                            "description": "Optional. Return transactions after this cursor."
                        }
                    },
                    "required": ["account_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_ACCOUNT", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="coinbase_get_portfolio_value",
                description="""
                Get total portfolio value across all accounts.

                Requires Coinbase API authentication.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_ACCOUNT", "readOnlyHint": True}
                ),
            ),
            # Product Information Tools (Cryptocurreny)
            types.Tool(
                name="coinbase_get_product_details",
                description="""
                Get detailed cryptocurrency information.

                Typical use: get comprehensive details about a specific cryptocurrency.
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Required. The product ID (e.g., 'BTC-USD')."
                        }
                    },
                    "required": ["product_id"]
                },
                annotations=types.ToolAnnotations(
                    **{"category": "COINBASE_MARKET", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        if name == "coinbase_get_prices":
            try:
                symbols = arguments.get("symbols")

                if not symbols:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: symbols.",
                        )
                    ]

                result = await coinbase_get_prices(symbols)

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
        elif name == "coinbase_get_current_exchange_rate":
            try:
                symbols = arguments.get("symbols")

                if not symbols:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: symbols.",
                        )
                    ]

                result = await coinbase_get_current_exchange_rate(symbols)

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
        elif name == "coinbase_get_historical_prices":
            try:
                symbol = arguments.get("symbol")
                start = arguments.get("start")
                end = arguments.get("end")
                granularity = arguments.get("granularity")

                if not all([symbol, start, end]):
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: symbol, start, end.",
                        )
                    ]

                result = await coinbase_get_historical_prices(
                    symbol,
                    start,
                    end,
                    granularity
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
        elif name == "coinbase_get_accounts":
            try:
                result = await coinbase_get_accounts()

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
        elif name == "coinbase_get_account_balance":
            try:
                account_id = arguments.get("account_id")

                if not account_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: account_id.",
                        )
                    ]

                result = await coinbase_get_account_balance(account_id)

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
        elif name == "coinbase_get_transactions":
            try:
                account_id = arguments.get("account_id")

                if not account_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: account_id.",
                        )
                    ]

                result = await coinbase_get_transactions(account_id)

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
        elif name == "coinbase_get_portfolio_value":
            try:
                result = await coinbase_get_portfolio_value()

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
        elif name == "coinbase_get_product_details":
            try:
                product_id = arguments.get("product_id")

                if not product_id:
                    return [
                        types.TextContent(
                            type="text",
                            text="Missing required parameters. Required: product_id.",
                        )
                    ]

                result = await coinbase_get_product_details(product_id)
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
