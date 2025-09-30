import json
import os
import webbrowser
from typing import Dict, Any, List
from openai import OpenAI
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

def stream_chat_completion(client: OpenAI, messages: List[Dict[str, str]], klavis_client: Klavis, server_url: str) -> None:
    """
    Stream chat completion from OpenAI with function calling support.
    
    Args:
        client: OpenAI client instance
        messages: List of conversation messages
        klavis_client: Klavis client instance
        server_url: MCP server URL
    """
    try:
            
        tools_info = klavis_client.mcp_server.list_tools(
            server_url=server_url,
            format=ToolFormat.OPENAI
        )
        
        # Create streaming completion with function calling
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools_info.tools,
            tool_choice="auto",
            stream=True,
            temperature=0.7
        )
        
        # Add assistant message to messages list that we'll modify in place
        messages.append({"role": "assistant", "content": ""})
        tool_calls = []
        current_tool_call = None
        is_tool_call = False
        
        print("\n🤖 Assistant: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                # Regular content streaming
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                messages[-1]["content"] += content
                
            elif chunk.choices[0].delta.tool_calls:
                # Tool call streaming
                is_tool_call = True
                delta_tool_calls = chunk.choices[0].delta.tool_calls
                
                for delta_tool_call in delta_tool_calls:
                    if delta_tool_call.index is not None:
                        # Ensure we have enough tool calls in our list
                        while len(tool_calls) <= delta_tool_call.index:
                            tool_calls.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        current_tool_call = tool_calls[delta_tool_call.index]
                        
                        if delta_tool_call.id:
                            current_tool_call["id"] += delta_tool_call.id
                        if delta_tool_call.function:
                            if delta_tool_call.function.name:
                                current_tool_call["function"]["name"] += delta_tool_call.function.name
                            if delta_tool_call.function.arguments:
                                current_tool_call["function"]["arguments"] += delta_tool_call.function.arguments
        
        
        # Handle tool calls if present
        if is_tool_call and tool_calls:
            for tool_call in tool_calls:
                if tool_call["function"]["name"]:
                    print(f"\n🔧 Calling function: {tool_call['function']['name']}")
                    
                    # Execute function call
                    function_result = klavis_client.mcp_server.call_tools(
                        server_url=server_url,
                        tool_name=tool_call["function"]["name"],
                        tool_args=json.loads(tool_call["function"]["arguments"])
                    )
                    
                    # Add tool call to the assistant message already in messages
                    messages[-1]["tool_calls"] = tool_calls
                    messages[-1]["content"] = messages[-1]["content"] or None
                    
                    # Add tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(function_result)
                    })
            
            # Get final response with tool results
            print("\n🤖 Assistant: ", end="", flush=True)
            final_stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True
            )
            
            messages.append({"role": "assistant", "content": ""})
            for chunk in final_stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    messages[-1]["content"] += content
            
        print()  # Final new line
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
    
    # Create MCP server instance
    mcp_instance = klavis_client.mcp_server.create_server_instance(
        server_name=McpServerName.YOUTUBE,  # Close CRM as an example
        user_id="1234")
    
    # Open OAuth authorization if needed
    if hasattr(mcp_instance, 'oauth_url') and mcp_instance.oauth_url:
        webbrowser.open(mcp_instance.oauth_url)
        print(f"🔐 Opening OAuth authorization for Close CRM: {mcp_instance.oauth_url}")
        print("Please complete the OAuth authorization in your browser before continuing...")
        input("Press Enter after completing OAuth authorization...")
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to various Klavis MCP tools"
        }
    ]
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            stream_chat_completion(openai_client, messages, klavis_client, mcp_instance.server_url)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main() 