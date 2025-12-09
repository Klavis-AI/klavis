import os
import asyncio
import webbrowser
from dotenv import load_dotenv
from klavis import Klavis, McpServerName
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.together.xyz/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
MCP_SERVERS_LOCAL_PATH = os.path.join(REPO_ROOT, "mcp_servers", "local")

async def main():
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))

    # Step 1: Create a Strata MCP server with Gmail and Google Calendar integrations
    response = klavis_client.mcp_server.create_strata_server(
        user_id="demo_user",
        servers=[McpServerName.GOOGLE_CALENDAR],
    )
    
    gmail_mcp_server = klavis_client.mcp_server.create_server_instance(
        server_name="Gmail",
        user_id="demo_user",
    )
    
    snowflake_mcp_server = klavis_client.mcp_server.create_server_instance(
        server_name="Snowflake",
        user_id="demo_user",
    )

    # Step 2: Handle OAuth authorization if needed
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")
            
    # snowflake_mcp_server = klavis_client.mcp_server.create_server_instance(
    #     server_name=McpServerName.SNOWFLAKE,
    #     user_id="demo_user",
    # )

    # Step 3: Create LangChain Agent with MCP Tools
    mcp_client = MultiServerMCPClient({
        # "filesystem": {
        #     "transport": "stdio",
        #     "command": "npx",
        #     "args": [
        #         "-y",
        #         os.path.join(MCP_SERVERS_LOCAL_PATH, "filesystem"),
        #         MCP_SERVERS_LOCAL_PATH
        #     ],
        #     "env": dict(os.environ)
        # },
        # "pdf-tools": {
        #     "transport": "stdio",
        #     "command": "uvx",
        #     "args": [
        #         "--from",
        #         os.path.join(MCP_SERVERS_LOCAL_PATH, "pdf-tools"),
        #         "pdf-tools-mcp",
        #         "--workspace_path",
        #         MCP_SERVERS_LOCAL_PATH,
        #         "--tempfile_dir",
        #         MCP_SERVERS_LOCAL_PATH
        #     ],
        #     "env": dict(os.environ)
        # },
        "strata": {
            "transport": "streamable_http",
            "url": response.strata_server_url,
        }
    })

    # Get all available tools from Strata
    tools = await mcp_client.get_tools()
    # Setup LLM
    llm = ChatOpenAI(model=LLM_MODEL, api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    # Step 4: Create LangChain agent with MCP tools
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=(
            "You are a helpful assistant that can use MCP tools. "
        ),
    )

    user_message = f"get my today's(2025-12-08) events"
    
    # Step 5: Invoke the agent with streaming for detailed logging
    print(f"\n{'='*80}\n👤 USER: {user_message}\n{'='*80}\n")
    
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]}
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
