# Miro MCP Server

This directory contains a Model Context Protocol (MCP) server for integrating [Miro](https://miro.com/) capabilities into applications like Klavis, Cursor, Claude, and other LLM clients. It allows leveraging Miro's powerful visual collaboration platform features through a standardized protocol.

## Features

This server exposes the following Miro functionalities as tools:

### Board Management
* `miro_create_board`: Create new Miro boards with customizable settings
* `miro_update_board`: Update existing board properties (name, description, sharing policy)
* `miro_delete_board`: Permanently delete boards
* `miro_list_boards`: Get all accessible boards with optional team filtering
* `miro_get_board_details`: Retrieve detailed information about specific boards
* `miro_export_board`: Export boards in PDF, PNG, or JPEG formats

### Content Management
* `miro_get_board_items`: Get all items from a board with optional type filtering
* `miro_get_board_item`: Get detailed information about specific board items
* `miro_create_board_item`: Create generic board items with flexible content
* `miro_update_board_item`: Update existing board item properties
* `miro_add_sticky_note`: Add colorful sticky notes with positioning
* `miro_add_shape`: Add various geometric shapes (rectangles, circles, arrows, etc.)
* `miro_add_text_item`: Add formatted text elements
* `miro_create_connector`: Create connectors between board items with styling options
* `miro_delete_board_item`: Remove items from boards

### Collaboration
* `miro_invite_collaborator`: Invite users to boards with role management
* `miro_get_board_members`: List all board members and their roles
* `miro_update_board_member_role`: Change member permissions (viewer/commenter/editor)
* `miro_remove_board_member`: Remove users from board access
* `miro_create_comment`: Add comments to board items
* `miro_get_comments`: Retrieve comments from board items

### Integrations
* `miro_create_webhook`: Set up webhook notifications for board events
* `miro_get_webhooks`: List all webhooks configured for a board
* `miro_delete_webhook`: Remove webhook integrations

### Team Management
* `miro_get_teams`: List all accessible teams
* `miro_get_team_members`: Get members of specific teams

## Prerequisites

* **Node.js:** Version 18.0.0 or higher
* **npm:** Node Package Manager (usually comes with Node.js)
* **Docker:** (Recommended) For containerized deployment
* **Miro Access Token:** Obtainable from your [Miro Developer Console](https://developers.miro.com/)

## Environment Setup

Before running the server, you need to configure your Miro API credentials.

1. Create an environment file:
cp mcp_servers/miro/.env.example mcp_servers/miro/.env

**Note:** If `.env.example` doesn't exist, create `.env` directly:
touch mcp_servers/miro/.env

2. Edit `mcp_servers/miro/.env` and add your Miro access token:

Miro API credentials
MIRO_ACCESS_TOKEN=your-actual-access-token-here


* `MIRO_ACCESS_TOKEN` (Required): Your access token for the Miro API. You can obtain this from your Miro Developer Console by creating an app and generating a Personal Access Token (for development) or implementing OAuth 2.0 flow (for production).
* `PORT` (Optional): The port number for the server to listen on. Defaults to 5000.

*(Note: When using Docker, the `.env` file should be in the `mcp_servers/miro/` directory and will be used during container runtime.)*

## Getting Your Miro Access Token

### For Development (Personal Access Token):
1. Visit the [Miro Developer Console](https://developers.miro.com/)
2. Sign in with your Miro account
3. Create a new app or select an existing one
4. Generate a Personal Access Token
5. Copy the token and use it as your `MIRO_ACCESS_TOKEN`

### For Production (OAuth 2.0):
1. Register your application in the Miro Developer Console
2. Configure redirect URIs and required scopes
3. Implement OAuth 2.0 authorization code flow
4. Exchange authorization codes for access tokens

## Running Locally

There are two primary ways to run the server locally:

### 1. Using Docker (Recommended)

This method packages the server and its dependencies into a container.

1. **Build the Docker Image:**
* Navigate to the root directory of the `klavis` project.
* Run the build command:
  ```
  # Replace 'miro-mcp-server' with your desired tag
  docker build -t miro-mcp-server -f mcp_servers/miro/Dockerfile .
  ```

2. **Run the Docker Container:**
This runs the server on port 5000
docker run -p 5000:5000 --env-file mcp_servers/miro/.env miro-mcp-server

* `-p 5000:5000`: Maps port 5000 on your host machine to port 5000 inside the container.
* `--env-file mcp_servers/miro/.env`: Passes the environment variables from your `.env` file to the container.

The server will start, and you should see log output indicating it's running, typically listening on `http://localhost:5000`.

### 2. Using Node.js / npm

This method runs the server directly using your local Node.js environment.

1. **Navigate to the Server Directory:**

cd mcp_servers/miro


2. **Install Dependencies:**
npm install


3. **Build the Server Code:**
(This compiles the TypeScript code to JavaScript)
npm run build


4. **Start the Server:**
npm start


The server will start using the environment variables defined in `mcp_servers/miro/.env` and listen on port 5000 (or the port specified by the `PORT` environment variable, if set).

## API Reference

### Available Tools

#### Board Management Tools

##### `miro_create_board`
Create a new Miro board.

**Parameters:**
- `name` (string, required): Name of the board
- `description` (string, optional): Board description
- `policy` (string, optional): Sharing policy ("private", "view", "comment", "edit", default: "private")
- `teamId` (string, optional): Team ID to create the board under

##### `miro_list_boards`
Get all accessible boards.

**Parameters:**
- `limit` (number, optional): Maximum number of boards to return (default: 25, max: 100)
- `teamId` (string, optional): Filter boards by team ID

##### `miro_get_board_details`
Get detailed information about a specific board.

**Parameters:**
- `board_id` (string, required): ID of the board

#### Content Management Tools

##### `miro_add_sticky_note`
Add a sticky note to a board.

**Parameters:**
- `board_id` (string, required): ID of the board
- `content` (string, required): Text content of the sticky note
- `x` (number, optional): X coordinate (default: 0)
- `y` (number, optional): Y coordinate (default: 0)
- `color` (string, optional): Color ("yellow", "green", "blue", "red", "gray", "orange", "purple", "pink", default: "yellow")

##### `miro_add_shape`
Add a shape to a board.

**Parameters:**
- `board_id` (string, required): ID of the board
- `shape` (string, required): Shape type ("rectangle", "circle", "triangle", "arrow", etc.)
- `content` (string, optional): Text content inside the shape
- `x`, `y` (number, optional): Position coordinates
- `width`, `height` (number, optional): Shape dimensions
- `color` (string, optional): Fill color in HEX format

##### `miro_add_text_item`
Add formatted text to a board.

**Parameters:**
- `board_id` (string, required): ID of the board
- `content` (string, required): Text content
- `x`, `y` (number, optional): Position coordinates
- `fontSize` (number, optional): Font size in pixels (default: 14)
- `color` (string, optional): Text color in HEX format

##### `miro_create_connector`
Create a connector between two board items.

**Parameters:**
- `board_id` (string, required): ID of the board
- `start_item_id` (string, required): ID of the starting item
- `end_item_id` (string, required): ID of the ending item
- `shape` (string, optional): Connector shape ("straight", "elbowed", "curved", default: "curved")
- `style` (string, optional): Line style ("normal", "dashed", "dotted")
- `strokeColor` (string, optional): Line color in HEX format

#### Collaboration Tools

##### `miro_invite_collaborator`
Invite users to collaborate on a board.

**Parameters:**
- `board_id` (string, required): ID of the board
- `emails` (array, required): Array of email addresses to invite
- `role` (string, optional): Access level ("viewer", "commenter", "editor", default: "editor")
- `message` (string, optional): Personal invitation message

## Authentication

The server supports two methods of authentication:

1. **Environment Variable (Recommended):** Set `MIRO_ACCESS_TOKEN` in your `.env` file.
2. **HTTP Header:** Pass the access token as `x-auth-token` header in requests to the MCP server.

## Development

* **Linting:** `npm run lint` (check code style), `npm run lint:fix` (automatically fix issues)
* **Formatting:** `npm run format` (using Prettier)
* **Testing:** `npm test` (runs Jest tests)
* **Building:** `npm run build` (compile TypeScript to JavaScript)

## Protocol Support

This server supports both:
- **Streamable HTTP Transport** (Protocol Version 2025-03-26) - Recommended
- **HTTP+SSE Transport** (Protocol Version 2024-11-05) - Legacy support

The server automatically handles both transport types on different endpoints:
- `/mcp` - Streamable HTTP Transport
- `/sse` and `/messages` - HTTP+SSE Transport

## Testing with MCP Clients

### Cursor IDE
1. Create `.cursor/mcp.json` in your project:
{
"mcpServers": {
"miro": {
"url": "http://localhost:5000/sse",
"env": {
"MIRO_ACCESS_TOKEN": "your_actual_token_here"
}
}
}
}


2. Enable the server in Cursor settings
3. Test with natural language: "Create a new Miro board called 'Project Planning'"

### Claude Desktop
Configure your MCP server in Claude Desktop's settings to connect via the SSE endpoint.


## Support

For issues related to this MCP server, please create an issue in the repository.
For Miro API questions, consult the [Miro API documentation](https://developers.miro.com/reference/).