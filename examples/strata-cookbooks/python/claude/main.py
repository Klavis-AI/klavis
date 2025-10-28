import os
import asyncio
import webbrowser

from klavis import Klavis
from klavis.types import McpServerName, ToolFormat
from anthropic import Anthropic

from dotenv import load_dotenv
load_dotenv()

async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    # Step 1: Create a Strata MCP server with Gmail and Slack integrations
    response = klavis_client.mcp_server.create_strata_server(
        servers=[McpServerName.GMAIL, McpServerName.SLACK],
        user_id="1234"
    )

    # Step 2: Handle OAuth authorization for each services
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")

    # Step 3: Setup Claude client
    claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Step 4: Get MCP server tools in Anthropic format
    mcp_server_tools = klavis_client.mcp_server.list_tools(
        server_url=response.strata_server_url,
        format=ToolFormat.ANTHROPIC
    )

    # Step 5: Define user query
    user_query = "Check my latest 5 emails and summarize them in a Slack message to #general channel"

    messages = [
        {"role": "user", "content": user_query}
    ]

    # Step 6: Agent loop to handle tool calls
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        claude_response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            system="You are a helpful assistant. Use the available tools to answer the user's question.",
            messages=messages,
            tools=mcp_server_tools.tools
        )

        messages.append({"role": "assistant", "content": claude_response.content})

        if claude_response.stop_reason == "tool_use":
            tool_results = []

            for content_block in claude_response.content:
                if content_block.type == "tool_use":
                    function_name = content_block.name
                    function_args = content_block.input

                    print(f"🔧 Calling: {function_name}, with args: {function_args}")

                    result = klavis_client.mcp_server.call_tools(
                        server_url=response.strata_server_url,
                        tool_name=function_name,
                        tool_args=function_args
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": str(result)
                    })

            messages.append({"role": "user", "content": tool_results})
            continue
        else:
            # Print only the final AI response content
            final_response = claude_response.content[0].text
            print(f"\n🤖 Final Response: {final_response}")
            return final_response

    print("Max iterations reached without final response")
    return None


if __name__ == "__main__":
    asyncio.run(main())