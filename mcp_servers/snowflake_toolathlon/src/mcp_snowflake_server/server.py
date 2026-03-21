import contextlib
import contextvars
import base64
import importlib.metadata
import json
import logging
import os
import re
from functools import wraps
from typing import Any, Callable
from collections.abc import AsyncIterator

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pydantic import AnyUrl, BaseModel
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
import uvicorn

from .db_client import SnowflakeDB
from .write_detector import SQLWriteDetector
from .serialization import to_yaml, to_json

ResponseType = types.TextContent | types.ImageContent | types.EmbeddedResource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("mcp_snowflake_server")

# Regex for validating SQL identifiers (database, schema, table names).
# Allows alphanumeric characters and underscores; must start with a letter or underscore.
_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]{0,255}$')


def validate_identifier(name: str, kind: str = "identifier") -> str:
    """Validate that a string is a safe SQL identifier.

    Raises ValueError if the name contains characters outside the allowed set.
    Returns the validated name (stripped of leading/trailing whitespace).
    """
    name = name.strip()
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"Invalid {kind} name: {name!r}. "
            f"Only alphanumeric characters and underscores are allowed, "
            f"and the name must start with a letter or underscore."
        )
    return name


# Context for request-specific connection arguments
connection_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "connection_context", default=None
)


def extract_credentials(request_or_scope) -> dict[str, Any] | None:
    """Extract credentials from x-auth-data header."""
    auth_data = None
    
    if hasattr(request_or_scope, 'headers'):
        # SSE request object (Starlette Request)
        auth_data = request_or_scope.headers.get('x-auth-data')
    elif isinstance(request_or_scope, dict) and 'type' in request_or_scope:
        # StreamableHTTP scope object
        headers = dict(request_or_scope.get("headers", []))
        # keys are bytes, lowercased
        auth_data_bytes = headers.get(b'x-auth-data')
        if auth_data_bytes:
            auth_data = auth_data_bytes.decode('utf-8')
    
    if auth_data:
        try:
            # Decode base64 then parse JSON
            decoded = base64.b64decode(auth_data).decode('utf-8')
            creds_json = json.loads(decoded)
            
            # Map keys to Snowflake connection config format
            mapped_creds = {}
            mapping = {
                "SNOWFLAKE_ACCOUNT": "account",
                "SNOWFLAKE_USER": "user",
                "SNOWFLAKE_ROLE": "role",
                "SNOWFLAKE_DATABASE": "database",
                "SNOWFLAKE_SCHEMA": "schema",
                "SNOWFLAKE_WAREHOUSE": "warehouse",
                "SNOWFLAKE_PRIVATE_KEY": "private_key_content",
            }
            
            for env_key, config_key in mapping.items():
                if env_key in creds_json:
                    mapped_creds[config_key] = creds_json[env_key]
            
            return mapped_creds if mapped_creds else None
            
        except Exception as e:
            logger.warning("Failed to parse x-auth-data header")
            return None
            
    return None




def handle_tool_errors(func: Callable) -> Callable:
    """Decorator to standardize tool error handling"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> list[types.TextContent]:
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # ValueError is used for expected validation errors — safe to return
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
        except Exception as e:
            # For unexpected errors, log the details but return a generic message
            # to avoid leaking credentials or internal details to clients
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: An internal error occurred in {func.__name__}. Check server logs for details.")]

    return wrapper


def check_database_access(database_name: str, allowed_databases: list[str] | None = None) -> None:
    """Check if database access is allowed based on allowed_databases restriction"""
    if allowed_databases is not None:
        if database_name not in allowed_databases:
            raise ValueError(f"Access denied: Database '{database_name}' is not in the allowed databases list: {allowed_databases}")


def extract_database_from_query(query: str) -> str | None:
    """Extract database name from SQL query using basic parsing"""
    # Convert to uppercase for easier matching
    query_upper = query.upper().strip()
    
    # For CREATE/DROP DATABASE commands
    if "CREATE DATABASE" in query_upper or "DROP DATABASE" in query_upper:
        tokens = query_upper.split()
        try:
            db_index = tokens.index("DATABASE") + 1
            if db_index < len(tokens):
                return tokens[db_index].strip(';')
        except (ValueError, IndexError):
            pass
    
    # For USE DATABASE commands
    if query_upper.startswith("USE"):
        tokens = query_upper.split()
        if len(tokens) >= 2:
            return tokens[1].strip(';')
    
    # For qualified table references like database.schema.table
    qualified_match = re.search(r'\b([A-Z_][A-Z0-9_]*)\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*', query_upper)
    if qualified_match:
        return qualified_match.group(1)
    
    return None


class Tool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[str, dict[str, Any] | None], list[ResponseType]]
    tags: list[str] = []


# Tool handlers
async def handle_list_databases(arguments, db, *_, exclusion_config=None, exclude_json_results=False, allowed_databases=None, **__):
    query = "SHOW DATABASES"
    data, data_id = await db.execute_query(query)

    # Filter to only allowed databases if restriction is set
    if allowed_databases is not None:
        allowed_db_set = {db.upper() for db in allowed_databases}
        data = [item for item in data if item.get("name", "").upper() in allowed_db_set]

    # Filter out excluded databases
    if exclusion_config and "databases" in exclusion_config and exclusion_config["databases"]:
        filtered_data = []
        for item in data:
            db_name = item.get("name", "")
            exclude = False
            for pattern in exclusion_config["databases"]:
                if pattern.lower() in db_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"), text=json_output, mimeType="application/json"
                ),
            )
        )
    return results


async def handle_list_schemas(arguments, db, *_, exclusion_config=None, exclude_json_results=False, allowed_databases=None, **__):
    if not arguments or "database" not in arguments:
        raise ValueError("Missing required 'database' parameter")

    database = validate_identifier(arguments["database"], "database")
    
    # Check allowed databases restriction
    check_database_access(database, allowed_databases)
    query = f"SELECT SCHEMA_NAME FROM {database.upper()}.INFORMATION_SCHEMA.SCHEMATA"
    data, data_id = await db.execute_query(query)

    # Filter out excluded schemas
    if exclusion_config and "schemas" in exclusion_config and exclusion_config["schemas"]:
        filtered_data = []
        for item in data:
            schema_name = item.get("SCHEMA_NAME", "")
            exclude = False
            for pattern in exclusion_config["schemas"]:
                if pattern.lower() in schema_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"), text=json_output, mimeType="application/json"
                ),
            )
        )
    return results


async def handle_list_tables(arguments, db, *_, exclusion_config=None, exclude_json_results=False, allowed_databases=None, **__):
    if not arguments or "database" not in arguments or "schema" not in arguments:
        raise ValueError("Missing required 'database' and 'schema' parameters")

    database = validate_identifier(arguments["database"], "database")
    schema = validate_identifier(arguments["schema"], "schema")
    
    # Check allowed databases restriction
    check_database_access(database, allowed_databases)

    query = f"""
        SELECT table_catalog, table_schema, table_name, comment 
        FROM {database}.information_schema.tables 
        WHERE table_schema = '{schema.upper()}'
    """
    data, data_id = await db.execute_query(query)

    # Filter out excluded tables
    if exclusion_config and "tables" in exclusion_config and exclusion_config["tables"]:
        filtered_data = []
        for item in data:
            table_name = item.get("TABLE_NAME", "")
            exclude = False
            for pattern in exclusion_config["tables"]:
                if pattern.lower() in table_name.lower():
                    exclude = True
                    break
            if not exclude:
                filtered_data.append(item)
        data = filtered_data

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database,
        "schema": schema,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"), text=json_output, mimeType="application/json"
                ),
            )
        )
    return results


async def handle_describe_table(arguments, db, *_, exclude_json_results=False, allowed_databases=None, **__):
    if not arguments or "table_name" not in arguments:
        raise ValueError("Missing table_name argument")

    table_spec = arguments["table_name"]
    split_identifier = table_spec.split(".")

    # Parse the fully qualified table name
    if len(split_identifier) < 3:
        raise ValueError("Table name must be fully qualified as 'database.schema.table'")

    database_name = validate_identifier(split_identifier[0], "database").upper()
    schema_name = validate_identifier(split_identifier[1], "schema").upper()
    table_name = validate_identifier(split_identifier[2], "table").upper()
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)

    query = f"""
        SELECT column_name, column_default, is_nullable, data_type, comment 
        FROM {database_name}.information_schema.columns 
        WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
    """
    data, data_id = await db.execute_query(query)

    output = {
        "type": "data",
        "data_id": data_id,
        "database": database_name,
        "schema": schema_name,
        "table": table_name,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"), text=json_output, mimeType="application/json"
                ),
            )
        )
    return results


async def handle_read_query(arguments, db, write_detector, *_, exclude_json_results=False, allowed_databases=None, **__):
    if not arguments or "query" not in arguments:
        raise ValueError("Missing query argument")

    if write_detector.analyze_query(arguments["query"])["contains_write"]:
        raise ValueError("Calls to read_query should not contain write operations")
    
    # Check database access if allowed_databases is specified
    if allowed_databases is not None:
        extracted_db = extract_database_from_query(arguments["query"])
        if extracted_db:
            check_database_access(extracted_db, allowed_databases)

    data, data_id = await db.execute_query(arguments["query"])

    output = {
        "type": "data",
        "data_id": data_id,
        "data": data,
    }
    yaml_output = to_yaml(output)
    json_output = to_json(output)
    results: list[ResponseType] = [types.TextContent(type="text", text=yaml_output)]
    if not exclude_json_results:
        results.append(
            types.EmbeddedResource(
                type="resource",
                resource=types.TextResourceContents(
                    uri=AnyUrl(f"data://{data_id}"), text=json_output, mimeType="application/json"
                ),
            )
        )
    return results


async def handle_append_insight(arguments, db, _, __, server, exclude_json_results=False):
    if not arguments or "insight" not in arguments:
        raise ValueError("Missing insight argument")

    db.add_insight(arguments["insight"])
    await server.request_context.session.send_resource_updated(AnyUrl("memo://insights"))
    return [types.TextContent(type="text", text="Insight added to memo")]


async def handle_write_query(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if arguments["query"].strip().upper().startswith("SELECT"):
        raise ValueError("SELECT queries are not allowed for write_query")

    # Check database access if allowed_databases is specified
    if allowed_databases is not None:
        extracted_db = extract_database_from_query(arguments["query"])
        if extracted_db:
            check_database_access(extracted_db, allowed_databases)

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=str(results))]


async def handle_create_databases(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "databases" not in arguments:
        raise ValueError("Missing required 'databases' parameter")
    
    database_names = arguments["databases"]
    if not isinstance(database_names, list):
        raise ValueError("'databases' parameter must be a list of database names")
    
    results = []
    warnings = []
    
    # Validate all database names and check allowed databases restriction
    real_database_names = []
    for db_name in database_names:
        validate_identifier(db_name, "database")
        try:
            check_database_access(db_name, allowed_databases)
            real_database_names.append(db_name)
        except Exception as e:
            warnings.append(f"Warning: Creating database '{db_name}' is not allowed, you can only create databases in the following list: {allowed_databases}")
    
    existing_dbs_result, _ = await db.execute_query("SHOW DATABASES")
    existing_db_names = {row["name"].upper() for row in existing_dbs_result}
    
    for db_name in real_database_names:
        db_name_upper = db_name.upper()
        if db_name_upper in existing_db_names:
            warnings.append(f"Warning: Database '{db_name}' already exists, skipping creation")
        else:
            try:
                create_result, _ = await db.execute_query(f"CREATE DATABASE {db_name}")
                results.append(f"Successfully created database '{db_name}'")
            except Exception as e:
                results.append(f"Failed to create database '{db_name}': {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_drop_databases(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "databases" not in arguments:
        raise ValueError("Missing required 'databases' parameter")
    
    database_names = arguments["databases"]
    if not isinstance(database_names, list):
        raise ValueError("'databases' parameter must be a list of database names")
    
    results = []
    warnings = []
    
    # Validate all database names and check allowed databases restriction
    for db_name in database_names:
        validate_identifier(db_name, "database")
        check_database_access(db_name, allowed_databases)
    
    existing_dbs_result, _ = await db.execute_query("SHOW DATABASES")
    existing_db_names = {row["name"].upper() for row in existing_dbs_result}
    
    for db_name in database_names:
        db_name_upper = db_name.upper()
        if db_name_upper not in existing_db_names:
            warnings.append(f"Warning: Database '{db_name}' does not exist, skipping deletion")
        else:
            try:
                drop_result, _ = await db.execute_query(f"DROP DATABASE {db_name}")
                results.append(f"Successfully dropped database '{db_name}'")
            except Exception as e:
                results.append(f"Failed to drop database '{db_name}': {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_create_schemas(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "database" not in arguments or "schemas" not in arguments:
        raise ValueError("Missing required 'database' and 'schemas' parameters")
    
    database_name = validate_identifier(arguments["database"], "database")
    schema_names = arguments["schemas"]
    
    if not isinstance(schema_names, list):
        raise ValueError("'schemas' parameter must be a list of schema names")
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)
    
    results = []
    warnings = []
    
    # Get existing schemas to check for duplicates
    try:
        existing_schemas_result, _ = await db.execute_query(f"SELECT SCHEMA_NAME FROM {database_name}.INFORMATION_SCHEMA.SCHEMATA")
        existing_schema_names = {row["SCHEMA_NAME"].upper() for row in existing_schemas_result}
    except Exception as e:
        return [types.TextContent(type="text", text=f"Failed to check existing schemas in database '{database_name}': {str(e)}")]
    
    for schema_name in schema_names:
        schema_name = validate_identifier(schema_name, "schema")
        schema_name_upper = schema_name.upper()
        if schema_name_upper in existing_schema_names:
            warnings.append(f"Warning: Schema '{schema_name}' already exists in database '{database_name}', skipping creation")
        else:
            try:
                create_result, _ = await db.execute_query(f"CREATE SCHEMA {database_name}.{schema_name}")
                results.append(f"Successfully created schema '{schema_name}' in database '{database_name}'")
            except Exception as e:
                results.append(f"Failed to create schema '{schema_name}' in database '{database_name}': {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_drop_schemas(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "database" not in arguments or "schemas" not in arguments:
        raise ValueError("Missing required 'database' and 'schemas' parameters")
    
    database_name = validate_identifier(arguments["database"], "database")
    schema_names = arguments["schemas"]
    
    if not isinstance(schema_names, list):
        raise ValueError("'schemas' parameter must be a list of schema names")
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)
    
    results = []
    warnings = []
    
    # Get existing schemas to check for non-existent ones
    try:
        existing_schemas_result, _ = await db.execute_query(f"SELECT SCHEMA_NAME FROM {database_name}.INFORMATION_SCHEMA.SCHEMATA")
        existing_schema_names = {row["SCHEMA_NAME"].upper() for row in existing_schemas_result}
    except Exception as e:
        return [types.TextContent(type="text", text=f"Failed to check existing schemas in database '{database_name}': {str(e)}")]
    
    for schema_name in schema_names:
        schema_name = validate_identifier(schema_name, "schema")
        schema_name_upper = schema_name.upper()
        if schema_name_upper not in existing_schema_names:
            warnings.append(f"Warning: Schema '{schema_name}' does not exist in database '{database_name}', skipping deletion")
        else:
            try:
                drop_result, _ = await db.execute_query(f"DROP SCHEMA {database_name}.{schema_name}")
                results.append(f"Successfully dropped schema '{schema_name}' from database '{database_name}'")
            except Exception as e:
                results.append(f"Failed to drop schema '{schema_name}' from database '{database_name}': {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_create_tables(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "database" not in arguments or "schema" not in arguments or "tables" not in arguments:
        raise ValueError("Missing required 'database', 'schema', and 'tables' parameters")
    
    database_name = validate_identifier(arguments["database"], "database")
    schema_name = validate_identifier(arguments["schema"], "schema")
    table_definitions = arguments["tables"]
    
    if not isinstance(table_definitions, list):
        raise ValueError("'tables' parameter must be a list of table definitions")
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)
    
    results = []
    warnings = []
    
    # Get existing tables to check for duplicates
    try:
        existing_tables_result, _ = await db.execute_query(
            f"SELECT TABLE_NAME FROM {database_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name.upper()}'"
        )
        existing_table_names = {row["TABLE_NAME"].upper() for row in existing_tables_result}
    except Exception as e:
        return [types.TextContent(type="text", text=f"Failed to check existing tables in {database_name}.{schema_name}: {str(e)}")]
    
    for table_def in table_definitions:
        if isinstance(table_def, dict) and "name" in table_def and "definition" in table_def:
            table_name = table_def["name"]
            table_definition = table_def["definition"]
        elif isinstance(table_def, str):
            # Simple format: just the CREATE TABLE SQL
            table_definition = table_def
            # Try to extract table name from SQL
            match = re.search(r'CREATE\s+TABLE\s+(\w+)', table_definition.upper())
            table_name = match.group(1) if match else "UNKNOWN"
        else:
            results.append(f"Invalid table definition format: {table_def}")
            continue

        # Validate the table name to prevent SQL injection
        table_name = validate_identifier(table_name, "table")
            
        table_name_upper = table_name.upper()
        if table_name_upper in existing_table_names:
            warnings.append(f"Warning: Table '{table_name}' already exists in {database_name}.{schema_name}, skipping creation")
        else:
            try:
                # Ensure the table is created in the correct database.schema
                full_table_definition = table_definition.replace(
                    f"CREATE TABLE {table_name}", 
                    f"CREATE TABLE {database_name}.{schema_name}.{table_name}"
                )
                create_result, _ = await db.execute_query(full_table_definition)
                results.append(f"Successfully created table '{table_name}' in {database_name}.{schema_name}")
            except Exception as e:
                results.append(f"Failed to create table '{table_name}' in {database_name}.{schema_name}: {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_drop_tables(arguments, db, _, allow_write, __, allowed_databases=None, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments or "database" not in arguments or "schema" not in arguments or "tables" not in arguments:
        raise ValueError("Missing required 'database', 'schema', and 'tables' parameters")
    
    database_name = validate_identifier(arguments["database"], "database")
    schema_name = validate_identifier(arguments["schema"], "schema")
    table_names = arguments["tables"]
    
    if not isinstance(table_names, list):
        raise ValueError("'tables' parameter must be a list of table names")
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)
    
    results = []
    warnings = []
    
    # Get existing tables to check for non-existent ones
    try:
        existing_tables_result, _ = await db.execute_query(
            f"SELECT TABLE_NAME FROM {database_name}.INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema_name.upper()}'"
        )
        existing_table_names = {row["TABLE_NAME"].upper() for row in existing_tables_result}
    except Exception as e:
        return [types.TextContent(type="text", text=f"Failed to check existing tables in {database_name}.{schema_name}: {str(e)}")]
    
    for table_name in table_names:
        table_name = validate_identifier(table_name, "table")
        table_name_upper = table_name.upper()
        if table_name_upper not in existing_table_names:
            warnings.append(f"Warning: Table '{table_name}' does not exist in {database_name}.{schema_name}, skipping deletion")
        else:
            try:
                drop_result, _ = await db.execute_query(f"DROP TABLE {database_name}.{schema_name}.{table_name}")
                results.append(f"Successfully dropped table '{table_name}' from {database_name}.{schema_name}")
            except Exception as e:
                results.append(f"Failed to drop table '{table_name}' from {database_name}.{schema_name}: {str(e)}")
    
    response_text = "\n".join(results)
    if warnings:
        response_text = "\n".join(warnings) + "\n" + response_text
    
    return [types.TextContent(type="text", text=response_text)]


async def handle_create_table(arguments, db, _, allow_write, __, **___):
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")
    if not arguments["query"].strip().upper().startswith("CREATE TABLE"):
        raise ValueError("Only CREATE TABLE statements are allowed")

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=f"Table created successfully. data_id = {data_id}")]


async def prefetch_tables(db: SnowflakeDB, credentials: dict) -> dict:
    """Prefetch table and column information"""
    try:
        logger.info("Prefetching table descriptions")
        # Validate identifiers from credentials used in queries
        db_name = validate_identifier(credentials['database'], "database")
        schema_name = validate_identifier(credentials['schema'], "schema")

        table_results, data_id = await db.execute_query(
            f"""SELECT table_name, comment 
                FROM {db_name}.information_schema.tables 
                WHERE table_schema = '{schema_name.upper()}'"""
        )

        column_results, data_id = await db.execute_query(
            f"""SELECT table_name, column_name, data_type, comment 
                FROM {db_name}.information_schema.columns 
                WHERE table_schema = '{schema_name.upper()}'"""
        )

        tables_brief = {}
        for row in table_results:
            tables_brief[row["TABLE_NAME"]] = {**row, "COLUMNS": {}}

        for row in column_results:
            row_without_table_name = row.copy()
            del row_without_table_name["TABLE_NAME"]
            tables_brief[row["TABLE_NAME"]]["COLUMNS"][row["COLUMN_NAME"]] = row_without_table_name

        return tables_brief

    except Exception as e:
        logger.error(f"Error prefetching table descriptions: {e}")
        return f"Error prefetching table descriptions: {e}"


async def main(
    allow_write: bool = False,
    connection_args: dict = None,
    log_dir: str = None,
    prefetch: bool = False,
    log_level: str = "INFO",
    exclude_tools: list[str] = [],
    config_file: str = "runtime_config.json",
    exclude_patterns: dict = None,
    exclude_json_results: bool = False,
    allowed_databases: list[str] = None,
    transport: str = "stdio",
    port: int = 8000,
):
    # Setup logging
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        logger.handlers.append(logging.FileHandler(os.path.join(log_dir, "mcp_snowflake_server.log")))
    if log_level:
        logger.setLevel(log_level)

    logger.info("Starting Snowflake MCP Server")
    logger.info("Allow write operations: %s", allow_write)
    logger.info("Prefetch table descriptions: %s", prefetch)
    logger.info("Excluded tools: %s", exclude_tools)

    # Load configuration from file if provided
    config = {}
    if config_file:
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")

    # Initialize components
    write_detector = SQLWriteDetector()
    server = Server("snowflake")

    # Process exclusion patterns from both exclude_patterns param and config file
    exclusion_config = {
        "databases": [],
        "schemas": [],
        "tables": [],
    }

    if exclude_patterns:
        for key in ["databases", "schemas", "tables"]:
            if key in exclude_patterns:
                exclusion_config[key].extend(exclude_patterns[key])

    if "exclude_patterns" in config:
        for key in ["databases", "schemas", "tables"]:
            if key in config["exclude_patterns"]:
                exclusion_config[key].extend(config["exclude_patterns"][key])

    logger.info(f"Exclusion patterns: {exclusion_config}")

    # Handle allowed_databases from config file
    if allowed_databases is None and "allowed_databases" in config:
        allowed_databases = config["allowed_databases"]

    if allowed_databases:
        logger.info(f"Allowed databases restriction: {allowed_databases}")

    # Process exclude_tools from config file
    config_exclude_tools = config.get("exclude_tools", [])
    if config_exclude_tools:
        exclude_tools = list(set(exclude_tools + config_exclude_tools))
        logger.info(f"Updated excluded tools from config: {exclude_tools}")

    # Initialize database connection
    db = SnowflakeDB(connection_args)
    db.start_init_connection()

    # Prefetch table information if configured
    tables_info = {}
    if prefetch:
        tables_info = await prefetch_tables(db, connection_args)
        if isinstance(tables_info, str):
            logger.error(tables_info)
            tables_info = {}
    db.close()

    # Define tools
    all_tools = [
        Tool(
            name="list_databases",
            description="List all available Snowflake databases",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=handle_list_databases,
        ),
        Tool(
            name="list_schemas",
            description="List all schemas in a specific database",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    }
                },
                "required": ["database"],
            },
            handler=handle_list_schemas,
        ),
        Tool(
            name="list_tables",
            description="List all tables in a specific database and schema",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    }
                },
                "required": ["database", "schema"],
            },
            handler=handle_list_tables,
        ),
        Tool(
            name="describe_table",
            description="Get a description of a table's columns, including name, type, nullable, default value, and comment",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Fully qualified table name (database.schema.table)",
                    }
                },
                "required": ["table_name"],
            },
            handler=handle_describe_table,
        ),
        Tool(
            name="read_query",
            description="Execute a SELECT query on the Snowflake database. You cannot make any write operations with this tool.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SELECT SQL query to execute",
                    }
                },
                "required": ["query"],
            },
            handler=handle_read_query,
        ),
        Tool(
            name="write_query",
            description="Execute a write query on the Snowflake database. You cannot execute SELECT queries with this tool.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL write query to execute (INSERT, UPDATE, DELETE, etc.)",
                    }
                },
                "required": ["query"],
            },
            handler=handle_write_query,
            tags=["write"],
        ),
        Tool(
            name="create_table",
            description="Create a new table in the Snowflake database using a CREATE TABLE SQL statement",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "CREATE TABLE SQL statement",
                    }
                },
                "required": ["query"],
            },
            handler=handle_create_table,
            tags=["write"],
        ),
        Tool(
            name="append_insight",
            description="Add a data insight to the memo",
            input_schema={
                "type": "object",
                "properties": {
                    "insight": {
                        "type": "string",
                        "description": "Data insight discovered from analysis",
                    }
                },
                "required": ["insight"],
            },
            handler=handle_append_insight,
        ),
        Tool(
            name="create_databases",
            description="Create multiple databases",
            input_schema={
                "type": "object",
                "properties": {
                    "databases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of database names to create"
                    }
                },
                "required": ["databases"],
            },
            handler=handle_create_databases,
            tags=["write"],
        ),
        Tool(
            name="drop_databases",
            description="Drop multiple databases",
            input_schema={
                "type": "object",
                "properties": {
                    "databases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of database names to drop"
                    }
                },
                "required": ["databases"],
            },
            handler=handle_drop_databases,
            tags=["write"],
        ),
        Tool(
            name="create_schemas",
            description="Create multiple schemas in a database",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "schemas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of schema names to create"
                    }
                },
                "required": ["database", "schemas"],
            },
            handler=handle_create_schemas,
            tags=["write"],
        ),
        Tool(
            name="drop_schemas",
            description="Drop multiple schemas from a database",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "schemas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of schema names to drop"
                    }
                },
                "required": ["database", "schemas"],
            },
            handler=handle_drop_schemas,
            tags=["write"],
        ),
        Tool(
            name="create_tables",
            description="Create multiple tables in a database schema",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    },
                    "tables": {
                        "type": "array",
                        "items": {
                            "oneOf": [
                                {"type": "string", "description": "CREATE TABLE SQL statement"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Table name"},
                                        "definition": {"type": "string", "description": "CREATE TABLE SQL statement"}
                                    },
                                    "required": ["name", "definition"]
                                }
                            ]
                        },
                        "description": "List of table definitions to create"
                    }
                },
                "required": ["database", "schema", "tables"],
            },
            handler=handle_create_tables,
            tags=["write"],
        ),
        Tool(
            name="drop_tables",
            description="Drop multiple tables from a database schema",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name"
                    },
                    "tables": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of table names to drop"
                    }
                },
                "required": ["database", "schema", "tables"],
            },
            handler=handle_drop_tables,
            tags=["write"],
        ),
    ]

    exclude_tags = []
    if not allow_write:
        exclude_tags.append("write")
    allowed_tools = [
        tool for tool in all_tools if tool.name not in exclude_tools and not any(tag in exclude_tags for tag in tool.tags)
    ]

    logger.info("Allowed tools: %s", [tool.name for tool in allowed_tools])

    # Register handlers
    @server.list_resources()
    async def handle_list_resources() -> list[types.Resource]:
        resources = [
            types.Resource(
                uri=AnyUrl("memo://insights"),
                name="Data Insights Memo",
                description="A living document of discovered data insights",
                mimeType="text/plain",
            )
        ]
        table_brief_resources = [
            types.Resource(
                uri=AnyUrl(f"context://table/{table_name}"),
                name=f"{table_name} table",
                description=f"Description of the {table_name} table",
                mimeType="text/plain",
            )
            for table_name in tables_info.keys()
        ]
        resources += table_brief_resources
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: AnyUrl) -> str:
        if str(uri) == "memo://insights":
            return db.get_memo()
        elif str(uri).startswith("context://table"):
            table_name = str(uri).split("/")[-1]
            if table_name in tables_info:
                return to_yaml(tables_info[table_name])
            else:
                raise ValueError(f"Unknown table: {table_name}")
        else:
            raise ValueError(f"Unknown resource: {uri}")

    @server.list_prompts()
    async def handle_list_prompts() -> list[types.Prompt]:
        return []

    @server.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        raise ValueError(f"Unknown prompt: {name}")

    @server.call_tool()
    @handle_tool_errors
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[ResponseType]:
        if name in exclude_tools:
            return [types.TextContent(type="text", text=f"Tool {name} is excluded from this data connection")]

        handler = next((tool.handler for tool in allowed_tools if tool.name == name), None)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        # Create new DB instance for this request
        # Merge global connection_args with request-specific credentials
        current_connection_args = connection_args.copy() if connection_args else {}
        request_creds = connection_context.get()
        
        # If request credentials are provided, override defaults
        if request_creds:
            current_connection_args.update(request_creds)
            logger.info(f"Using request-specific credentials for tool {name}")
        
        # Always create a new connection for isolation as requested
        current_db = SnowflakeDB(current_connection_args)
        current_db.start_init_connection()

        try:
            # Pass exclusion_config to the handler if it's a listing function
            if name in ["list_databases", "list_schemas", "list_tables"]:
                return await handler(
                    arguments,
                    current_db,
                    write_detector,
                    allow_write,
                    server,
                    exclusion_config=exclusion_config,
                    exclude_json_results=exclude_json_results,
                    allowed_databases=allowed_databases,
                )
            else:
                return await handler(
                    arguments,
                    current_db,
                    write_detector,
                    allow_write,
                    server,
                    exclude_json_results=exclude_json_results,
                    allowed_databases=allowed_databases,
                )
        finally:
            current_db.close()

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        logger.info("Listing tools")
        logger.error(f"Allowed tools: {allowed_tools}")
        tools = [
            types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            )
            for tool in allowed_tools
        ]
        return tools

    # Start server
    if transport == "stdio":
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server running with stdio transport")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="snowflake",
                    server_version=importlib.metadata.version("mcp_snowflake_server"),
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    elif transport == "http":
        # Set up SSE transport
        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            # Extract credentials and set context
            creds = extract_credentials(request)
            token = connection_context.set(creds)
            try:
                async with sse.connect_sse(
                    request.scope, request.receive, request._send
                ) as streams:
                    await server.run(
                        streams[0], streams[1], server.create_initialization_options()
                    )
            finally:
                connection_context.reset(token)
            return Response()

        # Set up StreamableHTTP transport
        session_manager = StreamableHTTPSessionManager(
            app=server,
            event_store=None,
            json_response=False,
            stateless=True,
        )

        async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
            # Extract credentials and set context
            creds = extract_credentials(scope)
            token = connection_context.set(creds)
            try:
                await session_manager.handle_request(scope, receive, send)
            finally:
                connection_context.reset(token)

        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            async with session_manager.run():
                logger.info(f"Server starting on port {port} with dual transports!")
                logger.info(f"  - SSE endpoint: http://0.0.0.0:{port}/sse")
                logger.info(f"  - StreamableHTTP endpoint: http://0.0.0.0:{port}/mcp")
                yield

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
                Mount("/mcp", app=handle_streamable_http),
            ],
            lifespan=lifespan,
        )

        config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level=log_level.lower())
        server_uvicorn = uvicorn.Server(config)
        await server_uvicorn.serve()
    else:
        raise ValueError(f"Unknown transport: {transport}")
