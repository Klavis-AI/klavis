# Hugging Face Official MCP Server 

<img src='https://github.com/evalstate/hf-mcp-server/blob/main/hf-logo.svg' width='100'>

Welcome to the official Hugging Face MCP Server 🤗. Connect your LLM to the Hugging Face Hub and thousands of Gradio AI Applications.

## Installing the MCP Server

Follow the instructions below to get started:

<details>
<summary>Install in <b>Claude Desktop</b> or <b>claude.ai</b></summary>
<br />

Click [here](https://claude.ai/redirect/website.v1.67274164-23df-4883-8166-3c93ced276be/directory/37ed56d5-9d61-4fd4-ad00-b9134c694296) to add the Hugging Face connector to your account. 

Alternatively, navigate to [https://claude.ai/settings/connectors](https://claude.ai/settings/connectors), and add "Hugging Face" from the gallery.

<img src='docs/claude-badge.png' width='50%' align='center' />

</details>

<details>
<summary>Install in <b>Claude Code</b></summary>
<br />

Enter the command below to install in <b>Claude Code</b>:

```bash
claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login
```

Then start `claude` and follow the instructions to complete authentication.

```bash
claude mcp add hf-mcp-server \
  -t http https://huggingface.co/mcp \
  -H "Authorization: Bearer <YOUR_HF_TOKEN>"
```


</details>

<details>
<summary>Install in <b>Gemini CLI</b></summary>
<br />

Enter the command below to install in <b>Gemini CLI</b>:

```bash
gemini mcp add -t http huggingface https://huggingface.co/mcp?login
```

Then start `gemini` and follow the instructions to complete authentication.

There is also a HuggingFace Gemini CLI extension that bundles the MCP server
with a context file and custom commands, teaching Gemini how to better use
all MCP tools.

```bash
gemini extensions install https://github.com/huggingface/hf-mcp-server
```

Start `gemini` and run `/mcp auth huggingface` to authenticate the extension.

</details>

<details>

<summary>Install in <b>VSCode</b></summary>
<br />

Click <a href="vscode:mcp/install?%7B%22name%22%3A%22huggingface%22%2C%22gallery%22%3Atrue%2C%22url%22%3A%22https%3A%2F%2Fhuggingface.co%2Fmcp%3Flogin%22%7D">here</a> to add the Hugging Face connector directly to VSCode. Alternatively, install from the gallery at [https://code.visualstudio.com/mcp](https://code.visualstudio.com/mcp): 

<img src='docs/vscode-badge.png' width='50%' align='center' />

If you prefer to configure manually or use an auth token, add the snippet below to your `mcp.json` configuration:


```JSON
"huggingface": {
    "url": "https://huggingface.co/mcp",
    "headers": {
        "Authorization": "Bearer <YOUR_HF_TOKEN>"
    }
```

</details>

<details>
<summary>Install in <b>Cursor</b></summary>
<br />

Click <a href="https://cursor.com/en/install-mcp?name=Hugging%20Face&config=eyJ1cmwiOiJodHRwczovL2h1Z2dpbmdmYWNlLmNvL21jcD9sb2dpbiJ9">here</a> to install the Hugging Face MCP Server directly in <b>Cursor</b>. 

If you prefer to use configure manually or specify an Authorization Token, use the snippet below:

```JSON
"huggingface": {
    "url": "https://huggingface.co/mcp",
    "headers": {
        "Authorization": "Bearer <YOUR_HF_TOKEN>"
    }
```
</details>

Once installed, navigate to https://huggingface.co/settings/mcp to configure your Tools and Spaces.

> [!TIP]
> Add ?no_image_content=true to the URL to remove ImageContent blocks from Gradio Servers.


![hf_mcp_server_small](https://github.com/user-attachments/assets/d30f9f56-b08c-4dfc-a68f-a164a93db564)


## Quick Guide (Repository Packages)

This repo contains:

 - (`/mcp`) MCP Implementations of Hub API and Search endpoints for integration with MCP Servers. 
 - (`/app`) An MCP Server and Web Application for deploying endpoints.

### MCP Server

The following transports are supported:

- STDIO 
- StreamableHTTP
- StreamableHTTP in Stateless JSON Mode (**StreamableHTTPJson**)

The Web Application and HTTP Transports start by default on Port 3000.

The StreamableHTTP service is available at `/mcp`. Although though not strictly enforced by the specification this is common convention.

> [!TIP]
> The Web Application allows you to switch tools on and off. For STDIO and StreamableHTTP this will send a ToolListChangedNotification to the MCP Client. In StreamableHTTPJSON mode the tool will not be listed when the client next requests the tool lists.

### Running Locally

You can run the MCP Server locally with either `npx` or `docker`. 

```bash
npx @llmindset/hf-mcp-server       # Start in STDIO mode
npx @llmindset/hf-mcp-server-http  # Start in Streamable HTTP mode
npx @llmindset/hf-mcp-server-json  # Start in Streamable HTTP (JSON RPC) mode
```

To run with docker: 

```bash
docker pull ghcr.io/evalstate/hf-mcp-server:latest
docker run --rm -p 3000:3000 ghcr.io/evalstate/hf-mcp-server:latest
```
![image](https://github.com/user-attachments/assets/2fc0ef58-2c7a-4fae-82b5-e6442bfcbd99)

All commands above start the Management Web interface on http://localhost:3000/. The Streamable HTTP server is accessible on  http://localhost:3000/mcp. See [Environment Variables](#Environment Variables) for configuration options. Docker defaults to Streamable HTTP (JSON RPC) mode.

### Developing OpenAI Apps SDK Components

To build and test the Apps SDK component, run 

```bash
cd packages/app
npm run dev:widget
```

Then open `http://localhost:5173/gradio-widget-dev.html`. This will bring up a browser with HMR where you can send Structured Content to the components for testing. 

![skybridge-viewer](./docs/skybridge-dev.png)


## Development

This project uses `pnpm` for build and development. Corepack is used to ensure everyone uses the same pnpm version (10.12.3).

```bash
# Install dependencies
pnpm install

# Build all packages
pnpm build
```

### Build Commands

`pnpm run clean` -> clean build artifacts

`pnpm run build` -> build packages

`pnpm run start` -> start the mcp server application

`pnpm run buildrun` -> clean, build and start

`pnpm run dev` -> concurrently watch `mcp` and start dev server with HMR


## Docker Build

Build the image:
```bash
docker build -t hf-mcp-server .
```

Run with default settings (Streaming HTTP JSON Mode), Dashboard on Port 3000:
```bash
docker run --rm -p 3000:3000 -e DEFAULT_HF_TOKEN=hf_xxx hf-mcp-server
```

Run STDIO MCP Server:
```bash
docker run -i --rm -e TRANSPORT=stdio -p 3000:3000 -e DEFAULT_HF_TOKEN=hf_xxx hf-mcp-server
```

`TRANSPORT` can be `stdio`, `streamableHttp` or `streamableHttpJson` (default).

### Transport Endpoints

The different transport types use the following endpoints:
- Streamable HTTP: `/mcp` (regular or JSON mode)
- STDIO: Uses stdin/stdout directly, no HTTP endpoint

### Stateful Connection Management

The `streamableHttp` transport is _stateful_ - it maintains a connection with the MCP Client through an SSE connection. When using this transport, the following configuration options take effect:

| Environment Variable              | Default | Description |
|-----------------------------------|---------|-------------|
| `MCP_CLIENT_HEARTBEAT_INTERVAL`   | 30000ms | How often to check connection health |
| `MCP_CLIENT_CONNECTION_CHECK`     | 90000ms | How often to check for stale sessions |
| `MCP_CLIENT_CONNECTION_TIMEOUT`   | 300000ms | Remove sessions inactive for this duration |
| `MCP_PING_ENABLED`                | true    | Enable ping keep-alive for sessions |
| `MCP_PING_INTERVAL`               | 30000ms | Interval between ping cycles | 


### Environment Variables

The server respects the following environment variables:
- `TRANSPORT`: The transport type to use (stdio, streamableHttp, or streamableHttpJson)
- `DEFAULT_HF_TOKEN`: ⚠️ Requests are serviced with the HF_TOKEN received in the Authorization: Bearer header. The DEFAULT_HF_TOKEN is used if no header was sent. Only set this in Development / Test environments or for local STDIO Deployments. ⚠️
- If running with `stdio` transport, `HF_TOKEN` is used if `DEFAULT_HF_TOKEN` is not set.
- `HF_API_TIMEOUT`: Timeout for Hugging Face API requests in milliseconds (default: 12500ms / 12.5 seconds)
- `USER_CONFIG_API`: URL to use for User settings (defaults to Local front-end)
- `MCP_STRICT_COMPLIANCE`: set to True for GET 405 rejects in JSON Mode (default serves a welcome page).
- `AUTHENTICATE_TOOL`: whether to include an `Authenticate` tool to issue an OAuth challenge when called
- `SEARCH_ENABLES_FETCH`: When set to `true`, automatically enables the `hf_doc_fetch` tool whenever `hf_doc_search` is enabled
- `PROXY_TOOLS_CSV`: Optional CSV that defines Streamable HTTP proxy tool sources (see below).
- `GRADIO_SKIP_INITIALIZE`: When set to `true`, Gradio MCP calls skip the `initialize` handshake and issue `tools/call` directly.

### Proxy tools (Streamable HTTP via CSV)

You can load proxy tool definitions at startup by setting `PROXY_TOOLS_CSV` to a **HTTPS URL** or a **local file path**.
The server fetches each MCP endpoint once on startup, runs `initialize` + `tools/list` (10s timeout), and registers any tools returned.
If a source fails or returns no tools, it is skipped (no startup failure).

**CSV format**

```
proxy_id,url,response_type
papers,https://evalstate-hf-papers.hf.space/mcp,SSE
news,https://example.com/mcp,JSON
```

- `proxy_id`: identifier used to disambiguate tools.
- `url`: Streamable HTTP MCP endpoint.
- `response_type`: `SSE` (streamed response) or `JSON` (direct JSON-RPC response).

**Tool naming**

- Single source: tool names are **unchanged** (taken from the downstream server).
- Multiple sources: tool names are **prefixed** with `proxy_id_` (e.g. `papers_hf-papers-search_send`).

You can include these tool names in bouquets or mixes as needed.
Use `bouquet=proxy` or `mix=proxy` to enable all proxy tools loaded from `PROXY_TOOLS_CSV` (in addition to the base built-in tools).
