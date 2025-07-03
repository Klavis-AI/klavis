# Monday.com MCP Server

A Model Context Protocol (MCP) server for integrating with the Monday.com API. This server provides comprehensive tools to manage boards, items, columns, users, and more in Monday.com workspaces.

## Features

- **Board Management**: Create, retrieve, and manage Monday.com boards
- **Item Operations**: Create, update, delete, and move items between groups
- **Column Management**: Create and delete board columns
- **User Management**: Search and retrieve user information
- **Updates & Comments**: Create updates and comments on items
- **Advanced Operations**: Change column values, move items, and manage board schemas

## Prerequisites

- Node.js 18.0.0 or higher
- Monday.com API token (see [Authentication](#authentication))

## Installation

1. Navigate to the Monday.com MCP server directory:

```bash
cd mcp_servers/monday
```

2. Install dependencies:

```bash
npm install
```

3. Build the project:

```bash
npm run build
```

## Configuration

Copy the .env.example file to .env

```bash
cp .env.example .env
```

Set the following environment variable:

- `MONDAY_API_KEY`: Your Monday.com API token

You can obtain your Monday.com API token from your Monday.com account settings under "Developers" → "My Access Tokens".

## Usage

### Starting the Server

```bash
npm start
```

The server will start on port 5000 and supports:

- **Streamable HTTP Transport**: POST `/mcp`
- **Server Sent Events Transport**: `/sse`

### Available Tools

| Category              | Tool Name                        | Description                                                     |
| --------------------- | -------------------------------- | --------------------------------------------------------------- |
| **User Management**   | monday_get_users_by_name         | Retrieve user information by name or partial name               |
| **Board Management**  | monday_get_boards                | Get all Monday.com boards accessible to the authenticated user  |
|                       | monday_create_board              | Create a new Monday.com board with specified configuration      |
|                       | monday_get_board_schema          | Get board schema (columns and groups) by board ID               |
| **Column Management** | monday_create_column             | Create a new column in a Monday.com board                       |
|                       | monday_delete_column             | Delete a column from a Monday.com board                         |
| **Item Management**   | monday_create_item               | Create a new item in a Monday.com board                         |
|                       | monday_get_board_items_by_name   | Get items by name from a Monday.com board                       |
|                       | monday_delete_item               | Delete an item from a Monday.com board                          |
|                       | monday_change_item_column_values | Change the column values of an item in a Monday.com board       |
|                       | monday_move_item_to_group        | Move an item to a different group within a Monday.com board     |
|                       | monday_create_update             | Create a new update (comment) for an item in a Monday.com board |

## Development

### Scripts

- `npm run build`: Build the TypeScript project
- `npm start`: Start the server
- `npm run lint`: Run ESLint
- `npm run lint:fix`: Fix ESLint issues
- `npm run format`: Format code with Prettier
- `npm run prepare`: Build the project (runs automatically on install)

### Project Structure

```
mcp_servers/monday/
├── src/
│   ├── index.ts              # Main server implementation
│   └── tools/
│       ├── base.ts           # API client configuration
│       ├── users.ts          # User management tools
│       ├── boards.ts         # Board management tools
│       ├── columns.ts        # Column management tools
│       ├── items.ts          # Item management tools
│       ├── queries.graphql.ts # GraphQL queries
│       └── index.ts          # Tool exports
├── package.json              # Project configuration
├── tsconfig.json             # TypeScript configuration
├── .eslintrc.json            # ESLint configuration
├── Dockerfile                # Docker configuration
└── README.md                 # This file
```

## Technical Details

- Uses Monday.com SDK
- Built with FastMCP
- Implements Zod schemas for parameter validation
- Supports Monday.com's full feature set including boards, items, columns, and users
- Uses TypeScript for type safety

## Authentication

The server requires a Monday.com API token which can be obtained from:

1. Log into your Monday.com account
2. Go to Avatar (top right) → Admin → API
3. Generate a new API token
4. Set the token as the `MONDAY_API_KEY` environment variable

## License

MIT License
