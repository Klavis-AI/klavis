# WordPress MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is a Model Context Protocol (MCP) server designed to provide access to WordPress sites. It enables Large Language Models (LLMs) and other compatible clients to interact with WordPress sites, allowing them to create, retrieve, and update posts.

## License

This MCP server is licensed under the **MIT License**. You are free to use, modify, and distribute the software under the terms of this license.

## Components

### Tools

*   **`create_post`**
    *   **Description:** Creates a new WordPress post.
    *   **Input:** JSON object containing post details:
        ```json
        {
          "title": "Post Title",
          "content": "Post content in HTML format",
          "status": "draft" // Optional, defaults to "draft"
        }
        ```
    *   **Output:** JSON object containing the created post details.

*   **`get_posts`**
    *   **Description:** Retrieves a list of WordPress posts.
    *   **Input:** JSON object with optional pagination parameters:
        ```json
        {
          "perPage": 10, // Optional, defaults to 10
          "page": 1 // Optional, defaults to 1
        }
        ```
    *   **Output:** JSON array containing post objects.

*   **`update_post`**
    *   **Description:** Updates an existing WordPress post.
    *   **Input:** JSON object containing the post ID and fields to update:
        ```json
        {
          "postId": 123,
          "title": "Updated Title", // Optional
          "content": "Updated content", // Optional
          "status": "publish" // Optional
        }
        ```
    *   **Output:** JSON object containing the updated post details.

### Resources

The server exposes WordPress content types as resources:

*   **WordPress Types:** Provides information about the available content types in the WordPress site.

## Prerequisites

*   **Node.js and npm:** Required for running locally without Docker (v16+ recommended).
*   **Docker:** (Optional, Recommended) For containerized deployment.
*   **WordPress Site:** An accessible WordPress site with REST API enabled.

## Setup

1.  **Clone the Repository:** If you haven't already, clone the main Klavis AI repository.
2.  **Configure Environment Variables:**
    *   This server requires authentication details for your WordPress site.
    *   Navigate to the `mcp_servers/wordpress` directory.
    *   Copy the example environment file: `cp .env.example .env`
    *   Edit the `.env` file and set the WordPress credentials:
        ```env
        # .env
        WORDPRESS_SITE_URL=https://your-wordpress-site.com
        WORDPRESS_USERNAME=your_username
        WORDPRESS_PASSWORD=your_password
        ```
        Replace the values with your actual WordPress site URL and credentials.

## Running the Server

You can run the server using Docker (recommended) or directly with Node.js/npm.

### Using Docker (Recommended)

1.  **Build the Docker Image:**
    *   Navigate to the **root directory** of the Klavis AI repository (the one containing the `mcp_servers` folder).
    *   Run the build command:
        ```bash
        docker build -t klavis-ai/mcp-server-wordpress -f mcp_servers/wordpress/Dockerfile .
        ```
        *   `-t klavis-ai/mcp-server-wordpress`: Tags the image with a descriptive name.
        *   `-f mcp_servers/wordpress/Dockerfile`: Specifies the path to the Dockerfile.
        *   `.`: Specifies the build context (the root directory).

2.  **Run the Docker Container:**
    *   Use the credentials you configured in the `.env` file or pass them directly.
    *   Run the container, exposing port 5000:
        ```bash
        docker run -p 5000:5000 \
          -e WORDPRESS_SITE_URL="https://your-wordpress-site.com" \
          -e WORDPRESS_USERNAME="your_username" \
          -e WORDPRESS_PASSWORD="your_password" \
          --rm klavis-ai/mcp-server-wordpress
        ```
        *   `-p 5000:5000`: Maps port 5000 on your host to port 5000 in the container.
        *   `-e WORDPRESS_*`: Passes the WordPress credentials as environment variables.
        *   `--rm`: Removes the container when it stops.
        *   `klavis-ai/mcp-server-wordpress`: The name of the image you built.

    The server should now be running and accessible at `http://localhost:5000`.

### Using NPM (Manual / Development)

1.  **Navigate to the Server Directory:**
    ```bash
    cd mcp_servers/wordpress
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Ensure `.env` is Configured:** Make sure you have created and configured the `.env` file as described in the Setup section.
4.  **Start the Server:**
    ```bash
    npm start
    ```
    This command first compiles the TypeScript code (`tsc`) and then runs the server (`node dist/index.js`).

    The server should now be running and accessible at `http://localhost:5000`.

## Usage with MCP Clients

Once the server is running, you can connect to it using any MCP-compatible client. The client can then use the WordPress tools to interact with your WordPress site, creating and managing posts through the WordPress REST API.

### Authentication

There are two ways to provide WordPress credentials:

1. **Environment Variables:** Set the `WORDPRESS_SITE_URL`, `WORDPRESS_USERNAME`, and `WORDPRESS_PASSWORD` variables in the environment or `.env` file.

2. **Request Headers:** Pass the credentials in the HTTP headers:
   - `x-wordpress-site-url`: Your WordPress site URL
   - `x-wordpress-username`: Your WordPress username
   - `x-wordpress-password`: Your WordPress password

The server will first check for credentials in the request headers, then fall back to environment variables. 