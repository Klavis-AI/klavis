# Contributor's Guide to Building MCP Servers

Welcome, contributor! This guide provides a concise overview for building new Model Context Protocol (MCP) servers and contributing them to the Klavis AI open-source repository. It's designed for software engineers who are new to AI agents and MCP.

## What is an MCP Server?

An MCP server is a specialized backend that acts as a bridge between a Large Language Model (LLM) and external systems. It exposes a set of "tools" that the LLM can use to interact with the world, such as reading files, searching databases, or calling APIs.

The Model Context Protocol (MCP) is an open standard that unifies how AI models communicate with these tools. This avoids the need for custom, one-off integrations. The model works via a simple client-server architecture: an MCP client (like an AI assistant in your editor) sends a request to an MCP server, which executes a specific tool and returns the result.

## How to Design Good Tools

The effectiveness of an MCP server depends entirely on the design of its tools. The LLM relies on the tool's name and description to understand its purpose and decide when to use it. Your goal is to make this decision as easy and accurate as possible for the model.

*   **Use Natural Language:** Tool names and descriptions should be clear, descriptive, and human-readable. Avoid jargon or cryptic abbreviations. For example, use `search_customer_by_email` instead of `cust_find_eml`.
*   **Write Detailed Descriptions:** The description is your most important documentation. Clearly explain what the tool does, what each parameter is for, and what the tool returns. Mention any important side effects or requirements.
*   **Think Like the LLM:** Ask yourself: "If I only read the name and description, would I know exactly when to use this tool and what to expect?" If the answer is no, refine your description.
*   **Keep Tools Atomic:** Design tools to perform one specific job well. Instead of a single `manage_files` tool, create smaller, more focused tools like `read_file`, `write_to_file`, and `list_directory_contents`.

## Getting Started with Development

You can build an MCP server in any language that can serve an HTTP endpoint or communicate over standard I/O. The official MCP provides SDKs, including [Python](https://github.com/modelcontextprotocol/python-sdk) and [TypeScript](https://github.com/modelcontextprotocol/typescript-sdk) that make development much easier.

## Important Resources for MCP Development

When starting with MCP development, it's essential to understand the architecture and operational modes of MCP. Here are some key resources:

- **MCP Architecture Overview:** Provides a comprehensive understanding of the MCP client-server architecture, including the roles of MCP hosts, clients, and servers. It explains the data and transport layers, which are crucial for effective communication and context exchange. [Model Context Protocol Architecture](https://modelcontextprotocol.io/docs/learn/architecture).

- **MCP Server Specification:** Details the operational modes of MCP, including local and remote server configurations, and the supported content protocols such as images, text, audio, and binary data. Understanding these specifications is vital for implementing robust MCP servers. [MCP Server Specification](https://modelcontextprotocol.io/specification/2025-06-18/server).

These documents will help you grasp the foundational concepts and ensure your MCP server implementations are aligned with the protocol standards.

## Example

You can check the [mcp_server](/mcp_servers/) folder for a list of examples. E.g. [attio](/mcp_servers/attio/) is written is Typescript and [airtable](/mcp_servers/airtable/) is written in Python.

## How to Test Your Server

Testing is a critical part of the contribution process. Your testing must demonstrate that your tools not only work but are also correctly understood and utilized by an AI client.

### Step 1: Connect to a Client

First, run your local MCP server and connect it to a client application. Common clients that supports local MCP servers include:

*   **Claude Desktop:** An official desktop application that provides a chat interface for interacting with your server's tools. [Detailed documentations](https://support.anthropic.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop) are available.
*   **Cursor:** An AI-first code editor that can be configured to connect to custom MCP servers. [Detailed documentations (click the remote server tab)](https://docs.cursor.com/en/context/mcp#using-mcp-json) are available.
*   **Visual Studio Code:** Using specific extensions, you can configure VS Code to act as an MCP client. [Detailed documentations](https://code.visualstudio.com/docs/copilot/chat/mcp-servers#_add-an-mcp-server) are available.
*   **Streamable HTTP Client:** For low-level testing, the [steamable_http_client.py](/mcp-clients/src/mcp_clients/streamable_http_client.py) in the Klavis repository is also good for sending raw requests to your server and inspecting its direct responses.

### Step 2: Test with Natural Language and Document It

For every tool you add, you must perform an end-to-end test and document the result.

1.  **Formulate a Test Query:** Devise a natural language prompt or question that should cause an AI agent to use your specific tool. For the `read_file`, a good query would be: *"Please read the file at 'docs/readme.md' and summarize it for me."*
2.  **Execute and Verify:** Run this query in your client application (like Claude Desktop or Cursor). Confirm that the client correctly identifies and calls your tool with the right parameters, and that the tool returns the expected output.
3.  **Record Proof of Correctness:** You are required to document this successful test. **You must record a short video or capture multiple screenshots** that clearly show:
    *   The natural language query you used.
    *   The log output showing your tool being called correctly.
    *   The final, correct result being displayed to the user.

This recording is mandatory. It provides clear, undeniable proof of functionality for reviewers and serves as living documentation for your contribution.

## Guidelines for Function Documentation

For each function you implement, ensure to provide the following details:

- **AI Prompt Words:** Clearly define the prompt words that the AI should use to invoke the function.
- **Title:** Provide a concise and descriptive title for the function.
- **Parameter Usage:** Explain how each parameter should be used, including whether they are optional and their default values.

These guidelines will help ensure that your functions are easily understood and correctly utilized by AI clients.