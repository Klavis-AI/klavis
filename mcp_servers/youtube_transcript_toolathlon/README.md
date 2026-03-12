# YouTube Transcript MCP Server

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python Application](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml/badge.svg)](https://github.com/jkawamoto/mcp-youtube-transcript/actions/workflows/python-app.yaml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![GitHub License](https://img.shields.io/github/license/jkawamoto/mcp-youtube-transcript)](https://github.com/jkawamoto/mcp-youtube-transcript/blob/main/LICENSE)
[![Dockerhub](https://img.shields.io/badge/Docker-mcp%2Fyoutube--transcript-blue.svg)](https://hub.docker.com/mcp/server/youtube_transcript)


This MCP server retrieves transcripts for given YouTube video URLs.

<a href="https://glama.ai/mcp/servers/of3kwtmlqp"><img width="380" height="200" src="https://glama.ai/mcp/servers/of3kwtmlqp/badge" alt="YouTube Transcript Server MCP server" /></a>

## Tools
This MCP server provides the following tools:

### `get_transcript`
Fetches the transcript of a specified YouTube video.

#### Parameters
- **url** *(string)*: The full URL of the YouTube video. This field is required.
- **lang** *(string, optional)*: The desired language for the transcript. Defaults to `en` if not specified.
- **next_cursor** *(string, optional)*: Cursor to retrieve the next page of the transcript.

### `get_timed_transcript`
Fetches the transcript of a specified YouTube video with timestamps.

#### Parameters
- **url** *(string)*: The full URL of the YouTube video. This field is required.
- **lang** *(string, optional)*: The desired language for the transcript. Defaults to `en` if not specified.
- **next_cursor** *(string, optional)*: Cursor to retrieve the next page of the transcript.

### `get_video_info`
Fetches the metadata of a specified YouTube video.

#### Parameters
- **url** *(string)*: The full URL of the YouTube video. This field is required.

## Installation
> [!NOTE]
> You'll need [`uv`](https://docs.astral.sh/uv) installed on your system to use `uvx` command.

### For [goose](https://block.github.io/goose/)
Please refer to this tutorial for detailed installation instructions:
[YouTube Transcript Extension](https://block.github.io/goose/docs/mcp/youtube-transcript-mcp).

### For [Claude](https://claude.com/download)

Download the latest MCP bundle `mcp-youtube-transcript.mcpb` from
the [Releases](https://github.com/jkawamoto/mcp-youtube-transcript/releases) page,
then open the downloaded `.mcpb `file or drag it into the Claude Desktop's Settings window.

<details>
<summary>Manually configuration</summary>

You can also manually configure this server for Claude Desktop.
Edit the `claude_desktop_config.json` file by adding the following entry under
`mcpServers`:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript"
      ]
    }
  }
}
```
After editing, restart the application.

</details>

For more information,
see: [Connect to local MCP servers - Model Context Protocol.](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

### For [LM Studio](https://lmstudio.ai/)
To configure this server for LM Studio, click the button below.

[![Add MCP Server youtube-transcript to LM Studio](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](https://lmstudio.ai/install-mcp?name=youtube-transcript&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL2prYXdhbW90by9tY3AteW91dHViZS10cmFuc2NyaXB0IiwibWNwLXlvdXR1YmUtdHJhbnNjcmlwdCJdfQ%3D%3D)

### Using Docker

A Docker image for this server is available on [Docker Hub](https://hub.docker.com/mcp/server/youtube_transcript/).
Please refer to the Docker Hub page for detailed usage instructions and documentation.

## Response Pagination
When retrieving transcripts for longer videos, the content may exceed the token size limits of the LLM.
To avoid this issue, this server splits transcripts that exceed 50,000 characters.
If a transcript is split, the response will include a `next_cursor`.
To retrieve the next part, include this `next_cursor` value in your request.

The token size limits vary depending on the LLM and language you are using.
If you need to split responses into smaller chunks,
you can adjust this using the `--response-limit` command line argument.
For example, the configuration below splits responses to contain no more than 15,000 characters each:

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/jkawamoto/mcp-youtube-transcript",
        "mcp-youtube-transcript",
        "--response-limit",
        "15000"
      ]
    }
  }
}
```

## Using Proxy Servers
In environments where access to YouTube is restricted, you can use proxy servers.

When using [Webshare](https://www.webshare.io/), set the username and password for the Residential Proxy using either
the environment variables `WEBSHARE_PROXY_USERNAME` and `WEBSHARE_PROXY_PASSWORD`,
or the command line arguments `--webshare-proxy-username` and `--webshare-proxy-password`.

When using other proxy servers, set the proxy server URL using either the environment variables `HTTP_PROXY` or
`HTTPS_PROXY`, or the command line arguments `--http-proxy` or `--https-proxy`.

For more details, please visit:
[Working around IP bans - YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api?tab=readme-ov-file#working-around-ip-bans-requestblocked-or-ipblocked-exception).

## License

This application is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
