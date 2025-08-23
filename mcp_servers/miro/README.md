# Miro MCP Server

This directory contains a Model Context Protocol (MCP) server for integrating [Miro](https://miro.com/) capabilities into applications like Claude, Cursor, and other LLM clients. It allows leveraging Miro's powerful visual collaboration platform features through a standardized protocol.

## Features

This server exposes **32 comprehensive tools** covering the full Miro API v2 functionality:

### Board Management (5 tools)

- `miro_create_board`: Create new Miro boards with customizable settings, sharing policies, and permissions
- `miro_list_boards`: Get all accessible boards with optional team filtering and pagination
- `miro_get_specific_board`: Retrieve detailed information about specific boards
- `miro_update_board`: Update existing board properties (name, description, sharing/permissions policies)
- `miro_delete_board`: Permanently delete boards

### Board Member Management (3 tools)

- `miro_get_board_members`: List all board members and their current roles
- `miro_update_board_member_role`: Change member permissions (viewer/commenter/editor/coowner/owner)
- `miro_remove_board_member`: Remove users from board access

### Item Management (4 tools)

- `miro_get_board_items`: Get all items from a board with optional type filtering and pagination
- `miro_get_specific_board_item`: Get detailed information about specific board items
- `miro_update_item_position`: Move items and change parent-child relationships
- `miro_delete_board_item`: Remove items from boards

### App Cards (4 tools)

- `miro_add_app_card_item`: Create app card items with status tracking and custom fields
- `miro_get_app_card_item`: Retrieve app card details
- `miro_update_app_card_item`: Update app card properties and status
- `miro_delete_app_card_item`: Remove app cards from boards

### Cards (4 tools)

- `miro_add_card_item`: Add task cards with assignees and due dates
- `miro_get_card_item`: Retrieve card details
- `miro_update_card_item`: Update card properties, assignments, and deadlines
- `miro_delete_card_item`: Remove cards from boards

### Shapes (4 tools)

- `miro_add_shape`: Add geometric shapes (21 types: rectangle, circle, triangle, arrows, flowchart elements, etc.)
- `miro_get_shape`: Retrieve shape details
- `miro_update_shape`: Update shape properties, styling, and content
- `miro_delete_shape`: Remove shapes from boards

### Sticky Notes (4 tools)

- `miro_add_sticky_note`: Add colorful sticky notes with positioning and text alignment
- `miro_get_sticky_note`: Retrieve sticky note details
- `miro_update_sticky_note`: Update sticky note content, color, and positioning
- `miro_delete_sticky_note`: Remove sticky notes from boards

### Text Items (4 tools)

- `miro_add_text_item`: Add formatted text elements with typography controls
- `miro_get_text_item`: Retrieve text item details
- `miro_update_text_item`: Update text content, styling, and positioning
- `miro_delete_text_item`: Remove text items from boards

## Prerequisites

- **Node.js:** Version 18.0.0 or higher
- **npm:** Node Package Manager (usually comes with Node.js)
- **TypeScript:** For development and building
- **Miro Access Token:** Obtainable from your [Miro Developer Console](https://developers.miro.com/)

## Environment Setup

Before running the server, you need to configure your Miro API credentials.

1. Create an environment file:
   cp .env.example .env

**Note:** If `.env.example` doesn't exist, create `.env` directly:
touch .env

2. Edit `.env` and add your Miro access token:

Miro API credentials
MIRO_ACCESS_TOKEN=your-actual-access-token-here

- `MIRO_ACCESS_TOKEN` (Required): Your access token for the Miro API. You can obtain this from your Miro Developer Console by creating an app and generating a Personal Access Token.
- `PORT` (Optional): The port number for the server to listen on. Defaults to 5000.

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

### Using Node.js / npm

1. **Install Dependencies:**
   npm install

2. **Build the Server Code:**
   npm run build

3. **Start the Server:**
   npm start

The server will start using the environment variables defined in `.env` and listen on port 5000 (or the port specified by the `PORT` environment variable).

## API Reference

### Key Tool Examples

#### Board Management

##### `miro_create_board`

Create a new Miro board with comprehensive configuration options.

**Parameters:**

- `name` (string, required): Name of the board (1-60 characters)
- `description` (string, optional): Board description (max 300 characters)
- `access` (string, optional): Sharing policy ("private", "view", "comment", "edit")
- `teamId` (string, optional): Team ID to create the board under
- `projectId` (string, optional): Project ID to associate with

##### `miro_list_boards`

Get all accessible boards with filtering and pagination.

**Parameters:**

- `limit` (number, optional): Maximum number of boards to return (1-100, default: 25)
- `team_id` (string, optional): Filter boards by team ID

#### Content Creation

##### `miro_add_sticky_note`

Add a sticky note to a board with full customization.

**Parameters:**

- `board_id` (string, required): ID of the board
- `content` (string, required): Text content of the sticky note
- `x`, `y` (number, optional): Position coordinates
- `width` (number, optional): Note width in pixels
- `fill_color` (string, optional): Color ("light_yellow", "yellow", "orange", "light_green", "green", "dark_green", "cyan", "light_pink", "pink", "violet", "red", "light_blue", "blue", "dark_blue", "black", "gray")
- `shape` (string, optional): "square" or "rectangle"
- `text_align` (string, optional): "left", "center", "right"
- `parent_id` (string, optional): Parent item ID for grouping

##### `miro_add_shape`

Add geometric shapes with extensive styling options.

**Parameters:**

- `board_id` (string, required): ID of the board
- `shape` (string, optional): Shape type - supports 21 types including "rectangle", "circle", "triangle", "rhombus", "star", "right_arrow", "cloud", etc.
- `content` (string, optional): Text content inside the shape
- `x`, `y` (number, optional): Position coordinates
- `width`, `height` (number, optional): Shape dimensions
- `fill_color` (string, optional): Fill color in HEX format
- `border_color` (string, optional): Border color in HEX format
- `border_width` (number, optional): Border width (1-24)
- `font_size` (number, optional): Text font size (10-288)
- `text_align` (string, optional): Text alignment ("left", "center", "right")

#### Advanced Features

##### `miro_update_item_position`

Move items and manage parent-child relationships.

**Parameters:**

- `board_id` (string, required): ID of the board
- `item_id` (string, required): ID of the item to move
- `x`, `y` (number, optional): New position coordinates
- `parent_id` (string, optional): New parent item ID
- `attach_to_canvas` (boolean, optional): Set to true to attach directly to canvas

## Authentication

The server supports two methods of authentication:

1. **Environment Variable (Recommended):** Set `MIRO_ACCESS_TOKEN` in your `.env` file.
2. **HTTP Header:** Pass the access token as `x-auth-token` header in requests to the MCP server.

Both Bearer token format (`Bearer token123`) and direct token format (`token123`) are supported.

## Protocol Support

This server supports both MCP protocol versions:

- **Streamable HTTP Transport** (Protocol Version 2025-03-26) - **Recommended**
  - Endpoint: `POST /mcp`
  - Single request/response model
  - Simpler implementation and better performance

- **HTTP+SSE Transport** (Protocol Version 2024-11-05) - **Legacy Support**
  - Endpoints: `GET /sse`, `POST /messages`, `DELETE /sse/:sessionId`
  - Persistent connections with session management
  - Server-Sent Events for real-time communication

### Additional Endpoints

- `GET /health` - Health check endpoint
- `GET /sse/status` - SSE connection status and monitoring

## Testing with MCP Clients

### Claude Desktop

Add to your MCP configuration:
{
"mcpServers": {
"miro": {
"command": "node",
"args": ["path/to/your/server/dist/index.js"],
"env": {
"MIRO_ACCESS_TOKEN": "your_actual_token_here"
}
}
}
}

### Cursor IDE

1. Create `.cursor/mcp.json` in your project:
   {
   "mcpServers": {
   "miro": {
   "url": "http://localhost:5000/mcp",
   "headers": {
   "x-auth-token": "your_actual_token_here"
   }
   }
   }
   }

2. Test with natural language:
   - "Create a new Miro board called 'Project Planning'"
   - "Add a sticky note saying 'Important deadline' to board [board-id]"
   - "Create a flowchart with rectangles and arrows on my board"

## Error Handling

The server includes comprehensive error handling:

- **Authentication errors**: Invalid or missing tokens
- **API errors**: Miro API rate limits, invalid parameters
- **Connection errors**: Network issues and timeouts
- **Validation errors**: Invalid input parameters

All errors are returned in proper JSON-RPC format with descriptive error messages.

## Development

- **Building:** `npm run build` (compile TypeScript to JavaScript)
- **Development:** `npm run dev` (if watch mode is configured)
- **Linting:** `npm run lint` (check code style)
- **Testing:** `npm test` (if tests are configured)

## Architecture

The server is built with:

- **Express.js** for HTTP server functionality
- **Model Context Protocol SDK** for MCP implementation
- **AsyncLocalStorage** for request context management
- **TypeScript** for type safety and better development experience

## Support

For issues related to this MCP server, please create an issue in the repository.
For Miro API questions, consult the [Miro API documentation](https://developers.miro.com/reference/).
