# GitHub MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This directory contains a Model Context Protocol (MCP) server designed to interact with the GitHub API. It is based on the official [github/github-mcp-server](https://github.com/github/github-mcp-server) implementation, adapted for use within the KlavisAI project.

This server allows MCP clients to leverage GitHub's API for tasks like retrieving repository contents, managing issues, searching code, and more, using the standardized MCP interface.

## Prerequisites

*   **Docker:** (Recommended for running) Download and install Docker Desktop or Docker Engine.
*   **Go:** Version 1.23 or later (Required for local development/running without Docker).
*   **Git:** Required for cloning and version control.

## Configuration

The server requires a GitHub Personal Access Token (PAT) for authenticated API access.

1.  **Create a `.env` file:** In the `mcp_servers/github` directory, create a file named `.env` by copying the example:
    ```bash
    cp mcp_servers/github/.env.example mcp_servers/github/.env
    ```
2.  **Add your GitHub Token:** Edit the `.env` file and replace `your_github_personal_access_token` with your actual GitHub PAT. Ensure your token has the necessary permissions (e.g., `repo`, `read:user`) for the operations you intend to perform.
    ```dotenv
    # mcp_servers/github/.env
    GITHUB_AUTH_TOKEN=ghp_YourActualGitHubTokenHere
    ```
    *   **Important:** Keep your `.env` file secure and do not commit it to version control. The `.gitignore` file in the project root should already be configured to ignore `.env` files.

3.  **Optional Variables:**
    *   `PORT`: The port the server listens on. Defaults to `5000`.
    *   `BASE_URL`: The base URL exposed by the server. Defaults to `http://localhost:{PORT}`. You generally don't need to change these for local Docker usage.

## Running with Docker (Recommended)

Using Docker provides a containerized and consistent environment.

1.  **Build the Docker Image:** Navigate to the **root** of the `klavis` repository (the directory containing this `mcp_servers` folder) and run the build command:
    ```bash
    docker build -t klavis-github-mcp -f mcp_servers/github/Dockerfile .
    ```
    *   `-t klavis-github-mcp`: Tags the image with the name `klavis-github-mcp`.
    *   `-f mcp_servers/github/Dockerfile`: Specifies the path to the Dockerfile.
    *   `.`: Sets the build context to the current directory (the `klavis` root), allowing the Dockerfile to copy files from `mcp_servers/github/`.

2.  **Run the Docker Container:**
    ```bash
    docker run --rm -p 5000:5000 --env-file mcp_servers/github/.env klavis-github-mcp
    ```
    *   `--rm`: Automatically removes the container when it exits.
    *   `-p 5000:5000`: Maps port 5000 on your host machine to port 5000 inside the container (the default port the server listens on).
    *   `--env-file mcp_servers/github/.env`: Loads environment variables (specifically `GITHUB_AUTH_TOKEN`) from your `.env` file into the container. **Note:** The `.env` file itself is *not* copied into the image.
    *   `klavis-github-mcp`: The name of the image to run.

    The server should now be running and accessible at `http://localhost:5000`.

## Running Locally (Alternative)

If you prefer not to use Docker, you can run the server directly using Go.

1.  **Ensure Prerequisites:** Make sure you have Go 1.23+ installed.
2.  **Navigate to Directory:** Open your terminal in the `mcp_servers/github` directory.
3.  **Configure:** Create and configure the `.env` file as described in the "Configuration" section.
4.  **Install Dependencies:** Download the necessary Go modules:
    ```bash
    go mod download
    ```
5.  **Run the Server:**
    ```bash
    go run server.go
    ```
    The server will load the `GITHUB_AUTH_TOKEN` from the `.env` file in the current directory and start listening on port 5000 (or the port specified in `.env`).

## Usage

Once the server is running (either via Docker or locally), you can interact with it using any MCP-compatible client (like `mcp-cli`). Point your client to the server's address (e.g., `http://localhost:5000`).

If you configured the server using the `GITHUB_AUTH_TOKEN` environment variable (e.g., via `--env-file` in Docker or the `.env` file locally), the server will use this token for all requests.

Alternatively, if the server was started *without* the `GITHUB_AUTH_TOKEN` environment variable set, clients must provide the token via the `x-auth-token` header with each request.