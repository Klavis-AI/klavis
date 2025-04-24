# Klavis AI Discord Bot (MCP Client) - Local Development

This document provides instructions for setting up and running the Klavis AI Discord Bot locally for development and testing purposes. This bot acts as a client for the Model Context Protocol (MCP), allowing users to interact with connected MCP servers and utilize their tools through Discord.

**Note:** This README is intended for developers or users who want to run the bot on their own machine. For regular use, please invite the official Klavis AI bot available through [www.klavis.ai](https://www.klavis.ai). The local development version runs with `USE_PRODUCTION_DB=False`, which uses local configuration files and might have different behavior or features compared to the hosted production bot (e.g., user verification is skipped).

## Prerequisites

- **Python:** Version 3.12 or higher.
- **uv:** Version 0.6.14 or higher.
- **Docker:** Recommended for easiest setup and execution. ([Docker Desktop](https://www.docker.com/products/docker-desktop/))
- **Git:** For cloning the repository.
- **Discord Bot Token:** You need to create a Discord application and bot user to get a token. See [Discord Developer Portal](https://discord.com/developers/docs/intro).

## Setup

1.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url> # Replace with the actual URL
    cd klavis/mcp-clients # Navigate to the root directory of the project
    ```

2.  **Environment Variables:**

    - Create a file named `.env` in the root directory of mcp-clients (`klavis/mcp-clients`).
    - Copy the example below and fill in your specific values:

    ```ini
    # .env example
    DISCORD_TOKEN="YOUR_DISCORD_BOT_TOKEN"
    WEBSITE_URL="https://www.klavis.ai" # Or http://localhost:3000 if running web UI locally
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY" # Needed for the default LLM in local mode

    # Optional: Set to true to use production database (NOT recommended for local dev)
    # USE_PRODUCTION_DB=False
    ```

    - Replace `"YOUR_DISCORD_BOT_TOKEN"` with the token obtained from the Discord Developer Portal.
    - Replace `"YOUR_OPENAI_API_KEY"` with your OpenAI API key. Local development mode defaults to using an OpenAI model (`gpt-4o`).
    - `WEBSITE_URL` is used for generating login links (though login is bypassed in local mode). Point it to the production site or your local web UI instance.
    - `USE_PRODUCTION_DB` defaults to `False` if omitted, which is the correct setting for local development.

3.  **Local MCP Servers Configuration:**

    - When running locally (`USE_PRODUCTION_DB=False`), the bot reads the list of MCP server URLs to connect to from `src/mcp_clients/local_mcp_servers.json`.
    - Create this file if it doesn't exist.
    - Add the URLs of the MCP servers you want the local bot to connect to.

    ```json
    // mcp_clients/local_mcp_servers.json example
    {
      "server_urls": [
        "http://localhost:8000/sse"
        // Add other local or remote MCP server SSE endpoints here
      ]
    }
    ```

    - Replace `http://localhost:8000/sse` with the actual URL of your running MCP server(s).

## Running the Bot

You can run the bot using Docker (recommended) or directly with Python in a virtual environment. Make sure you are in the `klavis/mcp-clients` root directory.

### Method 1: Docker (Recommended)

1.  **Build the Docker Image:**

    ```bash
    # Make sure that docker daemon is running before executing the command
    docker build -t klavis-discord-bot -f Dockerfile.discord .
    ```

    _(**Note:** The `.` at the end is important - it specifies the build context as the current directory)_

2.  **Run the Docker Container:**
    This command runs the bot using the environment variables from your `.env` file and mounts your local `local_mcp_servers.json` into the container.

    ```bash
    docker run --rm --env-file .env -v ./src/mcp_clients/local_mcp_servers.json:/app/src/mcp_clients/local_mcp_servers.json klavis-discord-bot
    ```

    - `--rm`: Automatically removes the container when it exits.
    - `--env-file .env`: Loads environment variables from the `.env` file in your current directory (`klavis`).
    - `-v ./src/mcp_clients/local_mcp_servers.json:/app/local_mcp_servers.json`: Mounts your local JSON config into the expected path (`/app/src/mcp_clients/local_mcp_servers.json`) inside the container.

    _(**Note:** If you encounter an error at this step, it may be due to the use of quotes in the `.env` file. Try removing all the quotes and run the command again. For example: change `DISCORD_TOKEN="<token>"` to `DISCORD_TOKEN=<token>`.)_

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
    uv run discord_bot
    ```

## Usage

1.  **Invite the Bot:** Go to your Discord application in the Developer Portal, navigate to the "OAuth2" > "URL Generator" section. Select the `bot` and `application.commands` scopes. Choose necessary permissions (e.g., `Send Messages`, `Read Message History`, `Embed Links`, `Create Public Threads`). Copy the generated URL and use it to invite the bot to your test server.
2.  **Interact:**
    - Mention the bot in a channel: `@YourBotName your query here`
    - Send a Direct Message (DM) to the bot.
    - When first interacting, the bot might send a message about linking your account (using the `WEBSITE_URL`). In local mode (`USE_PRODUCTION_DB=False`), user verification is skipped, so you can proceed to interact with the bot directly.
    - The bot will connect to the MCP servers listed in `local_mcp_servers.json`, process your query using the configured LLM (OpenAI by default locally), and potentially use tools from the connected servers to respond.

## Development Notes

- The bot uses `asyncio` for asynchronous operations.
- Logging is directed to the standard output/console.
- Key libraries include `discord.py` (Discord interaction), `mcp-client` (MCP communication), `python-dotenv` (environment variables), `openai`/`anthropic` (LLM interaction).
- Refer to `discord_bot.py`, `base_bot.py`, and `mcp_client.py` for core logic.
