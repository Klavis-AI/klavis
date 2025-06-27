"""
This is a simple MCP client that uses streamable HTTP to connect to an MCP server.
It is useful for simple testing of MCP servers.

To run the client, use the following command:
```
python streamable_http_client.py <url> <args>
```
"""

import argparse
import json
import logging
from contextlib import AsyncExitStack
from functools import partial
from typing import Optional

import anyio
import sys
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from openai import OpenAI

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
        self.openai = OpenAI()
        self.messages = []  # Store conversation history

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        # Add user message to conversation history
        self.messages.append({
            "role": "user",
            "content": query
        })

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Initial OpenAI API call with full conversation history
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            messages=self.messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        final_text = []

        message = response.choices[0].message
        if message.content:
            final_text.append(message.content)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)  # Parse JSON string to dict

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Add assistant message with tool use to history
                self.messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                
                # Add tool result to history
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content[0].text)
                })
                final_text.append(f"[Tool call result: {result.content[0].text}]")

                # Get next response from OpenAI with full history
                response = self.openai.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=1000,
                    messages=self.messages,
                )

                final_text.append(response.choices[0].message.content)

        # Add final assistant response to history
        if response.choices[0].message.content:
            self.messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries, 'clear' to clear history, or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                elif query.lower() == 'clear':
                    self.messages = []
                    print("Message history cleared.")
                    continue

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