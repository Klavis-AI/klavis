# Whois MCP

[Model Context Protocol](https://modelcontextprotocol.io) server for whois lookups.

<a href="https://glama.ai/mcp/servers/cwu9e3fcwg">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/cwu9e3fcwg/badge" alt="Whois MCP server" />
</a>

**Cursor IDE Demo**

https://github.com/user-attachments/assets/57a82adc-3f30-453f-aabd-7138c2e6a21d

**Claude Desktop Demo**

https://github.com/user-attachments/assets/d30a1f45-fdaf-4280-80f2-d5d4fc9743b1

## Overview

This MCP server allows AI agents like Claude Desktop, Cursor, Windsurf,.. etc to perform WHOIS lookups and retrieve domain details. 

**Purpose**
You can directly ask the AI to check if a domain is available, who owns it, when it was registered, and other important details. No need to go to browser and search.

**What is a WHOIS Lookup?**
A WHOIS lookup is the process of querying a WHOIS database to retrieve registration details about a domain name, IP address, or autonomous system. It helps users find out who owns a domain, when it was registered, when it expires, and other important details.

**What Information Can a WHOIS Lookup Provide?**

When you perform a WHOIS lookup, you can retrieve details such as:

- Domain Name – The specific domain queried
- Registrar Name – The company managing the domain registration (e.g., GoDaddy, Namecheap)
- Registrant Details – The name, organization, and contact details of the domain owner (unless protected by WHOIS privacy)
- Registration & Expiry Date – When the domain was registered and when it will expire
- Name Servers – The DNS servers the domain is using
- Domain Status – Active, expired, locked, or pending deletion
- Contact Information – Administrative, technical, and billing contacts (if not hidden)

## Available Tools

| Tool                  | Description                                |
| --------------------- | ------------------------------------------ |
| `whois_domain`        | Looksup whois information about the domain |
| `whois_tld`           | Looksup whois information about the Top Level Domain (TLD)    |
| `whois_ip`            | Looksup whois information about the IP     |
| `whois_as`            | Looksup whois information about the Autonomous System Number (ASN)     |

## Using with Cursor

**Installation - Globally**

Run the MCP server using npx:

```bash
npx -y @bharathvaj/whois-mcp@latest
```

In your Cursor IDE

1. Go to `Cursor Settings` > `MCP`
2. Click `+ Add New MCP Server`
3. Fill in the form:
   - Name: `Whois Lookup` (or any name you prefer)
   - Type: `command`
   - Command: `npx -y @bharathvaj/whois-mcp@latest`


**Installation - Project-specific**

Add an `.cursor/mcp.json` file to your project:

```json
{
  "mcpServers": {
    "whois": {
      "command": "npx",
      "args": [
        "-y",
        "@bharathvaj/whois-mcp@latest"
      ]
    }
  }
}
```

**Usage**

Once configured, the whois tools will be automatically available to the Cursor AI Agent. You can:

1. The tool will be listed under `Available Tools` in MCP settings
2. Agent will automatically use it when relevant
3. You can explicitly ask Agent to send notifications

## Using with Roo Code
Access the MCP settings by clicking “Edit MCP Settings” in Roo Code settings or using the “Roo Code: Open MCP Config” command in VS Code's command palette.

```json
{
  "mcpServers": {
    "whois": {
      "command": "npx",
      "args": [
        "-y",
        "@bharathvaj/whois-mcp@latest"
      ]
    }
  }
}
```
3. The whois capabilities will be available to Roo Code's AI agents

## Development

```bash
# Install dependencies
pnpm install

# Build
pnpm build

```

## Debugging the Server

To debug your server, you can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

First build the server

```
pnpm build
```

Run the following command in your terminal:

```
# Start MCP Inspector and server with all tools
npx @modelcontextprotocol/inspector node dist/index.js
```

## License

[MIT](LICENSE)