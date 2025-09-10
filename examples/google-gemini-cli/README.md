# klavis

A CLI tool for easily managing Klavis AI MCP servers in Google Gemini CLI.

## Installation

```bash
npm install -g klavis
```

## Usage

### Help

```bash
klavis gemini --help
```

Shows detailed help information with all commands and examples.

## Commands

### Add MCP Server

```bash
klavis gemini add <INSTANCE_URL>
```

**Parameters:**
- `<INSTANCE_URL>`: URL of your MCP server instance.

**Note:** Only Klavis AI MCPs can be added with this tool.

### Remove MCP Server

```bash
klavis gemini remove <MCP_NAME>
```

**Parameters:**
- `<MCP_NAME>`: Name of the MCP to remove (e.g., `gmail`, `slack`, `notion`)

**Note:** Only Klavis AI MCPs can be removed with this tool.

### List MCP Servers

```bash
klavis gemini list
```

Shows all currently configured Klavis AI MCP servers.

### Clear All MCP Servers

```bash
klavis gemini clear --force
```

Removes all Klavis AI MCP servers from the configuration. Requires `--force` flag for safety.

### Examples

**Add Gmail MCP Server:**
```bash
klavis gemini add https://gmail-mcp-server.klavis.ai/mcp/?instance_id=your-id
```

**Add Slack MCP Server:**
```bash
klavis gemini add https://slack-mcp-server.klavis.ai/mcp/?instance_id=your-id
```

**Add Notion MCP Server:**
```bash
klavis gemini add https://notion-mcp-server.klavis.ai/mcp/?instance_id=your-id
```

**Remove Gmail MCP Server:**
```bash
klavis gemini remove gmail
```

**Remove Slack MCP Server:**
```bash
klavis gemini remove slack
```

**List all MCP Servers:**
```bash
klavis gemini list
```

**Clear all MCP Servers:**
```bash
klavis gemini clear --force
```

## What It Does

1. **Locates** your Gemini config settings (`~/.gemini/settings.json`)
2. **Creates backup** of existing settings
3. **Adds, removes, lists, or clears** Klavis AI MCP server configurations in your Gemini settings
4. **Preserves** all existing preferences and authentication

## Configuration

After adding an MCP server, it will be added to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "npx",
      "args": ["mcp-remote", "https://gmail-mcp-server.klavis.ai/mcp/?instance_id=your-id"]
    }
  }
}
```

## Requirements

- Node.js 14.0.0 or higher
- Google Gemini installed with `.gemini` configuration directory

## License

MIT