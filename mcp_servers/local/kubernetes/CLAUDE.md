# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Build and Development

- `bun run build` - Compile TypeScript to dist/ and make executables
- `bun run dev` - Start TypeScript compiler in watch mode for development
- `bun run start` - Run the compiled server from dist/index.js
- `bun run test` - Run all tests using Vitest

### Testing and Quality

- `bun run test` - Execute the complete test suite with custom sequencer (kubectl tests run last)
- Tests have 120s timeout and 60s hook timeout due to Kubernetes operations
- Use `npx @modelcontextprotocol/inspector node dist/index.js` for local testing with Inspector
- Always run single test based on with area you are working on. running all tests will take a long time.

### Local Development Testing

- `bun run chat` - Test locally with mcp-chat CLI client
- For Claude Desktop testing, point to local `dist/index.js` build

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides Kubernetes cluster management capabilities. The server connects to Kubernetes clusters via kubectl and offers both read-only and destructive operations.

### Core Components

**KubernetesManager** (`src/utils/kubernetes-manager.ts`): Central class managing Kubernetes API connections, resource tracking, port forwards, and watches. Handles kubeconfig loading from multiple sources in priority order.

**Tool Structure**: Each Kubernetes operation is implemented as a separate tool in `src/tools/`, with corresponding Zod schemas for validation. Tools are divided into:

- kubectl operations (get, describe, apply, delete, create, etc.)
- Helm operations (install, upgrade, uninstall charts)
- Specialized operations (port forwarding, scaling, rollouts)

**Resource Handlers** (`src/resources/handlers.ts`): Manage MCP resource endpoints for dynamic data retrieval.

**Configuration System** (`src/config/`): Contains schemas and templates for deployments, namespaces, containers, and cleanup operations.

### Key Architecture Patterns

- **Tool Filtering**: Non-destructive mode dynamically removes destructive tools based on `ALLOW_ONLY_NON_DESTRUCTIVE_TOOLS` environment variable
- **Unified kubectl API**: Consistent interface across all kubectl operations with standardized error handling
- **Resource Tracking**: All created resources are tracked for cleanup capabilities
- **Transport Flexibility**: Supports both StdioTransport and SSE transport for different integration scenarios

### Request Flow

1. Client sends MCP request via transport layer
2. Server filters available tools based on destructive/non-destructive mode
3. Request routed to appropriate handler (tools/resources)
4. KubernetesManager executes Kubernetes API calls
5. Responses formatted and returned through transport

## Development Guidelines

### Adding New Tools

- Create new tool file in `src/tools/` with Zod schema export
- Import and register in `src/index.ts` main server setup
- Add to destructive/non-destructive filtering logic as appropriate
- Include comprehensive error handling for Kubernetes API failures

### Testing Strategy

- Unit tests focus on tool functionality and schema validation
- Integration tests verify actual Kubernetes operations
- Custom test sequencer ensures kubectl tests run last (they modify cluster state)
- Tests require active Kubernetes cluster connection

### Configuration Handling

- Server loads kubeconfig from multiple sources: KUBECONFIG_YAML env var, KUBECONFIG path, or ~/.kube/config
- Supports multiple kubectl contexts with context switching capabilities
- Environment variables control server behavior (non-destructive mode, custom kubeconfig paths)

## Kubernetes Integration Details

The server requires:

- kubectl installed and accessible in PATH
- Valid kubeconfig with configured contexts
- Active Kubernetes cluster connection
- Helm v3 for chart operations (optional)

**Non-destructive mode** disables: kubectl_delete, uninstall_helm_chart, cleanup operations, and kubectl_generic (which could contain destructive commands).
