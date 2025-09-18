import os
import asyncio
import webbrowser

from klavis import Klavis
from klavis.types import McpServerName
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from dotenv import load_dotenv
load_dotenv()


async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    # Step 1: Create a Strata MCP server with Gmail and Google Calendar integrations
    response = klavis_client.mcp_server.create_strata_server(
        user_id="demo_user",
        servers=[McpServerName.GMAIL, McpServerName.YOUTUBE],
    )

    # Step 2: Handle OAuth authorization if needed
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")

    # Step 3: Create LangChain Agent with MCP Tools
    mcp_client = MultiServerMCPClient({
        "strata": {
            "transport": "streamable_http",
            "url": response.strata_server_url,
        }
    })

    # Get all available tools from Strata
    tools = await mcp_client.get_tools()
    # Setup LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 4: Create LangChain agent with MCP tools
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=(
            "You are a helpful assistant that can use MCP tools. "
        ),
    )

    my_email = "golden-kpop@example.com" # TODO: Replace with your email
    # Step 5: Invoke the agent
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": f"summarize this video - https://youtu.be/yebNIHKAC4A?si=1Rz_ZsiVRz0YfOR7 and send the summary to my email {my_email}"}],
    })
    
    # Print only the final AI response content
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
