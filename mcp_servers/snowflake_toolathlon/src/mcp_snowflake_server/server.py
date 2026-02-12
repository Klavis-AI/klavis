import importlib.metadata
import json
import logging
import os
from functools import wraps
from typing import Any, Callable

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl, BaseModel

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




def handle_tool_errors(func: Callable) -> Callable:
    """Decorator to standardize tool error handling"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> list[types.TextContent]:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

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
    import re
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
    query = "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES"
    data, data_id = await db.execute_query(query)

    # Filter to only allowed databases if restriction is set
    if allowed_databases is not None:
        allowed_db_set = {db.upper() for db in allowed_databases}
        data = [item for item in data if item.get("DATABASE_NAME", "").upper() in allowed_db_set]

    # Filter out excluded databases
    if exclusion_config and "databases" in exclusion_config and exclusion_config["databases"]:
        filtered_data = []
        for item in data:
            db_name = item.get("DATABASE_NAME", "")
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

    database = arguments["database"]
    
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

    database = arguments["database"]
    schema = arguments["schema"]
    
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

    database_name = split_identifier[0].upper()
    
    # Check allowed databases restriction
    check_database_access(database_name, allowed_databases)
    schema_name = split_identifier[1].upper()
    table_name = split_identifier[2].upper()

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
    
    # Check allowed databases restriction for all databases first
    real_database_names = []
    for db_name in database_names:
        try:
            check_database_access(db_name, allowed_databases)
            real_database_names.append(db_name)
        except Exception as e:
            warnings.append(f"Warning: Creating database '{db_name}' is not allowed, you can only create databases in the following list: {allowed_databases}")
    
    # Get existing databases to check for duplicates
    existing_dbs_result, _ = await db.execute_query("SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES")
    existing_db_names = {row["DATABASE_NAME"].upper() for row in existing_dbs_result}
    
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
    
    # Check allowed databases restriction for all databases first
    for db_name in database_names:
        check_database_access(db_name, allowed_databases)
    
    # Get existing databases to check for non-existent ones
    existing_dbs_result, _ = await db.execute_query("SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES")
    existing_db_names = {row["DATABASE_NAME"].upper() for row in existing_dbs_result}
    
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
    
    database_name = arguments["database"]
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
    
    database_name = arguments["database"]
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
    
    database_name = arguments["database"]
    schema_name = arguments["schema"]
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
            import re
            match = re.search(r'CREATE\s+TABLE\s+(\w+)', table_definition.upper())
            table_name = match.group(1) if match else "UNKNOWN"
        else:
            results.append(f"Invalid table definition format: {table_def}")
            continue
            
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
    
    database_name = arguments["database"]
    schema_name = arguments["schema"]
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
        table_results, data_id = await db.execute_query(
            f"""SELECT table_name, comment 
                FROM {credentials['database']}.information_schema.tables 
                WHERE table_schema = '{credentials['schema'].upper()}'"""
        )

        column_results, data_id = await db.execute_query(
            f"""SELECT table_name, column_name, data_type, comment 
                FROM {credentials['database']}.information_schema.columns 
                WHERE table_schema = '{credentials['schema'].upper()}'"""
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
    #
    if config_file:
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")

    # Merge exclude_patterns from parameters with config file
    exclusion_config = config.get("exclude_patterns", {})
    if exclude_patterns:
        # Merge patterns from parameters with those from config file
        for key, patterns in exclude_patterns.items():
            if key in exclusion_config:
                exclusion_config[key].extend(patterns)
            else:
                exclusion_config[key] = patterns

    # Set default patterns if none are specified
    if not exclusion_config:
        exclusion_config = {"databases": [], "schemas": [], "tables": []}

    # Ensure all keys exist in the exclusion config
    for key in ["databases", "schemas", "tables"]:
        if key not in exclusion_config:
            exclusion_config[key] = []

    logger.info(f"Exclusion patterns: {exclusion_config}")

    db = SnowflakeDB(connection_args)
    db.start_init_connection()
    server = Server("snowflake-manager")
    write_detector = SQLWriteDetector()

    tables_info = (await prefetch_tables(db, connection_args)) if prefetch else {}
    tables_brief = to_yaml(tables_info) if prefetch else ""

    all_tools = [
        Tool(
            name="list_databases",
            description="List all available databases in Snowflake",
            input_schema={
                "type": "object",
                "properties": {},
            },
            handler=handle_list_databases,
        ),
        Tool(
            name="list_schemas",
            description="List all schemas in a database",
            input_schema={
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string",
                        "description": "Database name to list schemas from",
                    },
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
                    "database": {"type": "string", "description": "Database name"},
                    "schema": {"type": "string", "description": "Schema name"},
                },
                "required": ["database", "schema"],
            },
            handler=handle_list_tables,
        ),
        Tool(
            name="describe_table",
            description="Get the schema information for a specific table",
            input_schema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Fully qualified table name in the format 'database.schema.table'",
                    },
                },
                "required": ["table_name"],
            },
            handler=handle_describe_table,
        ),
        Tool(
            name="read_query",
            description="Execute a SELECT query.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SELECT SQL query to execute"}},
                "required": ["query"],
            },
            handler=handle_read_query,
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
            tags=["resource_based"],
        ),
        Tool(
            name="write_query",
            description="Execute an INSERT, UPDATE, or DELETE query on the Snowflake database",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "SQL query to execute"}},
                "required": ["query"],
            },
            handler=handle_write_query,
            tags=["write"],
        ),
        Tool(
            name="create_table",
            description="Create a new table in the Snowflake database",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "CREATE TABLE SQL statement"}},
                "required": ["query"],
            },
            handler=handle_create_table,
            tags=["write"],
        ),
        Tool(
            name="create_databases",
            description="Create multiple databases in Snowflake",
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
            description="Drop multiple databases in Snowflake",
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
                        "description": "Database name where schemas will be created"
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
                        "description": "Database name where schemas will be dropped"
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

        # Pass exclusion_config to the handler if it's a listing function
        if name in ["list_databases", "list_schemas", "list_tables"]:
            return await handler(
                arguments,
                db,
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
                db,
                write_detector,
                allow_write,
                server,
                exclude_json_results=exclude_json_results,
                allowed_databases=allowed_databases,
            )

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
