# OpenAI Function Calling with Klavis - TypeScript Example

This example demonstrates how to use OpenAI's function calling feature with the Klavis API in a TypeScript environment. The application is a simple command-line chat interface that connects to Klavis to access external tools.

## Prerequisites

- Node.js (v18 or higher)
- An OpenAI API key
- A Klavis API key

## Setup and Installation

1.  **Clone the repository and navigate to this directory:**
    ```bash
    cd examples/openai-example/typescript
    ```

2.  **Install the dependencies:**
    ```bash
    npm install
    ```

3.  **Set up your environment variables:**

    Create a file named `.env` in this directory (`examples/openai-example/typescript`) and add your API keys:

    ```
    OPENAI_API_KEY=your_openai_api_key_here
    KLAVIS_API_KEY=your_klavis_api_key_here
    ```
    
    Replace `your_openai_api_key_here` and `your_klavis_api_key_here` with your actual API keys.

## Running the Application

Once you have installed the dependencies and set up your `.env` file, you can run the application with the following command:

```bash
npm start
```

This will start the interactive chat assistant in your terminal. When you first run it, a browser window should open for OAuth authentication with the specified service (e.g., Close.com).

## How it Works

The application does the following:
1.  Initializes the OpenAI and Klavis API clients.
2.  Creates a new MCP (Managed Connection Proxy) instance via the Klavis API. For this example, it's configured to use the "Close" CRM connector.
3.  Opens a browser window to handle the OAuth flow for the connector.
4.  Starts a chat loop in the terminal.
5.  When you send a message, it fetches the list of available tools from the Klavis MCP instance.
6.  It sends your message, the conversation history, and the tool definitions to the OpenAI API.
7.  If OpenAI determines that a function (tool) should be called, the application:
    a. Receives the function call request from the API.
    b. Executes the corresponding tool using the Klavis API.
    c. Sends the tool's result back to the OpenAI API.
    d. Streams and prints the final response from the assistant.
8.  If no function call is needed, it streams and prints the assistant's response directly. 