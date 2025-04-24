# Klavis AI Web Bot (MCP Client) - Local Development

This document provides instructions for setting up and running the Klavis AI Web Bot locally. This bot acts as a FastAPI backend, serving as a client for the Model Context Protocol (MCP) and allowing web frontends to interact with connected MCP servers and utilize their tools.

**Note:** This README is intended for developers setting up the backend service. This backend is typically consumed by a separate web frontend application. The local development version can run with `USE_PRODUCTION_DB=False`, which uses local configuration files and might have different behavior compared to the hosted production service (e.g., user verification and database interactions might be different).

## Prerequisites

*   **Python:** Version 3.12 or higher.
*   **uv:** Version 0.6.14 or higher.
*   **Docker:** Recommended for easiest setup and execution. ([Docker Desktop](https://www.docker.com/products/docker-desktop/))
*   **Git:** For cloning the repository.
*   **Required Python Libraries:** `fastapi`, `uvicorn`, `python-dotenv`, `aiohttp`, `mcp-client`, `openai`, `anthropic` (and others as specified in a requirements file).

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url> # Replace with the actual URL
    cd klavis/mcp-clients # Navigate to the root directory of the project
    ```

2.  **Environment Variables:**
    *   Copy the example environment file if one exists, or create a new file named `.env` in the root directory (`klavis/mcp-clients`).
    *   Ensure the following variables are set:

    ```ini
    # .env example for web_bot
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY" # Needed for the default LLM in local mode

    # Optional: Set to true to use production database (NOT recommended for local dev)
    # USE_PRODUCTION_DB=False 
    ```
    *   Replace `"YOUR_OPENAI_API_KEY"` with your OpenAI API key if using OpenAI models locally.
    *   `USE_PRODUCTION_DB` defaults to `False` if omitted, which is the correct setting for local development using `local_mcp_servers.json`. If set to `True`, ensure database connection variables are also present.

3.  **Local MCP Servers Configuration (if `USE_PRODUCTION_DB=False`):**
    *   When running locally without a production database, the bot reads the list of MCP server URLs to connect to from `src/mcp_clients/local_mcp_servers.json`.
    *   Create this file if it doesn't exist.
    *   Add the URLs of the MCP servers you want the local bot to connect to.

    ```json
    // mcp_clients/local_mcp_servers.json example
    {
      "server_urls": [
        "http://localhost:8000/sse" 
        // Add other local or remote MCP server SSE endpoints here
      ]
    }
    ```
    *   Replace `http://localhost:8000/sse` with the actual URL of your running MCP server(s).

## Running the Web Service

You can run the service using Docker (recommended) or directly with Python in a virtual environment. Make sure you are in the `klavis/mcp-clients` root directory.

### Method 1: Docker (Recommended)

1.  **Build the Docker Image:**
    *(Assuming a Dockerfile exists, e.g., `Dockerfile.web`)*
    ```bash
    # Make sure that docker daemon is running before executing the command
    docker build -t klavis-web-bot -f Dockerfile.web .
    ```
    *(Note: The `.` at the end specifies the build context. Adjust `Dockerfile.web` if the filename differs.)*

2.  **Run the Docker Container:**
    This command runs the bot using the environment variables from your `.env` file and mounts your local `local_mcp_servers.json` if needed.
    ```bash
    # If using local_mcp_servers.json
    docker run --rm -p 8080:8080 --env-file .env -v ./src/mcp_clients/local_mcp_servers.json:/app/src/mcp_clients/local_mcp_servers.json klavis-web-bot

    # If using production DB (no volume mount needed for local_mcp_servers.json)
    # docker run --rm -p 8080:8080 --env-file .env klavis-web-bot 
    ```
    *   `--rm`: Automatically removes the container when it exits.
    *   `-p 8080:8080`: Maps port 8080 on your host to port 8080 in the container.
    *   `--env-file .env`: Loads environment variables from the `.env` file.
    *   `-v ...`: (Optional) Mounts your local JSON config into the container if `USE_PRODUCTION_DB=False`.

### Method 2: Python Virtual Environment

1.  **Create and Activate Virtual Environment:**

    ```bash
    # Make sure to navigate to the root directory of the project (skip if already done)
    cd klavis/mcp-clients
    ```

    ```bash
    # Create environment (only needs to be done once)
    uv venv

    # Activate environment
    # Windows (Command Prompt/PowerShell):
    .venv\Scripts\activate
    # macOS/Linux (bash/zsh):
    source .venv/bin/activate
    ```

2.  **Install Dependencies:**

    ```bash
    uv sync
    ```

3.  **Run the Bot:**
    Ensure your `.env` file exists in the `klavis/mcp-clients` root and `src/mcp_clients/local_mcp_servers.json` is configured.
    ```bash
    uv run web_bot
    ```

## API Endpoints

*   `POST /api/query`: Accepts a JSON payload (`{ "user_id": "...", "query": "...", "conversation_id": "..." }`) and streams responses using Server-Sent Events (SSE).
*   `GET /api/health`: Returns a simple `{"status": "ok"}` for health checks.

## Usage

This service is intended to be used by a web frontend application.

1.  The frontend sends a `POST` request to `/api/query` with the user's ID, query, and optionally a conversation ID.
2.  The backend (`web_bot.py`) processes the query, potentially interacting with MCP servers defined in `local_mcp_servers.json` (if `USE_PRODUCTION_DB=False`) or fetched based on user data (if `USE_PRODUCTION_DB=True`).
3.  Responses, including intermediate thoughts or tool usage and the final answer, are streamed back to the frontend via SSE. The frontend listens to these events to display the response dynamically.
4.  Events have a structure like `data: {"type": "message/special/error/done", "content": "..."}\n\n`.

## Development Notes

*   The service uses FastAPI for the web framework and Uvicorn as the ASGI server.
*   It leverages `asyncio` for asynchronous operations, essential for handling concurrent requests and streaming responses.
*   Logging is directed to the standard output/console.
*   Key libraries include `fastapi`, `uvicorn`, `mcp-client`, `python-dotenv`, `openai`/`anthropic` (for LLM interaction).
*   Core logic can be found in `web_bot.py`, `base_bot.py`, and `mcp_client.py`. 