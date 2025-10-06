import json
import os
import webbrowser
from typing import Dict, Any, List
from openai import OpenAI
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

from dotenv import load_dotenv
load_dotenv()

def stream_chat_completion(client: OpenAI, messages: List[Dict[str, str]], klavis_client: Klavis, user_id: str, servers: List[McpServerName]) -> None:
    """
    Stream chat completion from OpenAI with function calling support.
    Handles multiple rounds of tool calls until a final response is ready.
    Creates Strata server and handles OAuth within the method.
    """
    # Create Strata server with the provided servers and user_id
    response = klavis_client.mcp_server.create_strata_server(
        servers=servers, 
        user_id=user_id
    )
    
    # Handle OAuth if required
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")
    
    server_url = response.strata_server_url
    
    tools_info = klavis_client.mcp_server.list_tools(
        server_url=server_url,
        format=ToolFormat.OPENAI
    )
    
    max_iterations = 20
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools_info.tools,
            tool_choice="auto",
            stream=True,
            temperature=0.7
        )
        
        tool_calls = []
        is_tool_call = False
        content = ""
        
        if iteration == 1 or messages[-1].get("role") == "tool":
            print("\n🤖 Assistant: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                print(chunk_content, end="", flush=True)
                content += chunk_content
                
            elif chunk.choices[0].delta.tool_calls:
                is_tool_call = True
                
                for delta_tool_call in chunk.choices[0].delta.tool_calls:
                    if delta_tool_call.index is not None:
                        while len(tool_calls) <= delta_tool_call.index:
                            tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                        
                        current_tool_call = tool_calls[delta_tool_call.index]
                        
                        if delta_tool_call.id:
                            current_tool_call["id"] += delta_tool_call.id
                        if delta_tool_call.function:
                            if delta_tool_call.function.name:
                                current_tool_call["function"]["name"] += delta_tool_call.function.name
                            if delta_tool_call.function.arguments:
                                current_tool_call["function"]["arguments"] += delta_tool_call.function.arguments
        
        if is_tool_call and tool_calls:
            messages.append({
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls
            })
            
            for tool_call in tool_calls:
                if tool_call["function"]["name"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"Calling: {tool_name}")
                    print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                    
                    function_result = klavis_client.mcp_server.call_tools(
                        server_url=server_url,
                        tool_name=tool_name,
                        tool_args=tool_args
                    )
                                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(function_result)
                    })
            continue
        else:
            if content:
                messages.append({"role": "assistant", "content": content})
            print()
            break


def chat_completion(openai_client: OpenAI, messages: List[Dict[str, str]], klavis_client: Klavis, user_id: str, servers: List[McpServerName]) -> None:
    """
    Non-streaming chat completion using OpenAI SDK with function calling support.
    Handles multiple rounds of tool calls until a final response is ready.
    Creates Strata server and handles OAuth within the method.
    """
    # Create Strata server with the provided servers and user_id
    response = klavis_client.mcp_server.create_strata_server(
        servers=servers, 
        user_id=user_id
    )
    
    # Handle OAuth if required
    if response.oauth_urls:
        for server_name, oauth_url in response.oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")
    
    server_url = response.strata_server_url
    
    tools_info = klavis_client.mcp_server.list_tools(
        server_url=server_url,
        format=ToolFormat.OPENAI
    )
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Use OpenAI SDK for chat completion
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools_info.tools,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        if assistant_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"Calling: {tool_name}")
                print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                
                function_result = klavis_client.mcp_server.call_tools(
                    server_url=server_url,
                    tool_name=tool_name,
                    tool_args=tool_args
                )
                                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(function_result)
                })
            continue
        else:
            messages.append({"role": "assistant", "content": assistant_message.content})
            print(f"\n🤖 Assistant: {assistant_message.content}")
            break


def main():    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
    
    servers = [McpServerName.GMAIL]
    user_id = "4321"
                
    messages = [{"role": "system", "content": "You are a helpful assistant with access to various MCP tools"}]
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input:
            messages.append({"role": "user", "content": user_input})
            chat_completion(openai_client, messages, klavis_client, user_id, servers)


if __name__ == "__main__":
    main() 