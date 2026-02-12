[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/isaacwasserman-mcp-snowflake-server-badge.png)](https://mseep.ai/app/isaacwasserman-mcp-snowflake-server)

# Snowflake MCP Server
---

## Overview

A Model Context Protocol (MCP) server implementation that provides database interaction with Snowflake. This server enables running SQL queries via tools and exposes data insights and schema context as resources.

---

## Components

### Resources

- **`memo://insights`**  
  A continuously updated memo aggregating discovered data insights.  
  Updated automatically when new insights are appended via the `append_insight` tool.

- **`context://table/{table_name}`**  
  (If prefetch enabled) Per-table schema summaries, including columns and comments, exposed as individual resources.

---

### Tools

The server exposes the following tools:

#### Query Tools

- **`read_query`**  
  Execute `SELECT` queries to read data from the database.  
  **Input:**

  - `query` (string): The `SELECT` SQL query to execute  
    **Returns:** Query results as array of objects

- **`write_query`** (enabled only with `--allow-write`)  
  Execute `INSERT`, `UPDATE`, or `DELETE` queries.  
  **Input:**

  - `query` (string): The SQL modification query  
    **Returns:** Number of affected rows or confirmation

- **`create_table`** (enabled only with `--allow-write`)  
  Create new tables in the database.  
  **Input:**
  - `query` (string): `CREATE TABLE` SQL statement  
    **Returns:** Confirmation of table creation

- **`create_databases`** (enabled only with `--allow-write`)  
  Create multiple databases in batch with existence checking.  
  **Input:**
  - `databases` (array of strings): List of database names to create  
    **Returns:** Results with warnings for already existing databases

- **`drop_databases`** (enabled only with `--allow-write`)  
  Drop multiple databases in batch with existence checking.  
  **Input:**
  - `databases` (array of strings): List of database names to drop  
    **Returns:** Results with warnings for non-existent databases

- **`create_schemas`** (enabled only with `--allow-write`)  
  Create multiple schemas in a database with existence checking.  
  **Input:**
  - `database` (string): Name of the database
  - `schemas` (array of strings): List of schema names to create  
    **Returns:** Results with warnings for already existing schemas

- **`drop_schemas`** (enabled only with `--allow-write`)  
  Drop multiple schemas from a database with existence checking.  
  **Input:**
  - `database` (string): Name of the database
  - `schemas` (array of strings): List of schema names to drop  
    **Returns:** Results with warnings for non-existent schemas

- **`create_tables`** (enabled only with `--allow-write`)  
  Create multiple tables in a database.schema with existence checking.  
  **Input:**
  - `database` (string): Name of the database
  - `schema` (string): Name of the schema
  - `tables` (array): List of table definitions (strings or objects with name/definition)  
    **Returns:** Results with warnings for already existing tables

- **`drop_tables`** (enabled only with `--allow-write`)  
  Drop multiple tables from a database.schema with existence checking.  
  **Input:**
  - `database` (string): Name of the database
  - `schema` (string): Name of the schema
  - `tables` (array of strings): List of table names to drop  
    **Returns:** Results with warnings for non-existent tables

#### Schema Tools

- **`list_databases`**  
  List all databases in the Snowflake instance.  
  **Returns:** Array of database names

- **`list_schemas`**  
  List all schemas within a specific database.  
  **Input:**

  - `database` (string): Name of the database  
    **Returns:** Array of schema names

- **`list_tables`**  
  List all tables within a specific database and schema.  
  **Input:**

  - `database` (string): Name of the database
  - `schema` (string): Name of the schema  
    **Returns:** Array of table metadata

- **`describe_table`**  
  View column information for a specific table.  
  **Input:**
  - `table_name` (string): Fully qualified table name (`database.schema.table`)  
    **Returns:** Array of column definitions with names, types, nullability, defaults, and comments

#### Analysis Tools

- **`append_insight`**  
  Add new data insights to the memo resource.  
  **Input:**
  - `insight` (string): Data insight discovered from analysis  
    **Returns:** Confirmation of insight addition  
    **Effect:** Triggers update of `memo://insights` resource

---

## Usage with Claude Desktop

### uvx

*Note: please edit and change these parameters on your own need.

```json
"mcpServers": {
  "snowflake": {
    "command": "uvx",
    "args": [
      "git+https://github.com/lockon-n/mcp-snowflake-server"
      "--account your-account-id"
      "--warehouse COMPUTE_WH"
      "--user your-user-name"
      "--password your-password"
      "--role ACCOUNTADMIN"
      "--database SNOWFLAKE"
      "--schema PUBLIC"
      "--allowed_databases db1,db2,db3" (optionl)
      "--allow_write" (optional)
      "--exclude-json-results" (optionl)
      // Optionally: "--log_dir", "/absolute/path/to/logs"
      // Optionally: "--log_level", "DEBUG"/"INFO"/"WARNING"/"ERROR"/"CRITICAL"
      // Optionally: "--exclude_tools", "{tool_name}", ["{other_tool_name}"]
    ]
  }
}
```

### Installing Locally

1. Install [Claude AI Desktop App](https://claude.ai/download)

2. Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create a `.env` file with your Snowflake credentials:

```bash
SNOWFLAKE_USER="xxx@your_email.com"
SNOWFLAKE_ACCOUNT="xxx"
SNOWFLAKE_ROLE="xxx"
SNOWFLAKE_DATABASE="xxx"
SNOWFLAKE_SCHEMA="xxx"
SNOWFLAKE_WAREHOUSE="xxx"
SNOWFLAKE_PASSWORD="xxx"
SNOWFLAKE_PASSWORD="xxx"
SNOWFLAKE_PRIVATE_KEY_PATH=/absolute/path/key.p8
# Alternatively, use external browser authentication:
# SNOWFLAKE_AUTHENTICATOR="externalbrowser"
```

4. [Optional] Modify `runtime_config.json` to set exclusion patterns for databases, schemas, or tables.

5. Test locally:

```bash
uv --directory /absolute/path/to/mcp_snowflake_server run mcp_snowflake_server
```

6. Add the server to your `claude_desktop_config.json`:

#### Traditional Configuration (Using Environment Variables)

```json
"mcpServers": {
  "snowflake_local": {
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.12",  // Optional
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server"
      // Optionally: "--allow_write"
      // Optionally: "--allowed_databases", "database1,database2,database3"
      // Optionally: "--log_dir", "/absolute/path/to/logs"
      // Optionally: "--log_level", "DEBUG"/"INFO"/"WARNING"/"ERROR"/"CRITICAL"
      // Optionally: "--exclude_tools", "{tool_name}", ["{other_tool_name}"]
    ]
  }
}
```

#### TOML Configuration (Recommended)

```json
"mcpServers": {
  "snowflake_local": {
    "command": "/absolute/path/to/uv",
    "args": [
      "--python=3.12",
      "--directory", "/absolute/path/to/mcp_snowflake_server",
      "run", "mcp_snowflake_server",
      "--connections-file", "/absolute/path/to/snowflake_connections.toml",
      "--connection-name", "development"
      // Optionally: "--allow_write"
      // Optionally: "--allowed_databases", "database1,database2,database3"
      // Optionally: "--log_dir", "/absolute/path/to/logs"
      // Optionally: "--log_level", "DEBUG"/"INFO"/"WARNING"/"ERROR"/"CRITICAL"
      // Optionally: "--exclude_tools", "{tool_name}", ["{other_tool_name}"]
    ]
  }
}
```

---

## Notes

- By default, **write operations are disabled**. Enable them explicitly with `--allow-write`.
- The server supports filtering out specific databases, schemas, or tables via exclusion patterns.
- The server exposes additional per-table context resources if prefetching is enabled.
- The `append_insight` tool updates the `memo://insights` resource dynamically.

### New Batch Management Features

- **Database Access Control**: Use `--allowed_databases "db1,db2,db3"` to restrict all operations to specific databases only. When set, any operation attempting to access databases outside this list will be denied.

- **Batch Database Operations**: Create or drop multiple databases at once with `create_databases` and `drop_databases` tools. Both include intelligent warnings for already existing or non-existent databases.

- **Batch Schema Operations**: Create or drop multiple schemas within a database using `create_schemas` and `drop_schemas` tools. Includes existence checking and warning system.

- **Batch Table Operations**: Create or drop multiple tables within a database.schema using `create_tables` and `drop_tables` tools. Supports both simple SQL strings and structured definitions with existence validation.

- **Smart Warning System**: All batch operations provide detailed warnings for edge cases (already exists, doesn't exist, access denied) while continuing to process valid items.

---

## License

MIT
