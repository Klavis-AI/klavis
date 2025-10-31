"""Yahoo Finance MCP server powered by yfinance."""

from __future__ import annotations

import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Dict, List

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
    YahooFinanceError,
    fetch_dividends,
    fetch_historical_prices,
    fetch_option_chain,
    fetch_quote,
    fetch_splits,
    search_entities,
)


load_dotenv()


logger = logging.getLogger("yahoo-finance-mcp-server")

# Default configuration values
DEFAULT_REGION = "US"
DEFAULT_QUOTES_COUNT = 6
DEFAULT_CORPORATE_ACTION_LIMIT = 50
DEFAULT_OPTIONS_LIMIT = 25
YAHOO_FINANCE_MCP_SERVER_PORT = 5000


def _as_text(payload: Dict[str, Any]) -> types.TextContent:
    return types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return default


def _normalize_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@click.command()
@click.option("--port", default=YAHOO_FINANCE_MCP_SERVER_PORT, help="Port to listen on for HTTP")
@click.option("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses for StreamableHTTP instead of SSE streams",
)
def main(port: int, log_level: str, json_response: bool) -> int:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("yahoo-finance-mcp-server")

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            types.Tool(
                name="get_yahoo_finance_quote",
                description=(
                    "Live market snapshot (via yfinance) including price, day range, volume and profile metadata."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol, e.g. AAPL or MSFT.",
                        },
                        "region": {
                            "type": "string",
                            "description": "Market region (defaults to US).",
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_QUOTE", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="get_yahoo_finance_historical_prices",
                description=(
                    "Historical OHLCV candles fetched from yfinance. Supports preset range or explicit start/end."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol to query.",
                        },
                        "interval": {
                            "type": "string",
                            "description": "Sampling interval accepted by yfinance (e.g. 1d, 1wk, 1mo).",
                            "default": "1d",
                        },
                        "range": {
                            "type": "string",
                            "description": "Preset range label (e.g. 1mo, 6mo, 1y). Ignored if period_start/end provided.",
                            "default": "1mo",
                        },
                        "period_start": {
                            "type": "string",
                            "description": "ISO formatted start date. Must be paired with period_end.",
                        },
                        "period_end": {
                            "type": "string",
                            "description": "ISO formatted end date. Must be paired with period_start.",
                        },
                        "auto_adjust": {
                            "type": "boolean",
                            "description": "Pass-through to yfinance auto_adjust flag.",
                            "default": False,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_HISTORICAL", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="get_yahoo_finance_dividends",
                description=(
                    "Retrieve declared cash dividends for a symbol with optional date filter and result limit."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol to query.",
                        },
                        "period_start": {
                            "type": "string",
                            "description": "Optional ISO date to filter dividends on or after this day.",
                        },
                        "period_end": {
                            "type": "string",
                            "description": "Optional ISO date to filter dividends on or before this day.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of dividend events to return.",
                            "default": DEFAULT_CORPORATE_ACTION_LIMIT,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_DIVIDENDS", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="get_yahoo_finance_splits",
                description=(
                    "Return announced stock splits for a symbol with optional date constraints and result limit."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol to query.",
                        },
                        "period_start": {
                            "type": "string",
                            "description": "Optional ISO date to filter splits on or after this day.",
                        },
                        "period_end": {
                            "type": "string",
                            "description": "Optional ISO date to filter splits on or before this day.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of split events to return.",
                            "default": DEFAULT_CORPORATE_ACTION_LIMIT,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_SPLITS", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="search_yahoo_finance_entities",
                description=(
                    "Search Yahoo Finance instruments (via yfinance search API) using free-text queries."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Free-text query such as company name, ticker, or ISIN.",
                        },
                        "quotes_count": {
                            "type": "integer",
                            "description": "Limit the number of returned matches.",
                            "default": DEFAULT_QUOTES_COUNT,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_SEARCH", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="get_yahoo_finance_option_chain",
                description=(
                    "Fetch calls, puts, or both from the Yahoo Finance option chain for a given expiration."
                ),
                inputSchema={
                    "type": "object",
                    "required": ["symbol"],
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Ticker symbol to query.",
                        },
                        "expiration": {
                            "type": "string",
                            "description": "Specific option expiration date (YYYY-MM-DD). Defaults to nearest available.",
                        },
                        "contract_type": {
                            "type": "string",
                            "enum": ["calls", "puts", "both"],
                            "description": "Filter returned contracts to calls, puts, or both.",
                            "default": "both",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of contracts per side to return.",
                            "default": DEFAULT_OPTIONS_LIMIT,
                        },
                    },
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_OPTIONS", "readOnlyHint": True}
                ),
            ),
            types.Tool(
                name="get_yahoo_finance_config",
                description=(
                    "Get current Yahoo Finance MCP server configuration settings and defaults."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                annotations=types.ToolAnnotations(
                    **{"category": "YAHOO_FINANCE_CONFIG", "readOnlyHint": True}
                ),
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        logger.debug("call_tool=%s arguments=%s", name, json.dumps(arguments, default=str))
        try:
            if name == "get_yahoo_finance_quote":
                symbol = (arguments.get("symbol") or "").strip()
                if not symbol:
                    raise YahooFinanceError("Parameter 'symbol' is required")
                region = (arguments.get("region") or DEFAULT_REGION or None)
                result = await fetch_quote(symbol, region=region)
                return [_as_text(result)]

            if name == "get_yahoo_finance_historical_prices":
                symbol = (arguments.get("symbol") or "").strip()
                if not symbol:
                    raise YahooFinanceError("Parameter 'symbol' is required")
                interval = (arguments.get("interval") or "1d").strip()
                range_label = (arguments.get("range") or "1mo").strip()
                period_start = arguments.get("period_start")
                period_end = arguments.get("period_end")
                auto_adjust = bool(arguments.get("auto_adjust", False))
                if (period_start and not period_end) or (period_end and not period_start):
                    raise YahooFinanceError("period_start and period_end must be provided together")
                result = await fetch_historical_prices(
                    symbol,
                    interval=interval,
                    range_label=range_label,
                    period_start=period_start,
                    period_end=period_end,
                    auto_adjust=auto_adjust,
                )
                return [_as_text(result)]

            if name == "get_yahoo_finance_dividends":
                symbol = (arguments.get("symbol") or "").strip()
                if not symbol:
                    raise YahooFinanceError("Parameter 'symbol' is required")
                period_start = _normalize_optional_str(arguments.get("period_start"))
                period_end = _normalize_optional_str(arguments.get("period_end"))
                limit = _coerce_int(arguments.get("limit"), DEFAULT_CORPORATE_ACTION_LIMIT)
                result = await fetch_dividends(
                    symbol,
                    period_start=period_start,
                    period_end=period_end,
                    limit=limit,
                )
                return [_as_text(result)]

            if name == "get_yahoo_finance_splits":
                symbol = (arguments.get("symbol") or "").strip()
                if not symbol:
                    raise YahooFinanceError("Parameter 'symbol' is required")
                period_start = _normalize_optional_str(arguments.get("period_start"))
                period_end = _normalize_optional_str(arguments.get("period_end"))
                limit = _coerce_int(arguments.get("limit"), DEFAULT_CORPORATE_ACTION_LIMIT)
                result = await fetch_splits(
                    symbol,
                    period_start=period_start,
                    period_end=period_end,
                    limit=limit,
                )
                return [_as_text(result)]

            if name == "search_yahoo_finance_entities":
                query = (arguments.get("query") or "").strip()
                if not query:
                    raise YahooFinanceError("Parameter 'query' is required")
                quotes_count = _coerce_int(arguments.get("quotes_count"), DEFAULT_QUOTES_COUNT)
                result = await search_entities(query, limit=max(quotes_count, 1))
                return [_as_text(result)]

            if name == "get_yahoo_finance_option_chain":
                symbol = (arguments.get("symbol") or "").strip()
                if not symbol:
                    raise YahooFinanceError("Parameter 'symbol' is required")
                expiration = _normalize_optional_str(arguments.get("expiration"))
                contract_type = (_normalize_optional_str(arguments.get("contract_type")) or "both").lower()
                limit = _coerce_int(arguments.get("limit"), DEFAULT_OPTIONS_LIMIT)
                limit_value = limit if limit > 0 else None
                result = await fetch_option_chain(
                    symbol,
                    expiration=expiration,
                    contract_type=contract_type,
                    limit=limit_value,
                )
                return [_as_text(result)]

            if name == "get_yahoo_finance_config":
                result = {
                    "server_info": {
                        "name": "yahoo-finance-mcp-server",
                        "version": "1.0.0",
                        "description": "Yahoo Finance MCP server powered by yfinance"
                    },
                    "configuration": {
                        "default_region": DEFAULT_REGION,
                        "default_search_count": DEFAULT_QUOTES_COUNT,
                        "default_corporate_action_limit": DEFAULT_CORPORATE_ACTION_LIMIT,
                        "default_options_limit": DEFAULT_OPTIONS_LIMIT,
                        "server_port": YAHOO_FINANCE_MCP_SERVER_PORT
                    },
                    "usage_hints": {
                        "supported_regions": ["US", "CA", "AU", "GB", "DE", "FR", "IT", "ES", "HK", "JP"],
                        "available_intervals": ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
                        "available_ranges": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                        "contract_types": ["calls", "puts", "both"]
                    }
                }
                return [_as_text(result)]

            return [_as_text({"error": f"Unknown tool '{name}'"})]
        except YahooFinanceError as exc:
            logger.warning("Yahoo Finance tool error: %s", exc)
            return [_as_text({"error": str(exc)})]
        except Exception as exc:  # pragma: no cover - defensive catch
            logger.exception("Unexpected error while executing tool %s", name)
            return [_as_text({"error": f"Unexpected server error: {exc}"})]

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())
        return Response()

    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=json_response,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Yahoo Finance MCP server started")
            try:
                yield
            finally:
                logger.info("Yahoo Finance MCP server stopping")

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    logger.info("Server starting on port %s", port)
    logger.info("  - SSE endpoint: http://localhost:%s/sse", port)
    logger.info("  - StreamableHTTP endpoint: http://localhost:%s/mcp", port)

    import uvicorn

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)

    return 0


if __name__ == "__main__":
    main()
