"""
This is a simple MCP client that uses streamable HTTP to connect to an MCP server.
It is useful for simple testing of MCP servers.

To run the client, use the following command:
```
python streamable_http_client.py <url> <args>
```
"""

import argparse
import logging
from contextlib import AsyncExitStack
from functools import partial
from typing import Optional

import anyio
import sys
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from anthropic import Anthropic

load_dotenv()  # load environment variables from .env

if not sys.warnoptions:
    import warnings

    warnings.simplefilter("ignore")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("client")


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                messages.append({
                    "role": "assistant",
                    "content": [{
                        "type": "tool_use",
                        "name": tool_name,
                        "input": tool_args,
                        "id": content.id
                    }]
                })
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": str(result.content[0].text)
                    }]
                })
                final_text.append(f"[Tool call result: {result.content[0].text}]")

                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def run_session(read_stream, write_stream):
    client = MCPClient()
    async with ClientSession(read_stream, write_stream) as session:
        client.session = session

        logger.info("Initializing session")
        await session.initialize()
        logger.info("Initialized")

        # Start the chat loop
        await client.chat_loop()


# example streamable http url: http://localhost:8000/mcp as per the MCP spec
async def main(url: str, args: list[str]):
    # Use streamable HTTP client
    async with streamablehttp_client(url) as streams:
        await run_session(*streams[:2])  # Only pass read_stream and write_stream


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to connect to")
    parser.add_argument("args", nargs="*", help="Additional arguments")

    args = parser.parse_args()
    anyio.run(partial(main, args.url, args.args), backend="trio")


if __name__ == "__main__":
    cli() 