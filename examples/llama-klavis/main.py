import os
import asyncio
import json
import shutil
from typing import Dict
from dotenv import load_dotenv

from openai import OpenAI
from mcp import StdioServerParameters
from mcp_client import MultiServerMCPClient

load_dotenv()

# demo flow: 
# 1. snowflake init data 
# 2. llama model interact with 4 mcp servers : snowflake, filesystem, PDF, gmail
# 3. do the task
# 4. Gmail dump data

# Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.together.xyz/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")

def _setup_meta_llama() -> OpenAI:
    if not LLM_API_KEY:
        print("Please set LLM_API_KEY environment variable")
        return None
    
    return OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

def _get_local_server_config() -> StdioServerParameters:
    """Helper to get configuration for the local filesystem server."""
    
    # Prefer npx for the official filesystem server implementation
    if shutil.which("npx"):
        command = "npx"
        args = ["-y", "@modelcontextprotocol/server-filesystem", "."]
    elif shutil.which("uvx"):
        # Warning: The PyPI package 'mcp-server-filesystem' might behave unexpectedly
        command = "uvx"
        args = ["mcp-server-filesystem", "."]
    else:
        raise RuntimeError("Neither 'npx' nor 'uvx' found. Please install nodejs or uv.")

    return StdioServerParameters(
        command=command,
        args=args,
        env=dict(os.environ)  # Pass current environment
    )

async def main():
    # 1. Setup Llama Client
    client = _setup_meta_llama()
    if not client:
        return

    # 2. Define MCP Servers
    # We can add multiple servers here. For this example, we use the filesystem server.
    try:
        servers = {
            "filesystem": _get_local_server_config(),
            # "git": StdioServerParameters(...) # Add more servers here
        }
    except RuntimeError as e:
        print(f"Setup error: {e}")
        return

    # 3. Initialize Multi-Server Client
    print("Connecting to MCP servers...")
    async with MultiServerMCPClient(servers) as mcp_client:
        
        # 4. Aggregate Tools
        tools = await mcp_client.get_all_tools()
        print(f"\n📦 Aggregated {len(tools)} tools from {len(servers)} servers.")
        
        # Convert MCP tools to OpenAI tool format
        openai_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in tools]

        # 5. Interact with Llama
        query = "List the files in the current directory."
        print(f"\nUser: {query}")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant with access to local tools. When a tool returns information, please summarize it or present it clearly to the user."},
            {"role": "user", "content": query}
        ]

        print("🤖 Sending request to Llama...")
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # 6. Handle Tool Calls
        if response_message.tool_calls:
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = tool_call.function.arguments
                
                print(f"🛠️ Llama wants to call: {func_name}")
                
                # Execute tool via MultiServerMCPClient
                try:
                    result = await mcp_client.call_tool(func_name, json.loads(func_args))
                    
                    # Format result
                    content = ""
                    if result.content:
                        for item in result.content:
                            if item.type == "text":
                                content += item.text
                            else:
                                content += str(item)
                    else:
                        content = "No output"
                        
                    print(f"📄 Result: {content[:100]}...")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })
                except Exception as e:
                    print(f"❌ Error executing tool {func_name}: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Error: {str(e)}"
                    })

            # Get final response
            print("🤖 Getting final answer...")
            final_response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=openai_tools  # Keep tools context
            )
            print(f"\nAssistant: {final_response.choices[0].message.content}")
        else:
            print(f"\nAssistant: {response_message.content}")

if __name__ == "__main__":
    asyncio.run(main())
