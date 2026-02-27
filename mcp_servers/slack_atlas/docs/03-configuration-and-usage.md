## 3. Configuration and Usage

You can configure the MCP server using command line arguments and environment variables.

### Using DXT

For [Claude Desktop](https://claude.ai/download) users, you can use the DXT extension to run the MCP server without needing to edit the `claude_desktop_config.json` file directly. Download the [latest version](https://github.com/korotovsky/slack-mcp-server/releases/latest/download/slack-mcp-server.dxt) of the DXT Extension from [releases](https://github.com/korotovsky/slack-mcp-server/releases) page.

1. Open Claude Desktop and go to the `Settings` menu.
2. Click on the `Extensions` tab.
3. Drag and drop the downloaded .dxt file to install it and click "Install".
5. Fill all required configuration fields
    - Authentication method: `xoxc/xoxd` or `xoxp`.
    - Value for `SLACK_MCP_XOXC_TOKEN` and `SLACK_MCP_XOXD_TOKEN` in case of `xoxc/xoxd` method, or `SLACK_MCP_XOXP_TOKEN` in case of `xoxp`.
    - You may also enable `Add Message Tool` to allow posting messages to channels.
    - You may also change User-Agent if needed if you have Enterprise Slack.
6. Enbale MCP Server.

> [!IMPORTANT]
> You may need to disable bundled node in Claude Desktop and let it use node from host machine to avoid some startup issues in case you encounter them. It is DXT known bug: https://github.com/anthropics/dxt/issues/45#issuecomment-3050284228

### Using Cursor Installer

The MCP server can be installed using the Cursor One-Click method.

Below are prepared configurations:

 - `npx` and `xoxc/xoxd` method: [![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/install-mcp?name=slack-mcp-server&config=eyJjb21tYW5kIjogIm5weCAteSBzbGFjay1tY3Atc2VydmVyQGxhdGVzdCAtLXRyYW5zcG9ydCBzdGRpbyIsImVudiI6IHsiU0xBQ0tfTUNQX1hPWENfVE9LRU4iOiAieG94Yy0uLi4iLCAiU0xBQ0tfTUNQX1hPWERfVE9LRU4iOiAieG94ZC0uLi4ifSwiZGlzYWJsZWQiOiBmYWxzZSwiYXV0b0FwcHJvdmUiOiBbXX0%3D)
 - `npx` and `xoxp` method: [![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/install-mcp?name=slack-mcp-server&config=eyJjb21tYW5kIjogIm5weCAteSBzbGFjay1tY3Atc2VydmVyQGxhdGVzdCAtLXRyYW5zcG9ydCBzdGRpbyIsImVudiI6IHsiU0xBQ0tfTUNQX1hPWFBfVE9LRU4iOiAieG94cC0uLi4ifSwiZGlzYWJsZWQiOiBmYWxzZSwiYXV0b0FwcHJvdmUiOiBbXX0%3D)

> [!IMPORTANT]
> Remember to replace tokens in the configuration with your own tokens, as they are just examples.

### Using npx

If you have npm installed, this is the fastest way to get started with `slack-mcp-server` on Claude Desktop.

Open your `claude_desktop_config.json` and add the mcp server to the list of `mcpServers`:

> [!WARNING]  
> If you are using Enterprise Slack, you may set `SLACK_MCP_USER_AGENT` environment variable to match your browser's User-Agent string from where you extracted `xoxc` and `xoxd` and enable `SLACK_MCP_CUSTOM_TLS` to enable custom TLS-handshakes to start to look like a real browser. This is required for the server to work properly in some environments with higher security policies.

**Option 1: Using XOXP Token**
``` json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "slack-mcp-server@latest",
        "--transport",
        "stdio"
      ],
      "env": {
        "SLACK_MCP_XOXP_TOKEN": "xoxp-..."
      }
    }
  }
}
```

**Option 2: Using XOXC/XOXD Tokens**
``` json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "slack-mcp-server@latest",
        "--transport",
        "stdio"
      ],
      "env": {
        "SLACK_MCP_XOXC_TOKEN": "xoxc-...",
        "SLACK_MCP_XOXD_TOKEN": "xoxd-..."
      }
    }
  }
}
```

<details>
<summary>Or, stdio transport with docker.</summary>

**Option 1: Using XOXP Token**
```json
{
  "mcpServers": {
    "slack": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "SLACK_MCP_XOXP_TOKEN",
        "ghcr.io/korotovsky/slack-mcp-server",
        "mcp-server",
        "--transport",
        "stdio"
      ],
      "env": {
        "SLACK_MCP_XOXP_TOKEN": "xoxp-..."
      }
    }
  }
}
```

**Option 2: Using XOXC/XOXD Tokens**
```json
{
  "mcpServers": {
    "slack": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "SLACK_MCP_XOXC_TOKEN",
        "-e",
        "SLACK_MCP_XOXD_TOKEN",
        "ghcr.io/korotovsky/slack-mcp-server",
        "mcp-server",
        "--transport",
        "stdio"
      ],
      "env": {
        "SLACK_MCP_XOXC_TOKEN": "xoxc-...",
        "SLACK_MCP_XOXD_TOKEN": "xoxd-..."
      }
    }
  }
}
```

Please see [Docker](#Using-Docker) for more information.
</details>

### Using npx with `sse` transport:

In case you would like to run it in `sse` mode, then you  should use `mcp-remote` wrapper for Claude Desktop and deploy/expose MCP server somewhere e.g. with `ngrok` or `docker-compose`.

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://x.y.z.q:3001/sse",
        "--header",
        "Authorization: Bearer ${SLACK_MCP_SSE_API_KEY}"
      ],
      "env": {
        "SLACK_MCP_SSE_API_KEY": "my-$$e-$ecret"
      }
    }
  }
}
```

<details>
<summary>Or, sse transport for Windows.</summary>

```json
{
  "mcpServers": {
    "slack": {
      "command": "C:\\Progra~1\\nodejs\\npx.cmd",
      "args": [
        "-y",
        "mcp-remote",
        "https://x.y.z.q:3001/sse",
        "--header",
        "Authorization: Bearer ${SLACK_MCP_SSE_API_KEY}"
      ],
      "env": {
        "SLACK_MCP_SSE_API_KEY": "my-$$e-$ecret"
      }
    }
  }
}
```
</details>

### TLS and Exposing to the Internet

There are several reasons why you might need to setup HTTPS for your SSE.
- `mcp-remote` is capable to handle only https schemes;
- it is generally a good practice to use TLS for any service exposed to the internet;

You could use `ngrok`:

```bash
ngrok http 3001
```

and then use the endpoint `https://903d-xxx-xxxx-xxxx-10b4.ngrok-free.app` for your `mcp-remote` argument.

### Using Docker

For detailed information about all environment variables, see [Environment Variables](https://github.com/korotovsky/slack-mcp-server?tab=readme-ov-file#environment-variables).

```bash
export SLACK_MCP_XOXC_TOKEN=xoxc-...
export SLACK_MCP_XOXD_TOKEN=xoxd-...

docker pull ghcr.io/korotovsky/slack-mcp-server:latest
docker run -i --rm \
  -e SLACK_MCP_XOXC_TOKEN \
  -e SLACK_MCP_XOXD_TOKEN \
  slack-mcp-server mcp-server --transport stdio
```

Or, the docker-compose way:

```bash
wget -O docker-compose.yml https://github.com/korotovsky/slack-mcp-server/releases/latest/download/docker-compose.yml
wget -O .env https://github.com/korotovsky/slack-mcp-server/releases/latest/download/default.env.dist
nano .env # Edit .env file with your tokens from step 1 of the setup guide
docker-compose up -d
```

### Console Arguments

| Argument              | Required ? | Description                                                              |
|-----------------------|------------|--------------------------------------------------------------------------|
| `--transport` or `-t` | Yes        | Select transport for the MCP Server, possible values are: `stdio`, `sse` |

### Environment Variables

| Variable                          | Required? | Default                   | Description                                                                                                                                                                                                                                                                               |
|-----------------------------------|-----------|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `SLACK_MCP_XOXC_TOKEN`            | Yes*      | `nil`                     | Slack browser token (`xoxc-...`)                                                                                                                                                                                                                                                          |
| `SLACK_MCP_XOXD_TOKEN`            | Yes*      | `nil`                     | Slack browser cookie `d` (`xoxd-...`)                                                                                                                                                                                                                                                     |
| `SLACK_MCP_XOXP_TOKEN`            | Yes*      | `nil`                     | User OAuth token (`xoxp-...`) — alternative to xoxc/xoxd                                                                                                                                                                                                                                  |
| `SLACK_MCP_PORT`                  | No        | `13080`                   | Port for the MCP server to listen on                                                                                                                                                                                                                                                      |
| `SLACK_MCP_HOST`                  | No        | `127.0.0.1`               | Host for the MCP server to listen on                                                                                                                                                                                                                                                      |
| `SLACK_MCP_SSE_API_KEY`           | No        | `nil`                     | Bearer token for SSE transport                                                                                                                                                                                                                                                            |
| `SLACK_MCP_PROXY`                 | No        | `nil`                     | Proxy URL for outgoing requests                                                                                                                                                                                                                                                           |
| `SLACK_MCP_USER_AGENT`            | No        | `nil`                     | Custom User-Agent (for Enterprise Slack environments)                                                                                                                                                                                                                                     |
| `SLACK_MCP_CUSTOM_TLS`            | No        | `nil`                     | Send custom TLS-handshake to Slack servers based on `SLACK_MCP_USER_AGENT` or default User-Agent. (for Enterprise Slack environments)                                                                                                                                                     |
| `SLACK_MCP_SERVER_CA`             | No        | `nil`                     | Path to CA certificate                                                                                                                                                                                                                                                                    |
| `SLACK_MCP_SERVER_CA_TOOLKIT`     | No        | `nil`                     | Inject HTTPToolkit CA certificate to root trust-store for MitM debugging                                                                                                                                                                                                                  |
| `SLACK_MCP_SERVER_CA_INSECURE`    | No        | `false`                   | Trust all insecure requests (NOT RECOMMENDED)                                                                                                                                                                                                                                             |
| `SLACK_MCP_ADD_MESSAGE_TOOL`      | No        | `nil`                     | Enable message posting via `conversations_add_message` by setting it to true for all channels, a comma-separated list of channel IDs to whitelist specific channels, or use `!` before a channel ID to allow all except specified ones, while an empty value disables posting by default. |
| `SLACK_MCP_ADD_MESSAGE_MARK`      | No        | `nil`                     | When the `conversations_add_message` tool is enabled, any new message sent will automatically be marked as read.                                                                                                                                                                          |
| `SLACK_MCP_ADD_MESSAGE_UNFURLING` | No        | `nil`                     | Enable to let Slack unfurl posted links or set comma-separated list of domains e.g. `github.com,slack.com` to whitelist unfurling only for them. If text contains whitelisted and unknown domain unfurling will be disabled for security reasons.                                         |
| `SLACK_MCP_USERS_CACHE`           | No        | `.users_cache.json`       | Path to the users cache file. Used to cache Slack user information to avoid repeated API calls on startup.                                                                                                                                                                                |
| `SLACK_MCP_CHANNELS_CACHE`        | No        | `.channels_cache_v2.json` | Path to the channels cache file. Used to cache Slack channel information to avoid repeated API calls on startup.                                                                                                                                                                          |
| `SLACK_MCP_LOG_LEVEL`             | No        | `info`                    | Log-level for stdout or stderr. Valid values are: `debug`, `info`, `warn`, `error`, `panic` and `fatal`                                                                                                                                                                                   |
