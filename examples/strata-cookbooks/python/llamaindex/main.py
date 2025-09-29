import os
import asyncio
import webbrowser

from klavis import Klavis
from klavis.types import McpServerName
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.tools.mcp import BasicMCPClient
from llama_index.tools.mcp import (
    aget_tools_from_mcp_url,
)

from dotenv import load_dotenv
load_dotenv()

async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    # Step 1: Create a Strata MCP server with Gmail and YouTube integrations
    response = klavis_client.mcp_server.create_strata_server(
        user_id="1234",
        servers=[McpServerName.GMAIL, McpServerName.YOUTUBE],
    )

    # Step 2: Handle OAuth authorization if needed
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")

    # Get all available tools from Strata
    tools = await aget_tools_from_mcp_url(
        response.strata_server_url, 
        client=BasicMCPClient(response.strata_server_url)
    )

    # Setup LLM
    llm = OpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    # Step 3: Create LlamaIndex agent with MCP tools
    agent = FunctionAgent(
        name="my_first_agent",
        description="Agent using MCP-based tools",
        tools=tools,
        llm=llm,
        system_prompt="You are an AI assistant that uses MCP tools.",
    )

    my_email = "golden-kpop@example.com" # TODO: Replace with your email
    youtube_video_url = "https://youtu.be/yebNIHKAC4A?si=1Rz_ZsiVRz0YfOR7" # TODO: Replace with your favorite youtube video URL
    # Step 4: Invoke the agent
    response = await agent.run(
        f"summarize this video - {youtube_video_url} and mail this summary to my email {my_email}"
    )

    print(response)

if __name__ == "__main__":
    asyncio.run(main())