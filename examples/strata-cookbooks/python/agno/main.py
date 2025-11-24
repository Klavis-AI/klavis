import os
import asyncio
import webbrowser

from klavis import Klavis
from klavis.types import McpServerName

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

from dotenv import load_dotenv
load_dotenv()

klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

response = klavis_client.mcp_server.create_strata_server(
    servers=[McpServerName.GMAIL, McpServerName.SLACK],
    user_id="1234"
)

# Handle OAuth authorization for each service
if response.oauth_urls:
    for server_name, oauth_url in response.oauth_urls.items():
        webbrowser.open(oauth_url)
        print(f"Please open this URL to complete {server_name} OAuth authorization: {oauth_url}")


async def agno_with_mcp_server(mcp_server_url: str, user_query: str):
    """Run an Agno agent with Klavis MCP server tools."""

    async with MCPTools(transport="streamable-http", url=mcp_server_url) as mcp_tools:
        agent = Agent(
            model=OpenAIChat(
                id="gpt-4o",
                api_key=os.getenv("OPENAI_API_KEY")
            ),
            instructions="You are a helpful AI assistant.",
            tools=[mcp_tools],
            markdown=True,
        )

        response = await agent.arun(user_query)
        return response.content


async def main():
    result = await agno_with_mcp_server(
        mcp_server_url=response.strata_server_url,
        user_query="Check my latest 5 emails and summarize them in a Slack message to #general"
    )
    print(f"\nFinal Response: {result}")


if __name__ == "__main__":
    asyncio.run(main())