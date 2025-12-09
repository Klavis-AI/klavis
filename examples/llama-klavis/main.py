import json
import os
import asyncio
import webbrowser
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from klavis import Klavis, SandboxMcpServer

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.together.xyz/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
MCP_SERVERS_LOCAL_PATH = os.path.join(REPO_ROOT, "mcp_servers", "local")


async def main():
    # Initialize Klavis client
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
    
    # Step 1: Create sandbox
    gmail_sandbox = klavis_client.sandbox.create_sandbox(
        server_name=SandboxMcpServer.GMAIL,
    )
    
    snowflake_sandbox = klavis_client.sandbox.create_sandbox(
        server_name=SandboxMcpServer.SNOWFLAKE,
    )
    
    
    print(f"Gmail Sandbox: {gmail_sandbox}")
    print(f"Snowflake Sandbox: {snowflake_sandbox}")
    
    # Step 2: initialize snowflake sandbox data from snowflake.json
    snowflake_json_path = os.path.join(CURRENT_DIR, "snowflake.json")
    with open(snowflake_json_path, "r") as f:
        snowflake_data = json.load(f)
    
    initialize_response = klavis_client.sandbox.initialize_sandbox(
        sandbox_id=snowflake_sandbox.sandbox_id,
        databases=snowflake_data["databases"],
    )
    
    # Step 3: Create LangChain Agent with MCP Tools
    # Use the server URL from one of the created MCP servers
    
    mcp_client = MultiServerMCPClient({
        "gmail": {
            "transport": "streamable_http",
            "url": gmail_sandbox.server_url,
        },
        "snowflake": {
            "transport": "streamable_http",
            "url": snowflake_sandbox.server_url,
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
    
    delete_response = klavis_client.sandbox.delete_sandbox(
        server_name=SandboxMcpServer.SNOWFLAKE,
        sandbox_id=snowflake_sandbox.sandbox_id,
    )
    print(f"Delete Response: {delete_response}")
    print(f"Initialize Response: {initialize_response}")
    
    delete_response = klavis_client.sandbox.delete_sandbox(
        server_name=SandboxMcpServer.GMAIL,
        sandbox_id=gmail_sandbox.sandbox_id,
    )
    print(f"Delete Response: {delete_response}")
    


if __name__ == "__main__":
    asyncio.run(main())
