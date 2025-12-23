# Vercel MCP Server

This server provides a Model Context Protocol (MCP) interface to interact with Vercel projects, deployments, environment variables, and more. It exposes 17+ tools for safe, programmatic management and inspection of your Vercel account.

---

## Supported Tools

### Project Tools
1. **vercel_list_projects**: List all Vercel projects.
2. **vercel_get_project**: Get details of a specific project.
3. **vercel_create_project**: Create a new Vercel project.
4. **vercel_update_project**: Update project settings (rename, build command, etc).
5. **vercel_delete_project**: Permanently delete a project.

### Deployment Tools
6. **vercel_list_deployments**: List deployments (all or per project).
7. **vercel_get_deployment**: Get details of a specific deployment.
8. **vercel_get_deployment_logs**: View build/runtime logs for a deployment.
9. **vercel_get_deployment_events**: View deployment events and status updates.
10. **vercel_search_deployments**: Search deployments by name or query.
11. **vercel_cancel_deployment**: Cancel a building deployment (safe for non-critical only).

### Domain Tools
12. **vercel_list_domains**: List all configured custom domains.

### Environment Variable Tools
13. **vercel_list_env_vars**: List environment variables for a project.
14. **vercel_create_env_var**: Add a new environment variable (safe for development target).
15. **vercel_update_env_var**: Update an existing environment variable.
16. **vercel_delete_env_var**: Delete an environment variable.

### Team Tools
17. **vercel_list_teams**: List all accessible Vercel teams (if enabled).

---

## Setup Instructions

### 1. Environment Variables

> **Why is `VERCEL_API_TOKEN` required?**
>
> The `VERCEL_API_TOKEN` environment variable is your Vercel API token. The MCP server uses this key to authenticate and make authorized requests to the Vercel API on your behalf. Without it, the server cannot access or manage your Vercel projects, deployments, or environment variables. This is why you must provide it in both Docker and local setups.

Copy `.env.example` to `.env` and fill in your Vercel API token:

```sh
cp .env.example .env
# Edit .env and set VERCEL_API_TOKEN=your-vercel-api-token
```

Example `.env`:
```
PORT=5000
NODE_ENV=production
VERCEL_API_TOKEN=your-vercel-api-token
```

---

### 2. Docker Setup

Build and run the server using Docker from the root repository:

```sh
docker build -t vercel-mcp -f mcp_servers/vercel/Dockerfile mcp_servers/vercel
```

To run the container, you must provide your API token as an environment variable:

```sh
docker run -p 5000:5000 -e PORT=5000 -e NODE_ENV=production -e VERCEL_API_TOKEN=your-vercel-api-token vercel-mcp
```

> **Note:**
> The `-e VERCEL_API_TOKEN=...` flag is required so the server can authenticate with Vercel. Replace `your-vercel-api-token` with your actual Vercel API token.

---

### 3. Local (Non-Docker) Setup

```sh
cd mcp_servers/vercel
npm install
npm run build
npm start
```

---

### 4. MCP Server Integration

To connect your LLM or MCP client, add the following to your `mcp.json`:

```json
{
	"servers": {
		"vercel": {
			"type": "http",
			"url": "http://0.0.0.0:5000/mcp",
			"headers": {
				"x-api-token": "your-vercel-api-key"
			}
		}
	}
}
```

---

## Testing

- All tools can be tested via the MCP interface (see tool list above).
- For safe testing, use development-only environment variables and create/delete test projects as shown in the tool descriptions.
- Both Docker and non-Docker setups are supported and tested.

---

## Safety Notes
- Your main projects are safe if you follow the recommended test flow.
- Destructive operations (delete, update) are only performed on test projects/variables.
- Always use development targets for environment variable tests unless you intend to affect production.

---

## Maintainer
- @Priyanshuthapliyal2005
