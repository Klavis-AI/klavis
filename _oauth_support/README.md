# OAuth Support Layer for MCP Servers

This directory provides OAuth authentication support for MCP servers that require external service authentication.

## How it Works

### 1. Wrapper Architecture
- **Base Image**: Original MCP server container (e.g., `github-mcp-server`)
- **OAuth Wrapper**: Adds OAuth authentication layer on top of base image
- **Transparent Proxy**: OAuth layer handles authentication, then transparently starts the original MCP server

### 2. Components

#### `docker/Dockerfile.template`
- Builds OAuth wrapper image based on base image
- Installs authentication scripts and dependencies
- Replaces container entry point

#### `docker/entrypoint_wrapper.sh`
- Container startup entry point
- Parses command line arguments (server name and original command)
- Calls OAuth authentication script
- Executes original MCP server command

#### `oauth_acquire.sh`
- Core OAuth authentication logic
- Calls Klavis API to create authentication instance
- Shows authentication URL to user
- Polls and waits for user to complete authentication
- Sets `AUTH_DATA` environment variable

#### `server_name.json`
- Maps internal server names to display names
- Used by GitHub Actions to determine which servers need OAuth
- Example: `"github": "GitHub"`

### 3. Authentication Flow

```
1. Container starts → entrypoint_wrapper.sh
2. Calls oauth_acquire.sh
3. Requests Klavis API to create OAuth instance
4. Displays authentication URL 🔗🔗🔗
5. User completes authentication in browser
6. Polls to check authentication status
7. Gets AUTH_DATA and sets environment variable
8. Starts original MCP server (with auth info)
```

### 4. GitHub Actions Integration

#### Build Process:
1. **Build Base Image** - Original MCP server
2. **Check OAuth Requirements** - Query `server_name.json`
3. **Extract Container Commands** - Use `podman inspect` to get original entry point
4. **Build OAuth Image** - If OAuth needed, build wrapper version
5. **Push Images** - Push `*-mcp-server:*-oauth` image

#### Conditional Building:
- Only servers listed in `server_name.json` get OAuth versions built
- Uses server display name as OAuth service name

### 5. Environment Variables

- `KLAVIS_API_KEY`: Klavis API key (required)
- `AUTH_DATA`: OAuth authentication data (set by script, used by MCP server)

### 6. Usage

```bash
# Run OAuth version of GitHub MCP server
docker run -it -e KLAVIS_API_KEY=your_key_here \
  ghcr.io/klavis-ai/github-mcp-server:latest-oauth
```

Users will see the authentication URL, and after completing authentication, the MCP server will start automatically with GitHub API access.