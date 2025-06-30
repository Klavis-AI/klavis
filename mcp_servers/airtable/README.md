# Airtable MCP Server

A Model Context Protocol (MCP) server for interacting with Airtable bases, tables, fields, and records.

## Features

- **Base Management**: Access and retrieve information about all Airtable bases
- **Table Management**: Create, update, and list tables within bases
- **Field Management**: Create and update table fields with various types
- **Record Management**: Full CRUD operations on records with advanced filtering
- **Advanced Querying**: Filter, sort, and paginate records with formula support
- **Upsert Operations**: Update or insert records based on matching criteria
- **Flexible Data Types**: Support for all Airtable field types and options

## Available Tools

### Base Operations
- `airtable_list_bases_info`: Get information about all accessible bases

### Table Operations
- `airtable_list_tables_info`: Get information about all tables in a base
- `airtable_create_table`: Create a new table with specified fields
- `airtable_update_table`: Update table name and description

### Field Operations
- `airtable_create_field`: Create a new field in a table with specific type and options
- `airtable_update_field`: Update field name and description

### Record Operations
- `airtable_list_records`: List records with advanced filtering, sorting, and pagination
- `airtable_get_record`: Retrieve a specific record by ID
- `airtable_create_records`: Create multiple records in a single operation
- `airtable_update_records`: Update multiple records with optional upsert functionality
- `airtable_delete_records`: Delete multiple records by IDs

## Prerequisites

Get this from: https://airtable.com/create/tokens with these permissions:

1. data.records:read
See the data in records

2. data.records:write
Create, edit, and delete records

3. schema.bases:read
See the structure of a base, like table names or field types

4. schema.bases:write
Edit the structure of a base, like adding new fields or tables

## Configuration

Create a `.env` file in the `mcp_servers/airtable/` directory with the following content:

```bash
AIRTABLE_MCP_SERVER_PORT=5000
AIRTABLE_PERSONAL_ACCESS_TOKEN=your_token_here
```

Set the following environment variables in the .env file:

- `AIRTABLE_MCP_SERVER_PORT`: Port for the server (default: 5000)
- `AIRTABLE_PERSONAL_ACCESS_TOKEN`: Personal access token for the Airtable API

## Authentication

The server expects an Airtable Personal Access Token to be provided in the request headers. Authentication is handled at the tool level through the base request implementation.

## Running the Server

### Direct Python
```bash
python server.py --port 5000 --json-response
```

### Docker
from the root of the repository
```bash
docker build -t airtable-mcp-server mcp_servers/airtable
docker run -p 5000:5000 --env-file mcp_servers/airtable/.env airtable-mcp-server
```

### Command Line Options
- `--port`: Port to listen on (default: 5000)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--json-response`: Enable JSON responses for StreamableHTTP instead of SSE streams

## API Endpoints

- **SSE**: `GET /sse` - Server-Sent Events endpoint for MCP communication
- **StreamableHTTP**: `POST /mcp` - StreamableHTTP endpoint for MCP communication

## Dependencies

- mcp>=1.8.1
- httpx
- starlette
- uvicorn
- click
- python-dotenv
