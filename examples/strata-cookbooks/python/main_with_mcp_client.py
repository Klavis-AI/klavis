import os
import asyncio
import json
from klavis import Klavis
from klavis.types import McpServerName
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 1: Create MCP server
    server = klavis_client.mcp_server.create_server_instance(
        server_name=McpServerName.GMAIL,
        user_id="1234",
    )

    # Step 2: Create MCP client (streamablehttp) to connect to the MCP server
    async with streamablehttp_client(server.server_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()

            openai_tools = []
            for tool in tools.tools:
                openai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                        },
                    }
                )

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant with access to tools.",
                }
            ]

            while True:
                try:
                    user_input = input("\nYou: ").strip()

                    messages.append({"role": "user", "content": user_input})

                    response = openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=openai_tools,
                        tool_choice="auto",
                    )

                    assistant_message = response.choices[0].message
                    messages.append(assistant_message.model_dump())

                    if assistant_message.tool_calls:
                        for tool_call in assistant_message.tool_calls:
                            function_name = tool_call.function.name
                            function_args = json.loads(tool_call.function.arguments)

                            result = await session.call_tool(function_name, function_args)
                            tool_text = (
                                result.content[0].text if getattr(result, "content", None) else "No result"
                            )

                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "content": tool_text,
                                }
                            )

                        final = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                        )
                        final_message = final.choices[0].message
                        messages.append(final_message.model_dump())
                        print(f"Assistant: {final_message.content}")
                    else:
                        print(f"Assistant: {assistant_message.content}")
                except KeyboardInterrupt:
                    break
                except Exception:
                    pass


if __name__ == "__main__":
    asyncio.run(main())
