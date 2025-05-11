# Resend Email Sending MCP Server 💌

This project provides a Model Context Protocol (MCP) server designed to send emails using the [Resend API](https://resend.com/). It allows AI agents like Cursor or Claude Desktop assistants to compose and send emails directly, streamlining your workflow.

This server is derived from the original [resend/mcp-send-email](https://github.com/resend/mcp-send-email) repository and is intended for open-source distribution under the MIT License.

## Features

*   Send plain text and HTML emails via Resend.
*   Schedule emails for future delivery.
*   Add CC and BCC recipients.
*   Configure reply-to addresses.
*   Requires sender email verification through Resend.

## Prerequisites

*   **Resend Account & API Key:** You need a [Resend account](https://resend.com/) and an API key.
*   **Verified Domain/Email:** You must authorize Resend to send emails from your domain or specific email address. Follow the [Resend domain verification guide](https://resend.com/docs/introduction/getting-started/authentication#verify-your-domain).

## Setup and Running

There are two primary ways to run this MCP server: using Docker (recommended) or running it locally with Node.js.

### 1. Using Docker (Recommended)

This method encapsulates the server and its dependencies in a container.

1.  **Build the Docker Image:**
    Open your terminal in the `mcp_servers/resend` directory and run:
    ```bash
    docker build -t resend-mcp-server .
    ```

2.  **Run the Docker Container:**
    Replace `YOUR_RESEND_API_KEY` with your actual Resend API key.
    ```bash
    docker run -d -p 5000:5000 -e RESEND_API_KEY=YOUR_RESEND_API_KEY --name resend-mcp-server resend-mcp
    ```
    *   `-d`: Runs the container in detached mode (in the background).
    *   `-p 5000:5000`: Maps port 5000 on your host machine to port 5000 inside the container (the server listens on port 5000).
    *   `-e RESEND_API_KEY=...`: Passes your Resend API key as an environment variable to the container.
    *   `--name resend-mcp-server`: Assigns a convenient name to the container.
    *   `resend-mcp`: The name of the image you built.

    The server is now running and accessible at `http://localhost:5000`.

### 2. Running Locally with Node.js

This method requires Node.js and npm installed on your system.

1.  **Install Dependencies:**
    Navigate to the `mcp_servers/resend` directory in your terminal:
    ```bash
    cd mcp_servers/resend
    npm install
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Edit the newly created `.env` file and replace the placeholder with your actual Resend API key:
    ```
    RESEND_API_KEY=YOUR_RESEND_API_KEY
    ```

3.  **Build the Server:**
    Compile the TypeScript code to JavaScript:
    ```bash
    npm run build
    ```
    This will create a `build` directory containing the compiled code (e.g., `build/index.js`).

4.  **Run the Server:**
    Start the server:
    ```bash
    node build/index.js
    ```
    The server will start, load the API key from the `.env` file, and listen on port 5000. You should see a message like `server running on port 5000`.

## Connecting to Clients (e.g., Cursor)

Once the server is running (either via Docker or locally), you need to configure your AI client (like Cursor) to use it.

1.  Go to your client's MCP server settings (e.g., in Cursor: Settings -> MCP -> Add new MCP server).
2.  Configure the server connection:
    *   **Name:** Choose a descriptive name (e.g., "Resend Email Sender").
    *   **Type:** Select "http" or "sse" (this server uses SSE - Server-Sent Events).
    *   **URL:** Enter the address where the server is running.
        *   If using Docker or running locally: `http://localhost:5000/sse`
    *   **Authentication:** This server expects the API key via the `RESEND_API_KEY` environment variable (handled by Docker `run -e` or the local `.env` file), *not* typically via MCP client headers. However, consult your specific client's documentation if it offers ways to pass environment variables or if you need to modify the server (`index.ts`) to accept keys via headers (though the environment variable method is generally preferred for security).

3.  **Usage:**
    You can now instruct your AI agent to use the "send-email" tool provided by this server. For example, you could provide email details (to, from, subject, body) and ask the agent to "send this email using the Resend Email Sender". The agent will interact with your running MCP server to send the email via your Resend account.

    **Important Tool Arguments:**
    *   `from`: The *verified* sender email address associated with your Resend account.
    *   `to`: The recipient's email address.
    *   `subject`: The email subject.
    *   `text`: The plain text body of the email.
    *   `html` (optional): The HTML body of the email.
    *   `cc`, `bcc`, `replyTo`, `scheduledAt` (optional): Ask the user before using these.

## Development

To modify or contribute to the server:

1.  Clone the repository.
2.  Navigate to `mcp_servers/resend`.
3.  Install dependencies: `npm install`
4.  Make your changes (primarily in `index.ts`).
5.  Build the code: `npm run build`
6.  Run locally using the Node.js instructions above. 