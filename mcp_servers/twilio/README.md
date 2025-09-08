# Twilio MCP Server

A comprehensive Model Context Protocol (MCP) server implementation that provides full integration with Twilio's communication APIs. This server enables AI agents to send SMS/MMS messages, make voice calls, manage phone numbers, and monitor account usage through a set of atomic, well-designed tools.

## Features

- **15 Comprehensive Tools**: Complete coverage of Twilio's communication APIs
- **SMS & MMS Messaging**: Send text messages and multimedia content
- **Voice Calls**: Initiate calls with TwiML control and call management  
- **Phone Number Management**: Search, purchase, configure, and release phone numbers
- **Account Monitoring**: Check balances, usage records, and account information
- **Dual Mode Architecture**: Supports both Claude Desktop (stdio) and HTTP server modes
- **Secure Authentication**: Context-aware token management with environment variables
- **Detailed Logging**: Configurable logging with rich operational context
- **Error Handling**: Comprehensive error handling with actionable error messages

## Tools Overview

The server provides 15 atomic tools organized into four main categories:

### Messaging Operations
- `twilio_send_sms`: Send SMS messages with delivery tracking
- `twilio_send_mms`: Send multimedia messages with up to 10 attachments
- `twilio_get_messages`: Retrieve message history with flexible filtering
- `twilio_get_message_by_sid`: Get detailed information about specific messages

### Voice Operations  
- `twilio_make_call`: Initiate phone calls with TwiML instructions
- `twilio_get_calls`: Retrieve call history with status filtering
- `twilio_get_call_by_sid`: Get detailed call information including duration and costs
- `twilio_get_recordings`: Access call recordings for analysis

### Phone Number Management
- `twilio_search_available_numbers`: Find available numbers by area code or pattern
- `twilio_purchase_phone_number`: Purchase numbers with webhook configuration
- `twilio_list_phone_numbers`: View all owned phone numbers and their settings
- `twilio_update_phone_number`: Modify number configurations and webhooks
- `twilio_release_phone_number`: Release numbers to stop billing

### Account & Usage Monitoring
- `twilio_get_account_info`: Retrieve account details and status
- `twilio_get_balance`: Check current account balance
- `twilio_get_usage_records`: Generate detailed usage reports by category and time period

## Installation & Setup

### Prerequisites

1. **Twilio Account**: Sign up at [twilio.com](https://www.twilio.com)
2. **API Credentials**: Obtain your Account SID and Auth Token from the Twilio Console
3. **Python 3.8+**: Required for running the server
4. **Phone Number**: Purchase at least one Twilio phone number for sending messages/calls

### Quick Setup Guide

#### Step 1: Get Twilio Credentials
1. Sign up or log in to [Twilio Console](https://console.twilio.com)
2. Navigate to **Account Dashboard**
3. Copy your **Account SID** and **Auth Token**
4. (Optional) Purchase a phone number from **Phone Numbers > Manage > Buy a number**

#### Step 2: Install Dependencies
```bash
# Navigate to the Twilio MCP server directory
cd mcp_servers/twilio

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables
1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your Twilio credentials:
   ```bash
   # Open .env in your preferred editor
   nano .env  # or vim .env, or code .env
   ```

   Add your credentials:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_MCP_SERVER_PORT=5000
   ```

## Running the Server

The Twilio MCP server supports two modes:

### Mode 1: Claude Desktop Integration (stdio)
For use with Claude Desktop or other MCP clients that use stdio transport:

```bash
python server.py --stdio
```

**Claude Desktop Configuration:**
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "twilio": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["/path/to/mcp_servers/twilio/server.py", "--stdio"],
      "env": {
        "TWILIO_ACCOUNT_SID": "your_account_sid_here",
        "TWILIO_AUTH_TOKEN": "your_auth_token_here"
      }
    }
  }
}
```

### Mode 2: HTTP Server (default)
For API testing, web integration, or other MCP clients that use HTTP transport:

```bash
python server.py
# Server runs on http://localhost:5000
```

**Custom Configuration Options:**
```bash
# Custom port and logging level
python server.py --port 8080 --log-level DEBUG

# Enable JSON responses instead of SSE streams  
python server.py --json-response
```

### Docker Installation

For containerized deployment:

1. **Set up environment variables** (follow Step 3 above):
   ```bash
   cp .env.example .env
   # Edit .env with your Twilio credentials
   ```

2. **Build the Docker image**:
   ```bash
   docker build -t twilio-mcp-server .
   ```

3. **Run in HTTP mode** (default):
   ```bash
   docker run -p 5000:5000 --env-file .env twilio-mcp-server
   ```

4. **Run in stdio mode** (for MCP client integration):
   ```bash
   docker run --env-file .env twilio-mcp-server --stdio
   ```

## Testing Your Setup

### Quick Test Commands

1. **Test HTTP mode** (server running on localhost:5000):
   ```bash
   # Health check
   curl http://localhost:5000/
   
   # List available tools
   curl -X POST http://localhost:5000/ \
     -H "Content-Type: application/json" \
     -d '{"method": "tools/list"}'
   
   # Test account info (requires credentials in .env)
   curl -X POST http://localhost:5000/ \
     -H "Content-Type: application/json" \
     -d '{"method": "tools/call", "params": {"name": "twilio_get_account_info", "arguments": {}}}'
   ```

2. **Test Claude Desktop Integration**:
   - Add the server to your Claude Desktop config
   - Restart Claude Desktop
   - Ask Claude: "Can you check my Twilio account balance?"

## Usage Examples

### Available Server Endpoints

**HTTP Mode (default):**
- **Health Check**: `GET http://localhost:5000/`
- **SSE Streaming**: `GET http://localhost:5000/sse`
- **StreamableHTTP**: `POST http://localhost:5000/mcp`

**Stdio Mode:**
- Communicates via standard input/output for MCP client integration

### Example Tool Calls

#### Send an SMS Message
```json
{
  "tool": "twilio_send_sms",
  "arguments": {
    "to": "+1234567890",
    "from_": "+1987654321", 
    "body": "Hello from Twilio MCP Server!"
  }
}
```

#### Make a Voice Call
```json
{
  "tool": "twilio_make_call",
  "arguments": {
    "to": "+1234567890",
    "from_": "+1987654321",
    "twiml": "<Response><Say>Hello, this is a test call from Twilio!</Say></Response>"
  }
}
```

#### Search for Available Numbers
```json
{
  "tool": "twilio_search_available_numbers", 
  "arguments": {
    "country_code": "US",
    "area_code": "415",
    "sms_enabled": true,
    "voice_enabled": true,
    "limit": 10
  }
}
```

#### Check Account Usage
```json
{
  "tool": "twilio_get_usage_records",
  "arguments": {
    "category": "sms",
    "granularity": "daily",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

## Error Handling & Troubleshooting

The server provides detailed error information to help diagnose issues:

### Common Error Scenarios

1. **Authentication Errors**:
   - Verify `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct
   - Check that credentials haven't expired or been rotated

2. **Phone Number Format Errors**:
   - Ensure numbers are in E.164 format (e.g., `+1234567890`)
   - US numbers: 11 digits total including country code

3. **Permission Errors**:
   - Verify your Twilio account has sufficient permissions
   - Check if services (SMS, Voice) are enabled in your region

4. **Rate Limiting**:
   - Twilio has rate limits on API calls and messaging
   - Implement exponential backoff for production use


### Debugging Tips

1. **Enable Debug Logging**:
   ```bash
   python server.py --log-level DEBUG
   ```

2. **Test with Twilio Console**: 
   - Use Twilio's REST API Explorer to test credentials
   - Send test messages through the Console first

## Development & Testing

### Local Development

1. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Use Twilio Test Credentials**:
   - Use Twilio's test credentials for development
   - Test credentials don't send real messages or make real calls

## Quick Start

### Option 1: Local Installation
```bash
# 1. Navigate to the Twilio MCP server directory
cd mcp_servers/twilio

# 2. Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up your environment
cp .env.example .env
# Edit .env with your Twilio credentials

# 4. Run the server
python server.py --stdio  # For Claude Desktop
# OR
python server.py          # For HTTP API testing
```

### Option 2: Docker Installation
```bash
# 1. Set up environment and build
cp .env.example .env
# Edit .env with your Twilio credentials  
docker build -t twilio-mcp-server .

# 2. Run the server
docker run -p 5000:5000 --env-file .env twilio-mcp-server
```

### Option 3: Claude Desktop Integration
1. Follow local installation steps 1-3 above
2. Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "twilio": {
      "command": "/absolute/path/to/your/venv/bin/python",
      "args": ["/absolute/path/to/mcp_servers/twilio/server.py", "--stdio"],
      "env": {
        "TWILIO_ACCOUNT_SID": "your_account_sid_here",
        "TWILIO_AUTH_TOKEN": "your_auth_token_here"
      }
    }
  }
}
```
3. Restart Claude Desktop
4. Ask Claude: "Can you check my Twilio account info?"

## Contributing

We welcome contributions! Please see the main [Contributing Guide](../../CONTRIBUTING.md) for details on:

- Code style guidelines
- Pull request process  
- Testing requirements
- Documentation standards

### Twilio-Specific Contribution Guidelines

- Test all tools with both valid and invalid inputs
- Ensure proper error handling for Twilio API errors
- Update documentation for any new Twilio features
- Include usage examples for new tools

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Support & Resources

- **Twilio Documentation**: [https://www.twilio.com/docs](https://www.twilio.com/docs)
- **Twilio Console**: [https://console.twilio.com](https://console.twilio.com)
- **MCP Specification**: [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues**: [Report bugs or request features](https://github.com/klavis-ai/klavis/issues)

---