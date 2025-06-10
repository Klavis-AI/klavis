# Notion MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This server implements the Model Context Protocol (MCP) to provide access to various Notion API functionalities as tools for language models or other MCP clients. It allows interacting with Notion workspaces programmatically through a standardized interface.

## Features

The server exposes the following Notion API functions as MCP tools:

*   `notion_search`: Search for pages and databases in the workspace
*   `notion_create_page`: Create a new page in the workspace
*   `notion_update_page`: Update an existing page
*   `notion_get_page`: Get page content and properties
*   `notion_create_database`: Create a new database
*   `notion_query_database`: Query database entries
*   `notion_create_database_item`: Add new items to a database
*   `notion_update_database_item`: Update database item properties
*   `notion_add_comment`: Add comments to pages

## Prerequisites

Before you begin, ensure you have the following:

*   **Node.js and npm:** Required for local development (check versions with `node -v` and `npm -v`).
*   **Docker:** Required for running the server in a container (Recommended).
*   **Notion Integration Token:** A Notion integration token with the necessary permissions to perform the actions listed in the Features section. You can create a Notion App and obtain an Internal Integration Token from the "Secrets" tab in your Notion integration settings.
*   **Connected Pages/Databases:** Ensure relevant pages and databases are connected to your integration.

## Setup

You can run the server using Docker (recommended) or locally.

### Docker (Recommended)

1.  **Create Environment File:**
    Create a file named `.env` in the `mcp_servers/notion` directory with the following content:
    ```env
    # Required: Your Notion Integration Token
    NOTION_API_KEY=ntn_****
    
    # Optional: Notion API Version
    NOTION_VERSION=2022-06-28
    ```
    Replace `ntn_****` with your actual Notion Integration Token.

2.  **Build Docker Image:**
    Navigate to the root `klavis` directory (one level above `mcp_servers`) in your terminal and run the build command:
    ```bash
    docker build -t notion-mcp-server -f mcp_servers/notion/Dockerfile .
    ```
    *(Make sure the path to the Dockerfile is correct relative to your current directory.)*

3.  **Run Docker Container:**
    Run the container, mapping the server's port (5000) to a port on your host machine (e.g., 5000):
    ```bash
    # Note: The .env file created in step 1 is copied into the image during the build process specified in the Dockerfile.
    docker run -p 5000:5000 --name notion-mcp notion-mcp-server 
    ```
    The server will start and listen on port 5000 inside the container.

### Local Development

1.  **Clone Repository:** (If you haven't already)
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Navigate to Directory:**
    ```bash
    cd mcp_servers/notion
    ```

3.  **Create Environment File:**
    Create a file named `.env` in this directory as described in Step 1 of the Docker setup:
    ```env
    # Required: Your Notion Integration Token
    NOTION_API_KEY=ntn_****
    
    # Optional: Notion API Version
    NOTION_VERSION=2022-06-28
    ```

4.  **Install Dependencies:**
    ```bash
    npm install
    ```

5.  **Build and Run:**
    This command compiles the TypeScript code and starts the server:
    ```bash
    npm run build
    npm start
    ```
    The server will start and listen on `http://localhost:5000`.

## Configuration

*   **`NOTION_API_KEY` (Environment Variable):** This is required for all API calls and must be set in the `.env` file (both for Docker build and local run).
*   **`NOTION_VERSION` (Environment Variable):** Optional. Sets the Notion API version. Defaults to `2022-06-28`.
*   **Notion Integration Token (Request Header):** If `NOTION_API_KEY` is not set, the server expects the Notion Integration Token to be provided in the `x-auth-token` HTTP header for every request made to the `/mcp` or `/messages` endpoint. The server uses this token to authenticate with the Notion API for the requested operation.

## Usage

MCP clients can connect to this server via Server-Sent Events (SSE) and interact with it:

1.  **Establish SSE Connection:** Clients connect to the `/sse` endpoint (e.g., `http://localhost:5000/sse`).
2.  **Send Messages:** Clients send MCP requests (like `call_tool`) as JSON payloads via POST requests to the `/messages?sessionId=<session_id>` endpoint.
3.  **Authentication:** Each POST request to `/messages` **must** include the Notion Integration Token in the `x-auth-token` header.

Refer to the [MCP SDK documentation](https://github.com/modelcontextprotocol) for details on client implementation.

## License

This project is licensed under the MIT License.
