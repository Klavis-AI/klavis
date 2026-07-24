import os
import asyncio
import webbrowser

from klavis import Klavis
from klavis.types import McpServerName
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from autogen.mcp import create_toolkit
from autogen import AssistantAgent, LLMConfig

from dotenv import load_dotenv
load_dotenv()


async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    # Step 1: Create a Strata MCP server with Gmail and Slack integrations
    response = klavis_client.mcp_server.create_strata_server(
        servers=[McpServerName.GMAIL, McpServerName.SLACK],
        user_id="demo_user"
    )

    # Step 2: Handle OAuth authorization if needed
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")

    # Step 3: Connect to Strata MCP server and create AG2 toolkit
    async with (
        streamable_http_client(response.strata_server_url) as (
            read_stream,
            write_stream,
            _,
        ),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        toolkit = await create_toolkit(session=session, use_mcp_resources=False)
        print(f"Available tools: {[tool.name for tool in toolkit.tools]}")

        # Step 4: Create AG2 AssistantAgent with MCP tools
        assistant = AssistantAgent(
            name="klavis_assistant",
            system_message=(
            "You are a helpful assistant that uses MCP tools to complete tasks. "
            "When calling execute_action, always pass request body parameters via 'body_schema' "
            "and URL query parameters via 'query_params'. "
            "Check get_action_details to determine which parameters go where."
        ),
            llm_config=LLMConfig(
                {
                    "model": "gpt-4o-mini",
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }
            ),
        )

        toolkit.register_for_llm(assistant)

        # Step 5: Run the agent
        user_query = "Check my latest 5 emails and summarize them in a Slack message to #general"  # Change this query as needed

        print(f"\n{'='*80}\n👤 USER: {user_query}\n{'='*80}\n")

        result = await assistant.a_run(
            message=user_query,
            tools=toolkit.tools,
            max_turns=10,
            user_input=False,
        )
        await result.process()


if __name__ == "__main__":
    asyncio.run(main())
