# HeyGen MCP Server

A Model Context Protocol (MCP) server that provides comprehensive access to HeyGen's AI video generation platform. This server enables you to create avatar videos, manage your account, and interact with HeyGen's API through standardized MCP tools.

## Features

- **Account Management**: Check remaining credits and usage
- **Asset Management**: Browse voices, avatar groups, and avatars
- **Video Generation**: Create avatar videos with custom text and voice
- **Video Management**: List, monitor, and delete your videos
- **Dual Transport Support**: Both SSE and StreamableHTTP protocols
- **Environment Variable Support**: Flexible authentication configuration

## Tools Overview

### Account Management (1 tool)
- `heygen_get_remaining_credits` - Check your account credits

### Assets (5 tools)
- `heygen_get_voices` - List available voices (limited to first 100)
- `heygen_get_voice_locales` - Get available voice languages
- `heygen_get_avatar_groups` - List avatar groups
- `heygen_get_avatars_in_avatar_group` - Get avatars in a specific group
- `heygen_list_avatars` - List all available avatars

### Generation (2 tools)
- `heygen_generate_avatar_video` - Create new avatar videos
- `heygen_get_avatar_video_status` - Check video generation status

### Management (2 tools)
- `heygen_list_videos` - List your videos
- `heygen_delete_video` - Delete specific videos

## Prerequisites

1. **HeyGen Account**: Create an account at [HeyGen](https://www.heygen.com/)
2. **API Key**: Get your API key from the HeyGen Space Settings → API tab
3. **Python 3.11+**: Required for running the server

## Installation

### Option 1: Local Development

1. **Clone and navigate to the HeyGen server directory:**
   ```bash
   cd mcp_servers/heygen
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your HeyGen API key
   ```

5. **Run the server:**
   ```bash
   python server.py
   ```

### Option 2: Docker

1. **Build the Docker image:**
   ```bash
   docker build -t heygen-mcp-server .
   ```

2. **Run the container:**
   ```bash
   docker run -p 5000:5000 -e HEYGEN_API_KEY=your_api_key_here heygen-mcp-server
   ```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `HEYGEN_API_KEY` | Your HeyGen API key | Yes | - |
| `HEYGEN_MCP_SERVER_PORT` | Server port | No | 5000 |

### Getting Your HeyGen API Key

1. Log in to your HeyGen account
2. Click on the Space dropdown (top left corner)
3. Select "Space Settings"
4. Navigate to the "API" tab
5. Copy your API key

## Usage

### With Claude Desktop

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "heygen": {
      "command": "python",
      "args": ["/path/to/mcp_servers/heygen/server.py"],
      "env": {
        "HEYGEN_API_KEY": "your_heygen_api_key_here"
      }
    }
  }
}
```

### HTTP Transport

The server supports both SSE and StreamableHTTP transports:

- **SSE Endpoint**: `http://localhost:5000/sse`
- **StreamableHTTP Endpoint**: `http://localhost:5000/mcp`

#### Authentication Headers

For HTTP requests, include your API key in the header:
```
X-Api-Key: your_heygen_api_key_here
```

## Common Workflows

### 1. Account Setup and Exploration

```python
# Check your account credits
credits = await heygen_get_remaining_credits()

# Explore available voices
voices = await heygen_get_voices()

# Get avatar groups
avatar_groups = await heygen_get_avatar_groups()

# List all avatars
avatars = await heygen_list_avatars()
```

### 2. Create an Avatar Video

```python
# Generate a video
video_response = await heygen_generate_avatar_video(
    avatar_id="Daisy-inskirt-20220818",
    text="Welcome to our product demonstration!",
    voice_id="2d5b0e6cf36f460aa7fc47e3eee4ba54",
    background_color="#008000",
    width=1280,
    height=720
)

# Check generation status
video_id = video_response['data']['video_id']
status = await heygen_get_avatar_video_status(video_id)
```

### 3. Video Management

```python
# List your videos
videos = await heygen_list_videos(limit=10)

# Delete a specific video
result = await heygen_delete_video(video_id)
```

## API Limits and Considerations

- **Text Limit**: Video text input is limited to 1500 characters
- **Voice Limit**: The `heygen_get_voices` tool returns the first 100 voices
- **Credits**: Video generation consumes credits based on video length and quality
- **Rate Limits**: HeyGen enforces API rate limits - the server handles retries automatically

## Error Handling

The server provides comprehensive error handling:

- **Authentication Errors**: Invalid or missing API keys
- **Validation Errors**: Invalid parameters or exceeded limits
- **API Errors**: HeyGen service issues
- **Network Errors**: Connection timeouts and retries

All errors are returned in a structured format with descriptive messages.

## Development

### Project Structure

```
heygen/
├── server.py              # Main MCP server
├── tools/                 # Tool implementations
│   ├── __init__.py       # Module exports
│   ├── base.py           # HTTP client and auth
│   ├── account.py        # Account management tools
│   ├── assets.py         # Asset management tools
│   ├── generation.py     # Video generation tools
│   └── management.py     # Video management tools
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .env.example          # Environment template
└── README.md             # This file
```

### Adding New Tools

1. Implement the tool function in the appropriate module
2. Add the function to `tools/__init__.py`
3. Add the tool definition to `server.py` in the `list_tools()` function
4. Add the tool handler in the `call_tool()` function

## Testing

### Manual Testing with HTTP

Test individual tools using curl:

```bash
# Test getting credits
curl -X POST http://localhost:5000/mcp \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_api_key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "heygen_get_remaining_credits",
      "arguments": {}
    }
  }'
```

### Integration Testing

The server is designed to work seamlessly with Claude Desktop and other MCP clients.

## Troubleshooting

### Common Issues

1. **"No HeyGen API key found"**
   - Ensure `HEYGEN_API_KEY` is set in environment or .env file
   - Verify the API key is valid and not expired

2. **"HeyGen API error (401)"**
   - Check that your API key is correct
   - Verify your HeyGen account has API access enabled

3. **"Text input must be less than 1500 characters"**
   - Reduce the length of your video text
   - Consider breaking long content into multiple videos

4. **"Connection timeout"**
   - Check your internet connection
   - Verify HeyGen services are operational

### Debug Mode

Run with debug logging:
```bash
python server.py --log-level DEBUG
```

## Support

For issues specific to this MCP server:
- Check the troubleshooting section above
- Review the error messages for specific guidance

For HeyGen API issues:
- Consult the [HeyGen API Documentation](https://docs.heygen.com/)
- Contact HeyGen support for account-specific issues

## License

This MCP server is part of the Klavis project. See the main project license for details.