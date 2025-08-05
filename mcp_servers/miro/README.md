# Attio MCP Server

This directory contains a Model Context Protocol (MCP) server for integrating [Attio CRM](https://attio.com/) capabilities into applications like Klavis, Cursor, Claude, and other LLM clients. It allows leveraging Attio's powerful customer relationship management features through a standardized protocol.

## Features

This server exposes the following Attio CRM functionalities as tools:

*   `attio_search_people`: Search for people in your Attio workspace with advanced filtering options (name, email, company, job title, description, location).
*   `attio_search_companies`: Search for companies in your Attio workspace with filtering by name, domain, description, location, and team members.
*   `attio_search_deals`: Search for deals in your Attio workspace with filtering by name, stage, and value range.
*   `attio_search_notes`: Search for notes across all objects in your Attio workspace by content, title, or markdown.
*   `attio_create_note`: Create new notes attached to people, companies, or deals in your Attio workspace.

## Prerequisites

*   **Node.js:** Version 18.0.0 or higher.
*   **npm:** Node Package Manager (usually comes with Node.js).
*   **Docker:** (Recommended) For containerized deployment.
*   **Attio API Key:** Obtainable from your [Attio workspace settings](https://app.attio.com/).

## Environment Setup

Before running the server, you need to configure your Attio API credentials.

1.  Create an environment file:
    ```bash
    cp mcp_servers/attio/.env.example mcp_servers/attio/.env
    ```
    
    **Note:** If `.env.example` doesn't exist, create `.env` directly:
    ```bash
    touch mcp_servers/attio/.env
    ```

2.  Edit `mcp_servers/attio/.env` and add your Attio API key:
    ```dotenv
    # Attio API credentials
    ATTIO_API_KEY=your-actual-api-key-here

    # --- Optional: Server configuration --- 
    # PORT=5000
    # ------
    ```

*   `ATTIO_API_KEY` (Required): Your API key for the Attio service. You can obtain this from your Attio workspace settings under Developers > API keys.
*   `PORT` (Optional): The port number for the server to listen on. Defaults to 5000.

*(Note: When using Docker, the `.env` file should be in the `mcp_servers/attio/` directory and will be used during container runtime.)*

## Running Locally

There are two primary ways to run the server locally:

### 1. Using Docker (Recommended)

This method packages the server and its dependencies into a container.

1.  **Build the Docker Image:**
    *   Navigate to the root directory of the `klavis` project.
    *   Run the build command:
        ```bash
        # Replace 'attio-mcp-server' with your desired tag
        docker build -t attio-mcp-server -f mcp_servers/attio/Dockerfile .
        ```

2.  **Run the Docker Container:**
    ```bash
    # This runs the server on port 5000
    docker run -p 5000:5000 --env-file mcp_servers/attio/.env attio-mcp-server 
    ```
    *   `-p 5000:5000`: Maps port 5000 on your host machine to port 5000 inside the container.
    *   `--env-file mcp_servers/attio/.env`: Passes the environment variables from your `.env` file to the container.

The server will start, and you should see log output indicating it's running, typically listening on `http://localhost:5000`.

### 2. Using Node.js / npm

This method runs the server directly using your local Node.js environment.

1.  **Navigate to the Server Directory:**
    ```bash
    cd mcp_servers/attio
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Build the Server Code:**
    (This compiles the TypeScript code to JavaScript)
    ```bash
    npm run build
    ```

4.  **Start the Server:**
    ```bash
    npm start
    ```

The server will start using the environment variables defined in `mcp_servers/attio/.env` and listen on port 5000 (or the port specified by the `PORT` environment variable, if set).

## API Reference

### Available Tools

#### `attio_search_people`
Search for people in your Attio workspace.

**Parameters:**
- `query` (string, optional): Search query for people (searches across name, email, company, job title, description, location)
- `email` (string, optional): Filter by specific email address
- `limit` (number, optional): Maximum number of results to return (default: 25, max: 50)

#### `attio_search_companies`
Search for companies in your Attio workspace.

**Parameters:**
- `query` (string, optional): Search query for companies (searches across name, domain, description, employees names, employees descriptions, location)
- `domain` (string, optional): Filter by company domain
- `limit` (number, optional): Maximum number of results to return (default: 25, max: 50)

#### `attio_search_deals`
Search for deals in your Attio workspace.

**Parameters:**
- `name` (string, optional): Filter by deal name
- `stage` (string, optional): Filter by deal stage (one of "Lead", "In Progress", "Won 🎉", "Lost")
- `minValue` (number, optional): Minimum deal value
- `maxValue` (number, optional): Maximum deal value
- `limit` (number, optional): Maximum number of results to return (default: 25, max: 50)

#### `attio_search_notes`
Search for notes across all objects in your Attio workspace.

**Parameters:**
- `query` (string, optional): Search query for notes content (searches title, plaintext content, and markdown content). Leave empty to get all notes
- `limit` (number, optional): Maximum number of notes to fetch and search through (default: 50, max: 50)

#### `attio_create_note`
Create a new note for a given record in Attio.

**Parameters:**
- `parent_object` (string, required): The object type to attach the note to ("people", "companies", or "deals")
- `parent_record_id` (string, required): The ID of the record to attach the note to
- `title` (string, required): Title of the note
- `content` (string, required): Content of the note
- `format` (string, optional): Format of the note content ("plaintext" or "markdown", default: "plaintext")

## Authentication

The server supports two methods of authentication:

1. **Environment Variable (Recommended):** Set `ATTIO_API_KEY` in your `.env` file.
2. **HTTP Header:** Pass the API key as `x-auth-token` header in requests to the MCP server.

## Development

*   **Linting:** `npm run lint` (check code style), `npm run lint:fix` (automatically fix issues)
*   **Formatting:** `npm run format` (using Prettier)
*   **Testing:** `npm test` (runs Jest tests)
*   **Building:** `npm run build` (compile TypeScript to JavaScript)

## Protocol Support

This server supports both:
- **Streamable HTTP Transport** (Protocol Version 2025-03-26) - Recommended
- **HTTP+SSE Transport** (Protocol Version 2024-11-05) - Legacy support

The server automatically handles both transport types on different endpoints:
- `/mcp` - Streamable HTTP Transport
- `/sse` and `/messages` - HTTP+SSE Transport

## Contributing

Contributions are welcome! Please follow standard GitHub practices (fork, branch, pull request).

## License

This project is licensed under the MIT License.

## Support

For issues related to this MCP server, please create an issue in the repository.
For Attio API questions, consult the [Attio API documentation](https://developers.attio.com/). 