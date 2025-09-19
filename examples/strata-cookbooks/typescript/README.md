# Strata + LangChain TypeScript Example

This example demonstrates how to use Klavis Strata with LangChain in TypeScript to create an AI agent that can interact with Gmail and YouTube through MCP (Model Context Protocol).

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file with your API keys:
```bash
# Klavis API Key - Get from https://klavis.io
KLAVIS_API_KEY=your_klavis_api_key_here

# OpenAI API Key - Get from https://platform.openai.com
OPENAI_API_KEY=your_openai_api_key_here
```

3. Update the email address in the code:
   - Replace `golden-kpop@example.com` with your actual email address

## Running the Example

```bash
# Development mode (with tsx)
npm run dev

# Or build and run
npm run build
npm start
```

## What This Example Does

1. **Creates a Strata MCP Server**: Sets up a server with Gmail and YouTube integrations
2. **Handles OAuth**: Opens browser windows for OAuth authorization when needed
3. **Creates LangChain Agent**: Sets up an AI agent with access to MCP tools
4. **Executes Task**: Asks the agent to summarize a YouTube video and email the summary

## Note

This is a simplified TypeScript port of the Python example. The full MCP client integration for TypeScript is still evolving, so some functionality may be limited compared to the Python version.
