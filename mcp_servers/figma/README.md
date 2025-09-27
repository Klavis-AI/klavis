# Figma MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Figma API](https://img.shields.io/badge/Figma_API-REST-FF7262.svg)](https://www.figma.com/developers/api)

## 📖 Overview

Figma MCP Server is a Model Context Protocol (MCP) implementation that bridges language models and other applications with Figma's REST API. It provides a standardized interface for executing design operations through various tools defined by the MCP standard.

## 🚀 Features

This server provides comprehensive design workflow capabilities through MCP tools:

### Authentication & Account Management
| Tool | Description |
|------|-------------|
| `figma_test_connection` | Test API connection and verify authentication |
| `figma_get_current_user` | Get authenticated user information and profile |

### File Management
| Tool | Description |
|------|-------------|
| `figma_get_file` | Get complete file content including document structure |
| `figma_get_file_nodes` | Get specific nodes from a file |
| `figma_get_file_images` | Export images from file nodes in various formats |
| `figma_get_file_versions` | Get file version history and metadata |

### Project Management (⚠️ Limited)
| Tool | Description |
|------|-------------|
| `figma_get_team_projects` | Get projects for a team (requires team ID) |
| `figma_get_project_files` | Get files in a project (requires project ID) |

### Comment Management
| Tool | Description |
|------|-------------|
| `figma_get_file_comments` | Get comments from a file |
| `figma_post_file_comment` | Add comments to files and nodes |
| `figma_delete_comment` | Remove comments from files |

### Variables (Design Tokens)
| Tool | Description |
|------|-------------|
| `figma_get_local_variables` | Get local variables from a file |
| `figma_get_published_variables` | Get published variables (design tokens) |
| `figma_post_variables` | Create or update variables and collections |

### Dev Resources
| Tool | Description |
|------|-------------|
| `figma_get_dev_resources` | Get dev resources attached to file nodes |
| `figma_post_dev_resources` | Create new dev resources |
| `figma_put_dev_resource` | Update existing dev resources |
| `figma_delete_dev_resource` | Remove dev resources |

### Webhooks
| Tool | Description |
|------|-------------|
| `figma_get_team_webhooks` | Get webhooks for a team (requires team ID) |
| `figma_post_webhook` | Create webhooks for team events |
| `figma_put_webhook` | Update webhook configurations |
| `figma_delete_webhook` | Remove webhooks |

### Library Analytics
| Tool | Description |
|------|-------------|
| `figma_get_library_analytics` | Get usage analytics for published libraries |

## ⚠️ Important Limitations

**Please read this carefully before using the Figma MCP Server:**

### Major API Limitations
1. **No Team/Project Discovery**: The Figma API does not provide endpoints to list teams or projects that a user has access to
2. **Manual ID Collection Required**: Users must manually provide:
   - **Team IDs** (from team URLs: `https://www.figma.com/files/team/{team_id}/`)
   - **Project IDs** (from project pages)
   - **File Keys** (from file URLs: `https://www.figma.com/file/{file_key}/filename`)

### Workarounds
- **File Keys**: Extract from Figma URLs: `https://www.figma.com/file/ABC123DEF456/My-Design` → file_key is `ABC123DEF456`
- **Team IDs**: Found in team URLs: `https://www.figma.com/files/team/123456789/` → team_id is `123456789`
- **Project IDs**: Available through the team projects endpoint once you have a team ID

## 📧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip

## ⚙️ Setup & Configuration

### Figma API Key Setup

1. **Log into your Figma account**:
   - Navigate to [Figma Settings](https://www.figma.com/settings)
   - Go to "Account" tab

2. **Generate a Personal Access Token**:
   - Scroll down to "Personal access tokens"
   - Click "Create new token"
   - Give your token a descriptive name (e.g., "MCP Server Integration")
   - Select appropriate scopes (see below)
   - Click "Create token"
   - **Important**: Copy the generated token immediately and store it securely
   - You won't be able to see the full token again after this step

3. **Required Scopes**:
   For full functionality, your token should have these scopes:
   - `files:read` - Read file content
   - `file_variables:read` - Read variables
   - `file_variables:write` - Write variables  
   - `file_dev_resources:read` - Read dev resources
   - `file_dev_resources:write` - Write dev resources
   - `file_comments:read` - Read comments
   - `file_comments:write` - Write comments
   - `library_analytics:read` - Read library analytics
   - `webhooks:write` - Manage webhooks

### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your Figma credentials:
   ```
   FIGMA_API_KEY=your_actual_figma_personal_access_token_here
   FIGMA_MCP_SERVER_PORT=5002
   ```

   **Important**: Replace `your_actual_figma_personal_access_token_here` with your actual token from step 2 above.

## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t figma-mcp-server -f mcp_servers/figma/Dockerfile .

# Run the container
docker run -d -p 5002:5002 --name figma-mcp figma-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5002:5002 --env-file mcp_servers/figma/.env --name figma-mcp figma-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the Figma server directory
cd mcp_servers/figma

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5002`.

## 🔌 API Usage

The server implements the Model Context Protocol (MCP) standard. Here's an example of how to call a tool:

```python
import httpx

async def call_figma_tool():
    url = "http://localhost:5002/mcp"
    payload = {
        "tool_name": "figma_get_file",
        "tool_args": {
            "file_key": "ABC123DEF456",
            "depth": 1
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Testing Connection

```python
payload = {
    "tool_name": "figma_test_connection",
    "tool_args": {}
}
```

### Getting File Content

```python
payload = {
    "tool_name": "figma_get_file",
    "tool_args": {
        "file_key": "ABC123DEF456",  # Extract from Figma URL
        "depth": 2,
        "geometry": "paths"
    }
}
```

### Exporting Images

```python
payload = {
    "tool_name": "figma_get_file_images",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "ids": "123:456,789:012",  # Node IDs from the file
        "format": "png",
        "scale": 2
    }
}
```

### Getting Team Projects (Requires Team ID)

```python
payload = {
    "tool_name": "figma_get_team_projects",
    "tool_args": {
        "team_id": "123456789"  # From team URL
    }
}
```

### Working with Comments

```python
# Get comments
get_comments_payload = {
    "tool_name": "figma_get_file_comments",
    "tool_args": {
        "file_key": "ABC123DEF456"
    }
}

# Add a comment
post_comment_payload = {
    "tool_name": "figma_post_file_comment",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "message": "This needs to be updated",
        "client_meta": {
            "x": 100,
            "y": 200,
            "node_id": "123:456"
        }
    }
}
```

### Working with Variables (Design Tokens)

```python
# Get published variables
get_vars_payload = {
    "tool_name": "figma_get_published_variables",
    "tool_args": {
        "file_key": "ABC123DEF456"
    }
}

# Create/update variables
post_vars_payload = {
    "tool_name": "figma_post_variables",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "variableCollections": [
            {
                "action": "CREATE",
                "name": "Colors",
                "modes": [{"name": "Light"}, {"name": "Dark"}]
            }
        ],
        "variables": [
            {
                "action": "CREATE",
                "name": "Primary Color",
                "variableCollectionId": "collection_id",
                "resolvedType": "COLOR"
            }
        ]
    }
}
```

## 🛠️ Troubleshooting

### Common Issues

- **Authentication Failures**: 
  - Verify your Personal Access Token is correct and hasn't expired
  - Ensure your token has the required scopes for the operations you're trying to perform
  - Check that your token hasn't been revoked in Figma settings

- **Missing Team/Project IDs**: 
  - Extract team IDs from Figma team URLs manually
  - Use the `figma_get_team_projects` endpoint to discover project IDs
  - File keys can be found in any Figma file URL

- **File Access Errors**: 
  - Ensure you have proper permissions to access the file/team/project
  - Some operations require edit permissions, not just view permissions
  - Files in private teams may not be accessible with personal access tokens

- **Rate Limiting**: 
  - Figma enforces rate limits based on your plan and authentication method
  - Personal access tokens have per-user limits
  - OAuth applications have global application limits
  - Implement appropriate delays between requests if hitting limits

- **Node ID Issues**: 
  - Node IDs change when files are modified
  - Use the file structure from `figma_get_file` to find current node IDs
  - Node IDs are strings like "123:456" not just numbers

### Docker Build Issues

- **File Not Found Errors**: If you see errors during Docker build, make sure you're building from the root project directory (`klavis/`), not from the server directory.

### Finding Required IDs

**To find File Keys:**
```
Figma URL: https://www.figma.com/file/ABC123DEF456/My-Design-File
File Key: ABC123DEF456
```

**To find Team IDs:**
```
Team URL: https://www.figma.com/files/team/123456789/Team-Name
Team ID: 123456789
```

**To find Node IDs:**
1. Use `figma_get_file` to get the file structure
2. Navigate through the document tree to find specific nodes
3. Each node has an `id` field that you can use for other operations

## 📊 API Limits and Best Practices

### Rate Limits
- **Personal Access Tokens**: Per-user limits (varies by plan)
- **OAuth Applications**: Global application limits
- **Enterprise Plans**: Higher limits available

### Best Practices
- **Cache File Data**: File content doesn't change frequently, cache when possible
- **Use Specific Node IDs**: Instead of getting entire files, request specific nodes when possible
- **Batch Operations**: Group related operations to minimize API calls
- **Error Handling**: Always implement proper error handling for API calls
- **Respect Rate Limits**: Monitor response headers for rate limit information

## 🔄 Figma API Workflow Examples

### Complete Design Handoff Workflow

```python
# 1. Get file structure
file_structure = {
    "tool_name": "figma_get_file",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "depth": 2
    }
}

# 2. Export design assets
export_assets = {
    "tool_name": "figma_get_file_images",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "ids": "123:456,789:012",
        "format": "png",
        "scale": 2
    }
}

# 3. Get design tokens
design_tokens = {
    "tool_name": "figma_get_published_variables",
    "tool_args": {
        "file_key": "ABC123DEF456"
    }
}

# 4. Add dev resources
dev_resources = {
    "tool_name": "figma_post_dev_resources",
    "tool_args": {
        "file_key": "ABC123DEF456",
        "dev_resources": [
            {
                "name": "Component Documentation",
                "url": "https://storybook.example.com/component",
                "node_id": "123:456"
            }
        ]
    }
}
```

### Library Management Workflow

```python
# 1. Get library analytics
analytics = {
    "tool_name": "figma_get_library_analytics",
    "tool_args": {
        "file_key": "LIBRARY_FILE_KEY"
    }
}

# 2. Update variables based on usage
update_vars = {
    "tool_name": "figma_post_variables",
    "tool_args": {
        "file_key": "LIBRARY_FILE_KEY",
        "variableCollections": [...],
        "variables": [...]
    }
}

# 3. Set up webhook for library updates
webhook = {
    "tool_name": "figma_post_webhook",
    "tool_args": {
        "team_id": "123456789",
        "event_type": "LIBRARY_PUBLISH",
        "endpoint": "https://your-app.com/figma-webhook",
        "description": "Library update notifications"
    }
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Links

- [Figma REST API Documentation](https://www.figma.com/developers/api)
- [Figma OpenAPI Specification](https://github.com/figma/rest-api-spec)
- [Model Context Protocol (MCP) Specification](https://github.com/modelcontextprotocol/specification)
- [Figma Developer Portal](https://www.figma.com/developers/)
- [Figma API Quick Start Guide](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)

## 🎯 Use Cases

This MCP server is perfect for:

- **Design System Management**: Sync design tokens and components across tools
- **Automated Design Handoffs**: Export assets and specifications programmatically  
- **Design Workflow Integration**: Connect Figma to project management and development tools
- **Library Analytics**: Track usage of design system components
- **Comment Management**: Automate design review processes
- **Webhook Integration**: React to file changes and library updates in real-time
- **Dev Resource Management**: Link design components to documentation and code

## 💡 Tips for Success

1. **Start Small**: Begin with simple file reading operations before moving to complex workflows
2. **Understand the Hierarchy**: Learn Figma's node structure (Document → Page → Frame → Layer)
3. **Use Figma URLs**: Extract file keys and team IDs directly from Figma URLs
4. **Monitor Rate Limits**: Keep track of your API usage to avoid hitting limits
5. **Cache Strategically**: Cache file data and node structures that don't change frequently
6. **Handle Errors Gracefully**: Figma API errors can be informative - read the error messages
7. **Test with Simple Files**: Use simple test files to understand the API before working with complex designs