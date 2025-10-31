# DataDog MCP Server

A Model Context Protocol (MCP) server providing comprehensive access to DataDog's monitoring and observability APIs using the official DataDog Python API client. This server enables AI assistants to interact with DataDog's logs, metrics, traces, incidents, hosts, monitors, and dashboards.

---

## Features & Tool Reference

The server exposes the following atomic tools, each mapping directly to a DataDog API endpoint or workflow:

### Logs & Traces

- **datadog_get_logs**: Retrieve logs based on query filters.
- **datadog_list_spans**: List spans relevant to your query.

### Metrics & Monitoring

- **datadog_list_metrics**: List available metrics in your environment.
- **datadog_get_metrics**: Query timeseries metrics data.
- **datadog_list_monitors**: Retrieve monitors and their configurations.
- **datadog_get_monitor**: Get details for a specific monitor.

### Infrastructure Management

- **datadog_list_hosts**: Get detailed host information.

### Incident Management

- **datadog_list_incidents**: Retrieve ongoing incidents.
- **datadog_get_incident**: Get details for a specific incident.

### Dashboards

- **datadog_list_dashboards**: Discover available dashboards.
- **datadog_get_dashboard**: Get details for a specific dashboard.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your DataDog credentials:

```bash
cp .env.example .env
```

Edit `.env` with your DataDog API credentials:

```env
DD_API_KEY=your_datadog_api_key_here
DD_APP_KEY=your_datadog_application_key_here
DATADOG_SITE=datadoghq.com  # or datadoghq.eu for EU instance
DATADOG_MCP_SERVER_PORT=8000
```

### 3. Acquire DataDog API credentials

- Go to DataDog → Organization Settings → API Keys
- Create or copy your API Key
- Go to DataDog → Organization Settings → Application Keys
- Create or copy your Application Key

---

## Usage

### Running the Server

Start the server with default settings:

```bash
python server.py
```

Or with custom options:

```bash
python server.py --port 8000 --log-level DEBUG
```

Endpoints:

- SSE: `http://localhost:8000/sse`
- StreamableHTTP: `http://localhost:8000/mcp`

---

## Example Tool Calls

#### Get Recent Logs

```json
{
  "name": "datadog_get_logs",
  "arguments": {
    "query": "service:web-app status:error",
    "limit": 50
  }
}
```

#### Query Metrics

```json
{
  "name": "datadog_get_metrics",
  "arguments": {
    "query": "avg:system.cpu.idle{*}"
  }
}
```

#### List Current Incidents

```json
{
  "name": "datadog_list_incidents",
  "arguments": {
    "page_size": 20
  }
}
```

#### Get Host Information

```json
{
  "name": "datadog_list_hosts",
  "arguments": {
    "filter": "env:production"
  }
}
```

---

## Tool Parameters

Each tool accepts parameters as described below. All parameters are optional unless marked as required.

### datadog_get_logs

- `query` (string, optional): Search query (default: "*")
- `from_time` (string, optional): Start time (ISO or relative)
- `to_time` (string, optional): End time (ISO or relative)
- `limit` (integer, optional): Max results (default: 100, max: 1000)
- `sort` (string, optional): "asc" or "desc" (default: "desc")

### datadog_list_spans

- `env` (string, optional): Filter by environment
- `service` (string, optional): Filter by service name
- `operation` (string, optional): Filter by operation name
- `from_time` (string, optional): Start time (ISO or relative)
- `to_time` (string, optional): End time (ISO or relative)
- `limit` (integer, optional): Max results (default: 100, max: 1000)

### datadog_list_metrics

- `query` (string, optional): Query string (default: "*")

### datadog_get_metrics

- `query` (string, required): Metric query (e.g., "avg:system.cpu.idle{*}")
- `from_time` (string, optional): Start time (Unix timestamp or relative)
- `to_time` (string, optional): End time (Unix timestamp or relative)

### datadog_list_monitors

- `group_states` (array, optional): Filter by states (e.g., ["Alert", "Warn"])
- `name` (string, optional): Filter by monitor name
- `monitor_tags` (array, optional): Filter by tags

### datadog_get_monitor

- `monitor_id` (integer, required): The monitor ID

### datadog_list_hosts

- `filter` (string, optional): Filter by tag (e.g., "env:prod")
- `sort_field` (string, optional): Field to sort by
- `sort_dir` (string, optional): "asc" or "desc"
- `start` (integer, optional): Pagination start index
- `count` (integer, optional): Number of hosts to return
- `from_time` (string, optional): Date string or relative time
- `include_muted_hosts_data` (boolean, optional): Include muted hosts
- `include_hosts_metadata` (boolean, optional): Include host metadata

### datadog_list_incidents

- `page_size` (integer, optional): Results per page (default: 10, max: 100)
- `page_offset` (integer, optional): Page offset (default: 0)
- `include` (array, optional): Include related resources

### datadog_get_incident

- `incident_id` (string, required): The incident ID
- `include` (array, optional): Include related resources

### datadog_list_dashboards

- `filter_shared` (boolean, optional): Filter by shared status
- `filter_deleted` (boolean, optional): Include deleted dashboards
- `count` (integer, optional): Number of dashboards to return
- `start` (integer, optional): Starting index

### datadog_get_dashboard

- `dashboard_id` (string, required): The dashboard ID

---

## Configuration Options

- `--port`: HTTP port (default: 8000)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--json-response`: Enable JSON responses instead of SSE streams

---

## Error Handling

- DataDog API errors are caught and returned with context
- Network timeouts and connection issues are handled gracefully
- Invalid parameters are validated before API calls
- All errors are logged with appropriate detail levels

---

## Development & Extending

To add new tools:

1. Implement the function in `server.py`
2. Register the tool in `list_tools()`
3. Handle the tool in `call_tool()`
4. Update this README with the new tool and parameters

---

## Proof of Correctness

**Required for every MCP server submission.**

For each tool, you must provide:
- Short video recordings or clear screenshots
- Each must show:
  - A natural language query in a client (e.g., Claude Desktop, Cursor)
  - Server logs confirming the correct tool was called
  - The successful result

Include these assets in your pull request or link to them in this README.

---

## Security

- Store API keys in environment variables, never in code
- Use `.env` for local development
- In production, use secure secret management systems
- All inputs are validated before making API calls

---

## References

- [DataDog API Docs](https://docs.datadoghq.com/api/latest/?tab=java)

---

## Running with Trace

```bash
DD_SERVICE="datadog_mcp" DD_ENV="dev" DD_LOGS_INJECTION=true ddtrace-run python server.py
```