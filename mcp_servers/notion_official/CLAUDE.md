# CLAUDE.md

This file provides guidance for Claude Code when working with this repository.

## Project Overview

This is the Notion MCP Server - an [MCP (Model Context Protocol)](https://spec.modelcontextprotocol.io/) server that exposes the [Notion API](https://developers.notion.com/reference/intro) as MCP tools. It auto-generates tools from an OpenAPI specification.

## Architecture

```
scripts/notion-openapi.json    # OpenAPI spec (source of truth for all tools)
        ↓
src/init-server.ts             # Loads & validates spec, creates MCPProxy
        ↓
src/openapi-mcp-server/
├── openapi/parser.ts          # Converts OpenAPI → MCP tools
├── mcp/proxy.ts               # Registers tools with MCP server
└── client/http-client.ts      # Executes API calls
```

## Key Patterns

### Adding New Endpoints

Only modify `scripts/notion-openapi.json`. Tools are auto-generated from the spec - no code changes needed elsewhere.

### Tool Generation Flow

1. `OpenAPIToMCPConverter.convertToMCPTools()` iterates all paths/operations
2. Each operation becomes an MCP tool (name = `operationId`)
3. Parameters + requestBody → `inputSchema`
4. Response schema → `returnSchema`
5. `MCPProxy.setupHandlers()` registers tools with the MCP SDK

### Naming Conventions

- Tool names come from OpenAPI `operationId` (e.g., `retrieve-a-database`)
- Names are truncated to 64 chars and converted to title case for display

## Common Commands

```bash
npm run build      # TypeScript compilation + CLI bundling
npm test           # Run vitest tests
npm run dev        # Start dev server with hot reload
```

## File Structure

- `scripts/notion-openapi.json` - OpenAPI 3.1.0 spec defining all Notion API endpoints
- `scripts/start-server.ts` - Entry point
- `src/init-server.ts` - Server initialization
- `src/openapi-mcp-server/` - Core MCP server implementation
  - `openapi/parser.ts` - OpenAPI to MCP conversion (529 lines)
  - `mcp/proxy.ts` - MCP tool registration and execution (209 lines)
  - `client/http-client.ts` - HTTP request execution (198 lines)

## Testing

Tests are in `__tests__` directories adjacent to source files. Run with `npm test`.

## API Version

Uses Notion API version `2025-09-03` (Data Source Edition). The spec includes both:
- `/v1/databases/{database_id}` - Traditional database endpoints
- `/v1/data_sources/{data_source_id}` - New data source endpoints
