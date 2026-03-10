# ruff: noqa: B008
import argparse
import asyncio
import base64
import contextlib
import json
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextvars import ContextVar
from enum import Enum
from typing import Any
from typing import List
from typing import Literal
from typing import Union

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send

from postgres_mcp.index.dta_calc import DatabaseTuningAdvisor

from .artifacts import ErrorResult
from .artifacts import ExplainPlanArtifact
from .database_health import DatabaseHealthTool
from .database_health import HealthType
from .explain import ExplainPlanTool
from .index.index_opt_base import MAX_NUM_INDEX_TUNING_QUERIES
from .index.llm_opt import LLMOptimizerTool
from .index.presentation import TextPresentation
from .sql import DbConnPool
from .sql import SafeSqlDriver
from .sql import SqlDriver
from .sql import check_hypopg_installation_status
from .top_queries import TopQueriesCalc

# Constants
PG_STAT_STATEMENTS = "pg_stat_statements"
HYPOPG_EXTENSION = "hypopg"

ResponseType = List[types.TextContent | types.ImageContent | types.EmbeddedResource]

logger = logging.getLogger(__name__)


class AccessMode(str, Enum):
    """SQL access modes for the server."""

    UNRESTRICTED = "unrestricted"  # Unrestricted access
    RESTRICTED = "restricted"  # Read-only with safety features


# Global variables
db_connections: dict[str, DbConnPool] = {}  # Cache connections by database URL
current_access_mode = AccessMode.UNRESTRICTED
shutdown_in_progress = False

# Context variable to store the database URL for each request
database_url_context: ContextVar[str] = ContextVar('database_url')


def extract_database_url(request_or_scope) -> str:
    """Extract database URL from x-auth-data header.
    Returns the database connection URL.
    """
    auth_data = None

    ## ---- for Klavis Cloud ---- ##
    # Handle different input types (request object for SSE, scope dict for StreamableHTTP)
    if hasattr(request_or_scope, 'headers'):
        # SSE request object
        auth_data = request_or_scope.headers.get(b'x-auth-data')
        if auth_data:
            auth_data = base64.b64decode(auth_data).decode('utf-8')
    elif isinstance(request_or_scope, dict) and 'headers' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        auth_data = headers.get(b'x-auth-data')
        if auth_data:
            auth_data = base64.b64decode(auth_data).decode('utf-8')

    ## ---- for local development ---- ##
    if not auth_data:
        # Fall back to environment variable (check DATABASE_URI)
        return os.getenv("DATABASE_URI", "")

    try:
        # Parse the JSON auth data to extract api_key (database URL)
        auth_json = json.loads(auth_data)
        return auth_json.get('api_key', '')
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse auth data JSON: {e}")
        return ""


def get_database_url() -> str:
    """Get the database URL from context."""
    try:
        return database_url_context.get()
    except LookupError:
        raise RuntimeError("Database URL not found in request context")


def get_database_url_or_empty() -> str:
    """Get the database URL from context or return empty string."""
    try:
        return database_url_context.get()
    except LookupError:
        return ""


async def get_db_connection(database_url: str) -> DbConnPool:
    """Get or create a database connection pool for the given URL."""
    if database_url not in db_connections:
        conn = DbConnPool()
        await conn.pool_connect(database_url)
        db_connections[database_url] = conn
        logger.info("Created new connection pool for database")
    return db_connections[database_url]


async def get_sql_driver() -> Union[SqlDriver, SafeSqlDriver]:
    """Get the appropriate SQL driver based on the current access mode and request context."""
    database_url = get_database_url()
    if not database_url:
        raise ValueError("No database URL provided in request. Please include database URL in x-auth-data header.")

    db_connection = await get_db_connection(database_url)
    base_driver = SqlDriver(conn=db_connection)

    if current_access_mode == AccessMode.RESTRICTED:
        logger.debug("Using SafeSqlDriver with restrictions (RESTRICTED mode)")
        return SafeSqlDriver(sql_driver=base_driver, timeout=30)  # 30 second timeout
    else:
        logger.debug("Using unrestricted SqlDriver (UNRESTRICTED mode)")
        return base_driver


def format_text_response(text: Any) -> ResponseType:
    """Format a text response."""
    return [types.TextContent(type="text", text=str(text))]


def format_error_response(error: str) -> ResponseType:
    """Format an error response."""
    return format_text_response(f"Error: {error}")


# Tool implementations
async def list_schemas_tool() -> ResponseType:
    """List all schemas in the database."""
    try:
        sql_driver = await get_sql_driver()
        rows = await sql_driver.execute_query(
            """
            SELECT
                schema_name,
                schema_owner,
                CASE
                    WHEN schema_name LIKE 'pg_%' THEN 'System Schema'
                    WHEN schema_name = 'information_schema' THEN 'System Information Schema'
                    ELSE 'User Schema'
                END as schema_type
            FROM information_schema.schemata
            ORDER BY schema_type, schema_name
            """
        )
        schemas = [row.cells for row in rows] if rows else []
        return format_text_response(schemas)
    except Exception as e:
        logger.error(f"Error listing schemas: {e}")
        return format_error_response(str(e))


async def list_objects_tool(
    schema_name: str,
    object_type: str = "table",
) -> ResponseType:
    """List objects of a given type in a schema."""
    try:
        sql_driver = await get_sql_driver()

        if object_type in ("table", "view"):
            table_type = "BASE TABLE" if object_type == "table" else "VIEW"
            rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = {} AND table_type = {}
                ORDER BY table_name
                """,
                [schema_name, table_type],
            )
            objects = (
                [{"schema": row.cells["table_schema"], "name": row.cells["table_name"], "type": row.cells["table_type"]} for row in rows]
                if rows
                else []
            )

        elif object_type == "sequence":
            rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT sequence_schema, sequence_name, data_type
                FROM information_schema.sequences
                WHERE sequence_schema = {}
                ORDER BY sequence_name
                """,
                [schema_name],
            )
            objects = (
                [{"schema": row.cells["sequence_schema"], "name": row.cells["sequence_name"], "data_type": row.cells["data_type"]} for row in rows]
                if rows
                else []
            )

        elif object_type == "extension":
            # Extensions are not schema-specific
            rows = await sql_driver.execute_query(
                """
                SELECT extname, extversion, extrelocatable
                FROM pg_extension
                ORDER BY extname
                """
            )
            objects = (
                [{"name": row.cells["extname"], "version": row.cells["extversion"], "relocatable": row.cells["extrelocatable"]} for row in rows]
                if rows
                else []
            )

        else:
            return format_error_response(f"Unsupported object type: {object_type}")

        return format_text_response(objects)
    except Exception as e:
        logger.error(f"Error listing objects: {e}")
        return format_error_response(str(e))


async def get_object_details_tool(
    schema_name: str,
    object_name: str,
    object_type: str = "table",
) -> ResponseType:
    """Get detailed information about a database object."""
    try:
        sql_driver = await get_sql_driver()

        if object_type in ("table", "view"):
            # Get columns
            col_rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = {} AND table_name = {}
                ORDER BY ordinal_position
                """,
                [schema_name, object_name],
            )
            columns = (
                [
                    {
                        "column": r.cells["column_name"],
                        "data_type": r.cells["data_type"],
                        "is_nullable": r.cells["is_nullable"],
                        "default": r.cells["column_default"],
                    }
                    for r in col_rows
                ]
                if col_rows
                else []
            )

            # Get constraints
            con_rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
                FROM information_schema.table_constraints AS tc
                LEFT JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = {} AND tc.table_name = {}
                """,
                [schema_name, object_name],
            )

            constraints = {}
            if con_rows:
                for row in con_rows:
                    cname = row.cells["constraint_name"]
                    ctype = row.cells["constraint_type"]
                    col = row.cells["column_name"]

                    if cname not in constraints:
                        constraints[cname] = {"type": ctype, "columns": []}
                    if col:
                        constraints[cname]["columns"].append(col)

            constraints_list = [{"name": name, **data} for name, data in constraints.items()]

            # Get indexes
            idx_rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = {} AND tablename = {}
                """,
                [schema_name, object_name],
            )

            indexes = [{"name": r.cells["indexname"], "definition": r.cells["indexdef"]} for r in idx_rows] if idx_rows else []

            result = {
                "basic": {"schema": schema_name, "name": object_name, "type": object_type},
                "columns": columns,
                "constraints": constraints_list,
                "indexes": indexes,
            }

        elif object_type == "sequence":
            rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT sequence_schema, sequence_name, data_type, start_value, increment
                FROM information_schema.sequences
                WHERE sequence_schema = {} AND sequence_name = {}
                """,
                [schema_name, object_name],
            )

            if rows and rows[0]:
                row = rows[0]
                result = {
                    "schema": row.cells["sequence_schema"],
                    "name": row.cells["sequence_name"],
                    "data_type": row.cells["data_type"],
                    "start_value": row.cells["start_value"],
                    "increment": row.cells["increment"],
                }
            else:
                result = {}

        elif object_type == "extension":
            rows = await SafeSqlDriver.execute_param_query(
                sql_driver,
                """
                SELECT extname, extversion, extrelocatable
                FROM pg_extension
                WHERE extname = {}
                """,
                [object_name],
            )

            if rows and rows[0]:
                row = rows[0]
                result = {"name": row.cells["extname"], "version": row.cells["extversion"], "relocatable": row.cells["extrelocatable"]}
            else:
                result = {}

        else:
            return format_error_response(f"Unsupported object type: {object_type}")

        return format_text_response(result)
    except Exception as e:
        logger.error(f"Error getting object details: {e}")
        return format_error_response(str(e))


async def explain_query_tool(
    sql: str,
    analyze: bool = False,
    hypothetical_indexes: list[dict[str, Any]] | None = None,
) -> ResponseType:
    """Explains the execution plan for a SQL query."""
    if hypothetical_indexes is None:
        hypothetical_indexes = []
    try:
        sql_driver = await get_sql_driver()
        explain_tool = ExplainPlanTool(sql_driver=sql_driver)
        result: ExplainPlanArtifact | ErrorResult | None = None

        # If hypothetical indexes are specified, check for HypoPG extension
        if hypothetical_indexes and len(hypothetical_indexes) > 0:
            if analyze:
                return format_error_response("Cannot use analyze and hypothetical indexes together")
            try:
                # Use the common utility function to check if hypopg is installed
                (
                    is_hypopg_installed,
                    hypopg_message,
                ) = await check_hypopg_installation_status(sql_driver)

                # If hypopg is not installed, return the message
                if not is_hypopg_installed:
                    return format_text_response(hypopg_message)

                # HypoPG is installed, proceed with explaining with hypothetical indexes
                result = await explain_tool.explain_with_hypothetical_indexes(sql, hypothetical_indexes)
            except Exception:
                raise  # Re-raise the original exception
        elif analyze:
            try:
                # Use EXPLAIN ANALYZE
                result = await explain_tool.explain_analyze(sql)
            except Exception:
                raise  # Re-raise the original exception
        else:
            try:
                # Use basic EXPLAIN
                result = await explain_tool.explain(sql)
            except Exception:
                raise  # Re-raise the original exception

        if result and isinstance(result, ExplainPlanArtifact):
            return format_text_response(result.to_text())
        else:
            error_message = "Error processing explain plan"
            if isinstance(result, ErrorResult):
                error_message = result.to_text()
            return format_error_response(error_message)
    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        return format_error_response(str(e))


async def execute_sql_tool(sql: str) -> ResponseType:
    """Executes a SQL query against the database."""
    try:
        sql_driver = await get_sql_driver()
        rows = await sql_driver.execute_query(sql)  # type: ignore
        if rows is None:
            return format_text_response("No results")
        return format_text_response(list([r.cells for r in rows]))
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return format_error_response(str(e))


async def analyze_workload_indexes_tool(
    max_index_size_mb: int = 10000,
    method: Literal["dta", "llm"] = "dta",
) -> ResponseType:
    """Analyze frequently executed queries in the database and recommend optimal indexes."""
    try:
        sql_driver = await get_sql_driver()
        if method == "dta":
            index_tuning = DatabaseTuningAdvisor(sql_driver)
        else:
            index_tuning = LLMOptimizerTool(sql_driver)
        dta_tool = TextPresentation(sql_driver, index_tuning)
        result = await dta_tool.analyze_workload(max_index_size_mb=max_index_size_mb)
        return format_text_response(result)
    except Exception as e:
        logger.error(f"Error analyzing workload: {e}")
        return format_error_response(str(e))


async def analyze_query_indexes_tool(
    queries: list[str],
    max_index_size_mb: int = 10000,
    method: Literal["dta", "llm"] = "dta",
) -> ResponseType:
    """Analyze a list of SQL queries and recommend optimal indexes."""
    if len(queries) == 0:
        return format_error_response("Please provide a non-empty list of queries to analyze.")
    if len(queries) > MAX_NUM_INDEX_TUNING_QUERIES:
        return format_error_response(f"Please provide a list of up to {MAX_NUM_INDEX_TUNING_QUERIES} queries to analyze.")

    try:
        sql_driver = await get_sql_driver()
        if method == "dta":
            index_tuning = DatabaseTuningAdvisor(sql_driver)
        else:
            index_tuning = LLMOptimizerTool(sql_driver)
        dta_tool = TextPresentation(sql_driver, index_tuning)
        result = await dta_tool.analyze_queries(queries=queries, max_index_size_mb=max_index_size_mb)
        return format_text_response(result)
    except Exception as e:
        logger.error(f"Error analyzing queries: {e}")
        return format_error_response(str(e))


async def analyze_db_health_tool(health_type: str = "all") -> ResponseType:
    """Analyze database health for specified components."""
    health_tool = DatabaseHealthTool(await get_sql_driver())
    result = await health_tool.health(health_type=health_type)
    return format_text_response(result)


async def get_top_queries_tool(
    sort_by: str = "resources",
    limit: int = 10,
) -> ResponseType:
    """Reports the slowest or most resource-intensive queries."""
    try:
        sql_driver = await get_sql_driver()
        top_queries_tool = TopQueriesCalc(sql_driver=sql_driver)

        if sort_by == "resources":
            result = await top_queries_tool.get_top_resource_queries()
            return format_text_response(result)
        elif sort_by == "mean_time" or sort_by == "total_time":
            # Map the sort_by values to what get_top_queries_by_time expects
            result = await top_queries_tool.get_top_queries_by_time(limit=limit, sort_by="mean" if sort_by == "mean_time" else "total")
        else:
            return format_error_response("Invalid sort criteria. Please use 'resources' or 'mean_time' or 'total_time'.")
        return format_text_response(result)
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        return format_error_response(str(e))


def create_server(access_mode: AccessMode) -> Server:
    """Create and configure the MCP server."""
    app = Server("postgres-mcp")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        tools = [
            types.Tool(
                name="list_schemas",
                description="List all schemas in the database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
                annotations=ToolAnnotations(title="List Schemas", readOnlyHint=True),
            ),
            types.Tool(
                name="list_objects",
                description="List objects in a schema",
                inputSchema={
                    "type": "object",
                    "required": ["schema_name"],
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name",
                        },
                        "object_type": {
                            "type": "string",
                            "description": "Object type: 'table', 'view', 'sequence', or 'extension'",
                            "default": "table",
                        },
                    },
                },
                annotations=ToolAnnotations(title="List Objects", readOnlyHint=True),
            ),
            types.Tool(
                name="get_object_details",
                description="Show detailed information about a database object",
                inputSchema={
                    "type": "object",
                    "required": ["schema_name", "object_name"],
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name",
                        },
                        "object_name": {
                            "type": "string",
                            "description": "Object name",
                        },
                        "object_type": {
                            "type": "string",
                            "description": "Object type: 'table', 'view', 'sequence', or 'extension'",
                            "default": "table",
                        },
                    },
                },
                annotations=ToolAnnotations(title="Get Object Details", readOnlyHint=True),
            ),
            types.Tool(
                name="explain_query",
                description="Explains the execution plan for a SQL query, showing how the database will execute it and provides detailed cost estimates.",
                inputSchema={
                    "type": "object",
                    "required": ["sql"],
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to explain",
                        },
                        "analyze": {
                            "type": "boolean",
                            "description": "When True, actually runs the query to show real execution statistics instead of estimates.",
                            "default": False,
                        },
                        "hypothetical_indexes": {
                            "type": "array",
                            "description": "A list of hypothetical indexes to simulate.",
                            "items": {"type": "object"},
                            "default": [],
                        },
                    },
                },
                annotations=ToolAnnotations(title="Explain Query", readOnlyHint=True),
            ),
            types.Tool(
                name="analyze_workload_indexes",
                description="Analyze frequently executed queries in the database and recommend optimal indexes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "max_index_size_mb": {
                            "type": "integer",
                            "description": "Max index size in MB",
                            "default": 10000,
                        },
                        "method": {
                            "type": "string",
                            "enum": ["dta", "llm"],
                            "description": "Method to use for analysis",
                            "default": "dta",
                        },
                    },
                },
                annotations=ToolAnnotations(title="Analyze Workload Indexes", readOnlyHint=True),
            ),
            types.Tool(
                name="analyze_query_indexes",
                description="Analyze a list of (up to 10) SQL queries and recommend optimal indexes",
                inputSchema={
                    "type": "object",
                    "required": ["queries"],
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of Query strings to analyze",
                        },
                        "max_index_size_mb": {
                            "type": "integer",
                            "description": "Max index size in MB",
                            "default": 10000,
                        },
                        "method": {
                            "type": "string",
                            "enum": ["dta", "llm"],
                            "description": "Method to use for analysis",
                            "default": "dta",
                        },
                    },
                },
                annotations=ToolAnnotations(title="Analyze Query Indexes", readOnlyHint=True),
            ),
            types.Tool(
                name="analyze_db_health",
                description="Analyzes database health. Here are the available health checks:\n"
                "- index - checks for invalid, duplicate, and bloated indexes\n"
                "- connection - checks the number of connection and their utilization\n"
                "- vacuum - checks vacuum health for transaction id wraparound\n"
                "- sequence - checks sequences at risk of exceeding their maximum value\n"
                "- replication - checks replication health including lag and slots\n"
                "- buffer - checks for buffer cache hit rates for indexes and tables\n"
                "- constraint - checks for invalid constraints\n"
                "- all - runs all checks\n"
                "You can optionally specify a single health check or a comma-separated list of health checks. The default is 'all' checks.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "health_type": {
                            "type": "string",
                            "description": f"Optional. Valid values are: {', '.join(sorted([t.value for t in HealthType]))}.",
                            "default": "all",
                        },
                    },
                },
                annotations=ToolAnnotations(title="Analyze Database Health", readOnlyHint=True),
            ),
            types.Tool(
                name="get_top_queries",
                description=f"Reports the slowest or most resource-intensive queries using data from the '{PG_STAT_STATEMENTS}' extension.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sort_by": {
                            "type": "string",
                            "description": "Ranking criteria: 'total_time' for total execution time or 'mean_time' for mean execution time per call, or 'resources' for resource-intensive queries",
                            "default": "resources",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of queries to return when ranking based on mean_time or total_time",
                            "default": 10,
                        },
                    },
                },
                annotations=ToolAnnotations(title="Get Top Queries", readOnlyHint=True),
            ),
        ]

        # Add execute_sql tool with appropriate permissions based on access mode
        if access_mode == AccessMode.UNRESTRICTED:
            tools.append(
                types.Tool(
                    name="execute_sql",
                    description="Execute any SQL query",
                    inputSchema={
                        "type": "object",
                        "required": ["sql"],
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL to run",
                            },
                        },
                    },
                    annotations=ToolAnnotations(title="Execute SQL", destructiveHint=True),
                )
            )
        else:
            tools.append(
                types.Tool(
                    name="execute_sql",
                    description="Execute a read-only SQL query",
                    inputSchema={
                        "type": "object",
                        "required": ["sql"],
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL to run",
                            },
                        },
                    },
                    annotations=ToolAnnotations(title="Execute SQL (Read-Only)", readOnlyHint=True),
                )
            )

        return tools

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        try:
            if name == "list_schemas":
                return await list_schemas_tool()
            elif name == "list_objects":
                return await list_objects_tool(
                    schema_name=arguments.get("schema_name", ""),
                    object_type=arguments.get("object_type", "table"),
                )
            elif name == "get_object_details":
                return await get_object_details_tool(
                    schema_name=arguments.get("schema_name", ""),
                    object_name=arguments.get("object_name", ""),
                    object_type=arguments.get("object_type", "table"),
                )
            elif name == "explain_query":
                return await explain_query_tool(
                    sql=arguments.get("sql", ""),
                    analyze=arguments.get("analyze", False),
                    hypothetical_indexes=arguments.get("hypothetical_indexes", []),
                )
            elif name == "execute_sql":
                return await execute_sql_tool(sql=arguments.get("sql", ""))
            elif name == "analyze_workload_indexes":
                return await analyze_workload_indexes_tool(
                    max_index_size_mb=arguments.get("max_index_size_mb", 10000),
                    method=arguments.get("method", "dta"),
                )
            elif name == "analyze_query_indexes":
                return await analyze_query_indexes_tool(
                    queries=arguments.get("queries", []),
                    max_index_size_mb=arguments.get("max_index_size_mb", 10000),
                    method=arguments.get("method", "dta"),
                )
            elif name == "analyze_db_health":
                return await analyze_db_health_tool(
                    health_type=arguments.get("health_type", "all"),
                )
            elif name == "get_top_queries":
                return await get_top_queries_tool(
                    sort_by=arguments.get("sort_by", "resources"),
                    limit=arguments.get("limit", 10),
                )
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.exception(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    return app


async def run_stdio(app: Server):
    """Run the server with stdio transport."""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PostgreSQL MCP Server")
    parser.add_argument(
        "--access-mode",
        type=str,
        choices=[mode.value for mode in AccessMode],
        default=AccessMode.UNRESTRICTED.value,
        help="Set SQL access mode: unrestricted (unrestricted) or restricted (read-only with protections)",
    )
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "streamable-http"],
        default="streamable-http",
        help="Select MCP transport: stdio (default), sse, or streamable-http",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for server (default: 5000)",
    )

    args = parser.parse_args()

    # Store the access mode in the global variable
    global current_access_mode
    current_access_mode = AccessMode(args.access_mode)

    logger.info(f"Starting PostgreSQL MCP Server in {current_access_mode.value.upper()} mode")
    logger.info("Database connections will be established per-request from x-auth-data header")

    # Create the MCP server
    app = create_server(current_access_mode)

    if args.transport == "stdio":
        asyncio.run(run_stdio(app))
        return

    # HTTP-based transports (SSE and StreamableHTTP)
    # Set up SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")

        # Extract database URL from headers
        db_url = extract_database_url(request)

        # Set the database URL in context for this request
        token = database_url_context.set(db_url)
        try:
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        finally:
            database_url_context.reset(token)

        return Response()

    # Set up StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        logger.info("Handling StreamableHTTP request")

        # Extract database URL from headers
        db_url = extract_database_url(scope)

        # Set the database URL in context for this request
        token = database_url_context.set(db_url)
        try:
            await session_manager.handle_request(scope, receive, send)
        finally:
            database_url_context.reset(token)

    @contextlib.asynccontextmanager
    async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
        """Context manager for session manager."""
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")
                # Close all database connections
                for _, conn in db_connections.items():
                    try:
                        await conn.close()
                        logger.info("Closed database connection")
                    except Exception as e:
                        logger.error(f"Error closing database connection: {e}")
                db_connections.clear()

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

    logger.info(f"Server starting on {args.host}:{args.port} with dual transports:")
    logger.info(f"  - SSE endpoint: http://{args.host}:{args.port}/sse")
    logger.info(f"  - StreamableHTTP endpoint: http://{args.host}:{args.port}/mcp")

    import uvicorn
    uvicorn.run(starlette_app, host=args.host, port=args.port)


async def shutdown(sig=None):
    """Clean shutdown of the server."""
    global shutdown_in_progress

    if shutdown_in_progress:
        logger.warning("Forcing immediate exit")
        sys.exit(1)

    shutdown_in_progress = True

    if sig:
        logger.info(f"Received exit signal {sig.name}")

    # Close all database connections
    for _, conn in db_connections.items():
        try:
            await conn.close()
            logger.info("Closed database connection")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
    db_connections.clear()

    sys.exit(128 + sig if sig is not None else 0)


if __name__ == "__main__":
    main()
