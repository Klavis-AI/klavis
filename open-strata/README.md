<div align="center">
  <img width="1157" height="365" alt="image" src="https://github.com/user-attachments/assets/d1db7ed7-1bc5-4d49-a858-c10be6003347" />
</div>


# Overview

**Strata** is a unified MCP server that intelligently manages thousands of tools across multiple applications, presenting them to AI agents progressively without overwhelming the model context.

> [!TIP]
> **🚀 Looking for production-ready solution?** We offer a **fully managed Strata service** with enterprise-grade performance, native OpenAPI parsing, and advanced AI model optimizations. [Get started instantly →](https://docs.klavis.ai/documentation/concepts/strata)

**This repository contains our open-source implementation** - a streamlined version you can easily deploy as your MCP aggregation manager in your local infrastructure.

### 🚀 The Problem We Solve

Imagine you have:
- 📦 Dozens of MCP servers, each with dozens of tools
- 🤖 AI models seeing 100s-1000s of tools at once
- 📉 Degraded performance due to massive context

### ✨ The Strata Solution

Instead of flooding your AI model with hundreds of tools, Strata acts as an intelligent router:

🔍 **Smart Discovery** → Only exposes a few essential tools to the model  
🎯 **Progressive Access** → Finds and surfaces the right tool when needed  
⚡ **Optimized Context** → Maintains peak model performance  
🔗 **Seamless Integration** → Works with your existing MCP servers, and easy configuration  

Your AI agent gets access to thousands of tools while maintaining high performance! ⚡


# Quick Start

## Installation

```bash
pipx install strata-mcp
```

Or with pip:
```bash
pip install strata-mcp
```

For development:
```bash
pip install -e .
```

## Configure MCP Servers

You can configure your MCP servers by strata CLI tool. Or manually configure it in a JSON file, just like your other MCP JSON config files.

### Add MCP servers

- Stdio Server
```bash
strata add --type stdio <server_name> npx @playwright/mcp@latest
```

- SSE Server
```bash
strata add --type sse <server_name> http://localhost:8080/mcp/ --env API_KEY=your_key
```

- HTTP Server
```bash
strata add --type http <server_name> https://api.githubcopilot.com/mcp/ --header "Authorization=Bearer token"
```
- HTTP Server with OAuth
```bash
strata add --type http <server_name> https://mcp.notion.com/mcp --auth_type oauth
```


### List Servers
```bash
strata list
```

### Enable/Disable Servers
```bash
strata enable <server_name>
strata disable <server_name>
```

### Remove Servers
```bash
strata remove server-name
```

### Manual Configuration

Configuration is stored in `~/.config/strata/servers.json` by default. You can specify a custom config path:

```bash
strata --config-path /path/to/config.json add --type stdio ...
```

#### Config Format

```json
{
  "mcp": {
    "servers": {
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_TOKEN": "your_token"
        },
        "enabled": true
      },
      "api-server": {
        "type": "http",
        "url": "https://api.example.com/mcp",
        "headers": {
          "Authorization": "Bearer token"
        },
        "enabled": true
      }
    }
  }
}
```

#### Environment Variables

- `MCP_CONFIG_PATH` - Custom config file path
- `MCP_ROUTER_PORT` - Default port for HTTP/SSE server (default: 8080)

## Running Strata MCP servers

Strata itself is a MCP server. You can run and use it like a normal MCP, in stdio mode or http/sse mode.

### Stdio Mode (Default)
Run without arguments to start in stdio mode for direct MCP communication:
```bash
python -m strata
# or
strata
```

### HTTP/SSE Server Mode
Run with port to start as HTTP/SSE server:
```bash
strata run --port 8080
```

## Tool Integration

Strata can automatically configure itself in various AI assistants and IDEs that support MCP.

#### Add Strata to Claude Code
```bash
# Add to user configuration (default)
strata tool add claude

# Add to project-specific configuration
strata tool add claude --scope project
```

#### Add Strata to Gemini
```bash
strata tool add gemini
```

#### Add Strata to VSCode
```bash
strata tool add vscode
```

#### Add Strata to Cursor
```bash
# Add to user configuration (~/.cursor/mcp.json)
strata tool add cursor --scope user

# Add to project configuration (.cursor/mcp.json)
strata tool add cursor --scope project
```

**Supported scopes:**
- `user`: Global configuration (default)
- `project`: Project-specific configuration
- `local`: Same as project (for Cursor)

Note: VSCode doesn't support scope parameter and will use its default behavior.

## Available Tools

When running as a router, the following tools are exposed:

- `discover_server_actions` - Discover available actions from configured servers
- `get_action_details` - Get detailed information about a specific action
- `execute_action` - Execute an action on a target server
- `search_documentation` - Search server documentation
- `handle_auth_failure` - Handle authentication issues

# Development

### Running Tests
```bash
pytest
```

### Project Structure
- `src/strata/` - Main source code
  - `cli.py` - Command-line interface
  - `server.py` - Server implementation (stdio/HTTP/SSE)
  - `tools.py` - Tool implementations
  - `mcp_client_manager.py` - MCP client management
  - `config.py` - Configuration management

## Examples

### Running GitHub MCP Server through Router
```bash
# Add GitHub server (official HTTP server)
strata add --type http github https://api.githubcopilot.com/mcp/

# Run router in stdio mode
strata

# Or run as HTTP server
strata run --port 8080
```

### Running Multiple Servers
```bash
# Add multiple servers
strata add --type stdio playwright npx @playwright/mcp@latest
strata add --type http github https://api.githubcopilot.com/mcp/

# List all servers
strata list

# Run router with all enabled servers
strata run --port 8080
```

---

**Ready to experience the power of thousands of AI tools?** 

👉 **[Get Instant Access at Klavis AI (YC X25)](https://klavis.ai/)** 👈

*From zero to thousands of tools in under a minute!* ⏱️
