import json
import os
import sys
from typing import Dict, Any, List
from openai import OpenAI


def get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    Get weather information for a specific location.
    This is a mock function that returns sample weather data.
    
    Args:
        location: The city or location name
        unit: Temperature unit (celsius or fahrenheit)
    
    Returns:
        Dictionary containing weather information
    """
    # Mock weather data - in real implementation, you'd call a weather API
    mock_weather = {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "Partly cloudy",
        "humidity": 65,
        "wind_speed": 10
    }
    
    print(f"🌤️  Fetching weather for {location}...")
    return mock_weather


def get_available_functions() -> Dict[str, callable]:
    """Return a dictionary of available functions for function calling."""
    return {
        "get_weather": get_weather
    }


def get_function_definitions() -> List[Dict[str, Any]]:
    """Return OpenAI tool definitions for function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a specific location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state/country, e.g. San Francisco, CA or London, UK"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]


def handle_function_call(function_name: str, function_args: str) -> str:
    """
    Execute a function call and return the result.
    
    Args:
        function_name: Name of the function to call
        function_args: JSON string of function arguments
    
    Returns:
        JSON string of function result
    """
    available_functions = get_available_functions()
    
    if function_name not in available_functions:
        return json.dumps({"error": f"Function {function_name} not found"})
    
    try:
        args = json.loads(function_args)
        function_to_call = available_functions[function_name]
        result = function_to_call(**args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def stream_chat_completion(client: OpenAI, messages: List[Dict[str, str]]) -> None:
    """
    Stream chat completion from OpenAI with function calling support.
    
    Args:
        client: OpenAI client instance
        messages: List of conversation messages
    """
    try:
        # Create streaming completion with function calling
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=get_function_definitions(),
            tool_choice="auto",
            stream=True,
            temperature=0.7
        )
        
        current_message = {"role": "assistant", "content": ""}
        tool_calls = []
        current_tool_call = None
        is_tool_call = False
        
        print("\n🤖 Assistant: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                # Regular content streaming
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                current_message["content"] += content
                
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
        
        print()  # New line after streaming
        
        # Handle tool calls if present
        if is_tool_call and tool_calls:
            for tool_call in tool_calls:
                if tool_call["function"]["name"]:
                    print(f"\n🔧 Calling function: {tool_call['function']['name']}")
                    
                    # Execute function call
                    function_result = handle_function_call(
                        tool_call["function"]["name"], 
                        tool_call["function"]["arguments"]
                    )
                    
                    # Add tool call to assistant message
                    current_message["tool_calls"] = tool_calls
                    current_message["content"] = current_message["content"] or None
                    
                    # Add assistant message with tool calls
                    messages.append(current_message)
                    
                    # Add tool result message
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": function_result
                    })
            
            # Get final response with tool results
            print("\n🤖 Assistant: ", end="", flush=True)
            final_stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True
            )
            
            final_message = {"role": "assistant", "content": ""}
            for chunk in final_stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    final_message["content"] += content
            
            messages.append(final_message)
        else:
            messages.append(current_message)
            
        print()  # Final new line
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
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
            
            stream_chat_completion(openai_client, messages)
            
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