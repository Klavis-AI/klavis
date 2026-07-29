# Xquik MCP Gateway

This gateway exposes Xquik through Klavis over Streamable HTTP.

It proxies Xquik's canonical MCP server. Clients always receive the current
tool definitions, instructions, annotations, errors, and response contracts.

## Quick Start

```bash
pip install -r requirements.txt
XQUIK_API_KEY=<your_api_key> python server.py
```

Connect your MCP client to `http://localhost:5000/mcp`.

Override the port with `XQUIK_MCP_SERVER_PORT`.
Override the loopback host with `XQUIK_MCP_SERVER_HOST`.

## Docker

Run these commands from the Klavis repository root:

```bash
docker build -t xquik-mcp-server -f mcp_servers/xquik/Dockerfile .
docker run --rm -p 127.0.0.1:5000:5000 \
  -e XQUIK_API_KEY=<your_api_key> \
  xquik-mcp-server
```

The image runs as an unprivileged user. Its health endpoint is `/health`.

## Authentication

Use one of these methods:

1. Set `XQUIK_API_KEY` or `API_KEY`.
2. Set `AUTH_DATA` with `token`, `api_key`, or `access_token`.
3. Send the same JSON through the `x-auth-data` header.
4. Send a standard bearer token or `x-api-key` header.

`AUTH_DATA` and `x-auth-data` accept JSON or base64-encoded JSON.

Configured credentials take precedence over request credentials.

## Capabilities

The gateway exposes Xquik's current canonical MCP tools.

- `explore` searches the authenticated endpoint catalog.
- `xquik` performs the selected read, write, or automation workflow.

Xquik performs authenticated execution in its restricted MCP sandbox.
The gateway never executes submitted code locally.

See the [Xquik documentation](https://docs.xquik.com) for current workflows.

## Security

- The upstream destination is fixed to `https://xquik.com/mcp`.
- Redirects remain disabled.
- Request bodies stop at 4 MiB.
- Only MCP protocol headers pass upstream.
- Credentials never appear in logs or response errors.
- Upstream authentication challenges pass through unchanged.
- Keep configured credentials behind local or Klavis access controls.

## Test

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

Xquik is an independent third-party service. Not affiliated with X Corp.
"Twitter" and "X" are trademarks of X Corp.

## License

Apache 2.0. See the repository [LICENSE](../../LICENSE).
