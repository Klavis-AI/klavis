# Snowflake MCP Server

A comprehensive Model Context Protocol (MCP) server for Snowflake that provides intelligent database interaction capabilities. This server enables AI agents to discover, query, and analyze Snowflake data warehouses through atomic, well-documented tools.

## 🎯 Purpose

This MCP server serves as a bridge between AI agents and Snowflake data warehouses, providing:

- **Database Discovery**: Explore databases, schemas, and tables
- **Data Querying**: Execute SELECT statements and retrieve results
- **Schema Analysis**: Understand table structures and relationships
- **Data Insights**: Accumulate and track analytical findings
- **Safe Operations**: Write operations only when explicitly enabled

## ⚡ Quick Start

### Prerequisites

- Python 3.10+ (≤3.12 recommended)
- Snowflake account with appropriate permissions
- Claude Desktop (for testing) or other MCP-compatible client

### Installation via UVX (Recommended)

```bash
# Install via UVX (handles Python dependencies automatically)
uvx --python=3.12 mcp_snowflake_server --help
```

### Local Development Installation

```bash
# Clone the repository
git clone https://github.com/Klavis-AI/klavis.git
cd mcp-snowflake-server

# Install dependencies
pip install -e .

# Or using uv (recommended)
uv pip install -e .
```

## 🔑 Authentication Setup

### Method 1: Environment Variables (.env file)

Create a `.env` file in your project directory:

```bash
# Required credentials
SNOWFLAKE_ACCOUNT="your_account_id"
SNOWFLAKE_USER="your_username"
SNOWFLAKE_PASSWORD="your_password"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="your_database"
SNOWFLAKE_SCHEMA="PUBLIC"
SNOWFLAKE_ROLE="your_role"

# Optional: Private key authentication
SNOWFLAKE_PRIVATE_KEY_PATH="/absolute/path/to/private_key.pem"

# Optional: Browser-based authentication
SNOWFLAKE_AUTHENTICATOR="externalbrowser"
```

**Finding Your Snowflake Account ID:**

1. Log into your Snowflake web interface
2. The account ID is in the URL: `https://<ACCOUNT_ID>.snowflakecomputing.com`
3. Or run `SELECT CURRENT_ACCOUNT()` in a Snowflake worksheet

### Method 2: TOML Configuration (Recommended for Multiple Environments)

Create a `snowflake_connections.toml` file:

```toml
[production]
account = "abc12345.us-east-1"
user = "prod_user"
password = "secure_password"
warehouse = "PROD_WH"
database = "ANALYTICS_DB"
schema = "PUBLIC"
role = "ANALYST_ROLE"

[development]
account = "abc12345.us-east-1"
user = "dev_user"
authenticator = "externalbrowser"  # Browser authentication
warehouse = "DEV_WH"
database = "DEV_DB"
schema = "PUBLIC"
role = "DEVELOPER"

[staging]
account = "abc12345.us-east-1"
user = "service_account"
private_key_path = "/path/to/staging_key.pem"  # Key-pair auth
warehouse = "STAGING_WH"
database = "STAGING_DB"
schema = "PUBLIC"
role = "STAGING_ROLE"
```

### Method 3: Private Key Authentication

1. **Generate a key pair** (if you don't have one):

```bash
# Generate private key
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.pem -nocrypt

# Generate public key
openssl rsa -in snowflake_key.pem -pubout -out snowflake_key.pub
```

2. **Add public key to Snowflake user**:

```sql
-- In Snowflake, run this command (replace with your public key content)
ALTER USER your_username SET RSA_PUBLIC_KEY='MIIBIjANBgkqhkiG9w0B...';
```

3. **Configure the server**:

```bash
SNOWFLAKE_PRIVATE_KEY_PATH="/absolute/path/to/snowflake_key.pem"
```

## 📋 Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

### Using Environment Variables

```json
{
  "mcpServers": {
    "snowflake": {
      "command": "uvx",
      "args": ["--python=3.12", "mcp_snowflake_server"]
    }
  }
}
```

### Using TOML Configuration (Multiple Environments)

```json
{
  "mcpServers": {
    "snowflake_prod": {
      "command": "uvx",
      "args": [
        "--python=3.12",
        "mcp_snowflake_server",
        "--connections-file",
        "/absolute/path/to/snowflake_connections.toml",
        "--connection-name",
        "production"
      ]
    },
    "snowflake_dev": {
      "command": "uvx",
      "args": [
        "--python=3.12",
        "mcp_snowflake_server",
        "--connections-file",
        "/absolute/path/to/snowflake_connections.toml",
        "--connection-name",
        "development"
      ]
    }
  }
}
```

### Local Development

```json
{
  "mcpServers": {
    "snowflake_local": {
      "command": "/absolute/path/to/uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-snowflake-server",
        "run",
        "mcp_snowflake_server",
        "--allow-write"
      ]
    }
  }
}
```

## 🛠️ Available Tools

### Discovery Tools

#### `snowflake_list_databases`

List all accessible databases in your Snowflake instance.

- **Purpose**: Discover available databases for querying
- **Returns**: List of database names
- **Usage**: "Show me all available databases"

#### `snowflake_list_schemas`

List all schemas within a specific database.

- **Parameters**:
  - `database` (string): Database name to explore
- **Returns**: List of schema names
- **Usage**: "List schemas in the ANALYTICS_DB database"

#### `snowflake_list_tables`

List all tables within a database and schema.

- **Parameters**:
  - `database` (string): Database name
  - `schema` (string): Schema name
- **Returns**: Table metadata with comments
- **Usage**: "Show tables in ANALYTICS_DB.PUBLIC schema"

#### `snowflake_describe_table`

Get detailed schema information for a table.

- **Parameters**:
  - `table_name` (string): Fully qualified name (database.schema.table)
- **Returns**: Column details, types, constraints, comments
- **Usage**: "Describe the structure of ANALYTICS_DB.PUBLIC.SALES_DATA"

#### `snowflake_list_table_columns`

Get column names for a table (faster than describe_table).

- **Parameters**:
  - `table_name` (string): Fully qualified table name
- **Returns**: Ordered list of column names
- **Usage**: "What columns are in the USERS table?"

### Query Tools

#### `snowflake_execute_select`

Execute SELECT queries to retrieve data.

- **Parameters**:
  - `query` (string): Valid SELECT SQL statement
- **Returns**: Query results as structured data
- **Usage**: "SELECT \* FROM SALES_DATA WHERE date >= '2024-01-01'"

#### `snowflake_get_table_sample`

Get sample rows from a table for exploration.

- **Parameters**:
  - `table_name` (string): Fully qualified table name
  - `limit` (integer, optional): Number of rows (default: 10, max: 100)
- **Returns**: Sample data with metadata
- **Usage**: "Show me a sample of the CUSTOMER_DATA table"

#### `snowflake_get_table_row_count`

Get total row count for a table.

- **Parameters**:
  - `table_name` (string): Fully qualified table name
- **Returns**: Row count information
- **Usage**: "How many rows are in the TRANSACTIONS table?"

### Analysis Tools

#### `snowflake_append_insight`

Record data insights discovered during analysis.

- **Parameters**:
  - `insight` (string): Specific, actionable insight
- **Returns**: Confirmation of insight recording
- **Usage**: "Customer churn rate increased 15% in Q4 2024"

#### `snowflake_get_query_history`

View recent query execution history.

- **Parameters**:
  - `limit` (integer, optional): Number of queries (default: 10, max: 50)
- **Returns**: Query history with execution details
- **Usage**: "Show my recent query activity"

### Validation Tools

#### `snowflake_check_table_exists`

Verify if a table exists before querying.

- **Parameters**:
  - `table_name` (string): Fully qualified table name
- **Returns**: Boolean existence check
- **Usage**: "Does the MONTHLY_REPORTS table exist?"

### Write Operations (Optional)

#### `snowflake_execute_dml`

Execute INSERT, UPDATE, DELETE operations.

- **Requires**: `--allow-write` flag
- **Parameters**:
  - `query` (string): DML SQL statement
- **Returns**: Operation results
- **Usage**: "UPDATE products SET price = price \* 1.1 WHERE category = 'electronics'"

#### `snowflake_create_table`

Create new tables using DDL.

- **Requires**: `--allow-write` flag
- **Parameters**:
  - `query` (string): CREATE TABLE statement
- **Returns**: Creation confirmation
- **Usage**: "CREATE TABLE test_table (id INT, name STRING)"

## 🔒 Security & Safety

### Write Protection

By default, all write operations are **disabled** to prevent accidental data modification. Enable explicitly:

```bash
# Enable write operations
mcp_snowflake_server --allow-write
```

### Connection Security

- Credentials loaded from environment variables or secure TOML files
- Private key authentication supported
- Browser-based authentication available
- No credentials stored in code

### Query Safety

- SELECT-only operations by default
- Write operation detection and blocking
- Input validation on all parameters
- Comprehensive error handling

## 🎛️ Configuration Options

### Command Line Arguments

```bash
# Basic usage
mcp_snowflake_server

# With write operations enabled
mcp_snowflake_server --allow-write

# Using TOML configuration
mcp_snowflake_server --connections-file ./config.toml --connection-name production

# Custom logging
mcp_snowflake_server --log-level DEBUG --log-dir ./logs

# Exclude specific tools
mcp_snowflake_server --exclude-tools snowflake_execute_dml snowflake_create_table

# Private key authentication
mcp_snowflake_server --private-key-path /path/to/key.pem
```

### Environment Variables

All Snowflake connection parameters can be set via environment variables with the `SNOWFLAKE_` prefix:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_PRIVATE_KEY_PATH`
- `SNOWFLAKE_AUTHENTICATOR`

## 📊 Resources

The server exposes these MCP resources:

### `memo://insights`

A living document of accumulated data insights discovered during analysis sessions. Automatically updated when using `snowflake_append_insight`.

### `context://table/{table_name}` (when prefetch enabled)

Per-table schema summaries with column information and comments.

## 🧪 Testing the Server

### 1. Test Basic Connection

```bash
# Test server startup
uv run mcp_snowflake_server --help

# Test with your credentials
uv run mcp_snowflake_server
```

### 2. Test in Claude Desktop

After configuring Claude Desktop, try these natural language commands:

- "Show me all available databases"
- "List the tables in the PUBLIC schema of ANALYTICS_DB"
- "Describe the SALES_DATA table structure"
- "Get a sample of 5 rows from CUSTOMER_DATA"
- "How many rows are in the TRANSACTIONS table?"
- "Execute: SELECT COUNT(\*) FROM SALES_DATA WHERE date >= '2024-01-01'"

### 3. Expected Behavior

✅ **Successful Operations:**

- Tool calls logged to console
- Structured YAML and JSON responses
- Error-free data retrieval
- Insights accumulated in memo

❌ **Expected Errors (Good!):**

- "Table not found" → Suggests using discovery tools
- "Access denied" → Suggests permission check
- "Write operations disabled" → Suggests enabling --allow-write

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems

```
Error: Failed to connect to Snowflake database
```

**Solutions:**

1. Verify account ID format: `account_name.region` or `organization-account_name`
2. Check credentials in `.env` file
3. Ensure warehouse is running: `ALTER WAREHOUSE your_warehouse RESUME`
4. Verify network connectivity to Snowflake

#### Permission Errors

```
Access denied: insufficient privileges
```

**Solutions:**

1. Check role permissions: `SHOW GRANTS TO ROLE your_role`
2. Ensure role can access database/schema: `USE ROLE your_role; USE DATABASE your_db`
3. Contact Snowflake administrator for access

#### Tool Not Found

```
Unknown tool: list_databases
```

**Solutions:**

1. Update tool names to new prefixed versions (e.g., `snowflake_list_databases`)
2. Restart Claude Desktop after configuration changes
3. Check server logs for tool registration

### Debug Mode

Enable detailed logging:

```bash
mcp_snowflake_server --log-level DEBUG --log-dir ./debug_logs
```

This creates detailed logs in the specified directory for troubleshooting.

## 🚀 Advanced Usage

### Multi-Environment Setup

Use different connections for different purposes:

```json
{
  "mcpServers": {
    "snowflake_analytics": {
      "command": "uvx",
      "args": [
        "--python=3.12",
        "mcp_snowflake_server",
        "--connections-file",
        "./connections.toml",
        "--connection-name",
        "analytics"
      ]
    },
    "snowflake_warehouse": {
      "command": "uvx",
      "args": [
        "--python=3.12",
        "mcp_snowflake_server",
        "--connections-file",
        "./connections.toml",
        "--connection-name",
        "warehouse",
        "--allow-write"
      ]
    }
  }
}
```

### Custom Tool Exclusion

Exclude tools you don't need:

```bash
mcp_snowflake_server --exclude-tools snowflake_get_query_history snowflake_execute_dml
```

### Table Prefetching

Enable table prefetching for faster schema access:

```bash
mcp_snowflake_server --prefetch
```

This loads table schemas into memory and exposes them as MCP resources.

## 📝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/Klavis-AI/klavis.git
cd mcp-snowflake-server

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run type checking
pyright src/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/Klavis-AI/klavis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Klavis-AI/klavis/discussions)
- **Documentation**: [Wiki](https://github.com/Klavis-AI/klavis/wiki)

---

**Built with ❤️ for the Klavis AI ecosystem**
