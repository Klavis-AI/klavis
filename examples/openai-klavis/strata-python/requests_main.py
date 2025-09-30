import json
import os
import webbrowser
from typing import Dict, Any, List
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

KLAVIS_API_BASE_URL = "https://api.klavis.ai"


class KlavisClient:
    """Klavis API client using requests library"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = KLAVIS_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_strata_server(self, servers: List[str], user_id: str) -> Dict[str, Any]:
        """Create a Strata MCP server instance."""
        url = f"{self.base_url}/mcp-server/strata/create"
        payload = {"userId": user_id, "servers": servers}
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def list_tools(self, server_url: str, format: str = "openai") -> Dict[str, Any]:
        """List all available tools from the MCP server."""
        url = f"{self.base_url}/mcp-server/list-tools"
        payload = {"serverUrl": server_url, "format": format}
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def call_tool(self, server_url: str, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        url = f"{self.base_url}/mcp-server/call-tool"
        payload = {"serverUrl": server_url, "toolName": tool_name, "toolArgs": tool_args}
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()


def stream_chat_completion(client: OpenAI, messages: List[Dict[str, str]], klavis_client: KlavisClient, server_url: str) -> None:
    """Stream chat completion from OpenAI with function calling support."""
    tools_response = klavis_client.list_tools(server_url=server_url, format="openai")
    tools_info = tools_response.get("tools", [])
    
    max_iterations = 20
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        stream = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=tools_info,
            tool_choice="auto",
            stream=True,
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
                    
                    print(f"\n🔧 Calling tool: {tool_name}")
                    print(f"   Arguments: {json.dumps(tool_args, indent=2)}")
                    
                    try:
                        function_response = klavis_client.call_tool(
                            server_url=server_url,
                            tool_name=tool_name,
                            tool_args=tool_args
                        )
                        
                        if function_response.get("success"):
                            result = function_response.get("result", {})
                            function_result = result.get("content", result)
                        else:
                            function_result = {"error": function_response.get("error", "Unknown error")}
                        
                    except Exception as e:
                        function_result = {"error": str(e)}
                                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(function_result) if isinstance(function_result, dict) else str(function_result)
                    })
            continue
        else:
            if content:
                messages.append({"role": "assistant", "content": content})
            print()
            break


def chat_completion(client: OpenAI, messages: List[Dict[str, str]], klavis_client: KlavisClient, server_url: str) -> None:
    """Non-streaming chat completion from OpenAI with function calling support."""
    tools_response = klavis_client.list_tools(server_url=server_url, format="openai")
    tools_info = tools_response.get("tools", [])
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=tools_info,
            tool_choice="auto",
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
                
                print(f"\n🔧 Calling tool: {tool_name}")
                print(f"   Arguments: {json.dumps(tool_args, indent=2)}")
                
                try:
                    function_response = klavis_client.call_tool(
                        server_url=server_url,
                        tool_name=tool_name,
                        tool_args=tool_args
                    )
                    
                    if function_response.get("success"):
                        result = function_response.get("result", {})
                        function_result = result.get("content", result)
                    else:
                        function_result = {"error": function_response.get("error", "Unknown error")}
                    
                except Exception as e:
                    function_result = {"error": str(e)}
                                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_result) if isinstance(function_result, dict) else str(function_result)
                })
            continue
        else:
            messages.append({"role": "assistant", "content": assistant_message.content})
            print(f"\n🤖 Assistant: {assistant_message.content}")
            break


def main():
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    klavis_client = KlavisClient(api_key=os.getenv("KLAVIS_API_KEY"))
    
    response = klavis_client.create_strata_server(
        servers=["gmail", "slack"],
        user_id="4321"
    )
    
    oauth_urls = response.get("oauthUrls", {})
    if oauth_urls:
        for server_name, oauth_url in oauth_urls.items():
            webbrowser.open(oauth_url)
            input(f"Press Enter after completing {server_name} OAuth authorization...")
    
    server_url = response.get("strataServerUrl")
    messages = [{"role": "system", "content": "You are a helpful assistant with access to various MCP tools"}]
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if not user_input:
            continue
            
        messages.append({"role": "user", "content": user_input})
        stream_chat_completion(openai_client, messages, klavis_client, server_url)


if __name__ == "__main__":
    main()
