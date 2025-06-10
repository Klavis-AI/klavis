# MCP Streamable HTTP Client Example

Simple example showing how to connect to an MCP server using StreamableHTTP transport.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set your Klavis API key:
```bash
export KLAVIS_API_KEY=your_api_key_here
```

## Run

```bash
npm run build
npm start
```

The example will:
- Create an MCP instance using Klavis API
- Connect to the MCP server via StreamableHTTP
- List available tools
- Close the connection 