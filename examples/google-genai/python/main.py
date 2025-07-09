import os
import webbrowser
from google import genai
from google.genai import types

from klavis import Klavis
from klavis.types import McpServerName, ToolFormat

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    # Get API keys
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    klavis_api_key = os.getenv("KLAVIS_API_KEY")
    
    if not gemini_api_key or not klavis_api_key:
        print("Error: GEMINI_API_KEY or KLAVIS_API_KEY environment variable is not set")
        return
    
    # Initialize clients
    gemini_client = genai.Client(api_key=gemini_api_key)
    klavis_client = Klavis(api_key=klavis_api_key)
    
    # Create MCP server instance
    print("🔧 Creating MCP server instance...")
    mcp_instance = klavis_client.mcp_server.create_server_instance(
        server_name=McpServerName.NOTION,
        user_id="1234",
        platform_name="Klavis",
    )
    print("--- mcp_instance --- \n", mcp_instance)
    
    # Handle OAuth if needed
    if hasattr(mcp_instance, 'oauth_url') and mcp_instance.oauth_url:
        webbrowser.open(mcp_instance.oauth_url)
        print(f"🔐 Opening OAuth authorization: {mcp_instance.oauth_url}")
        print("Please complete the OAuth authorization in your browser...")
        input("Press Enter after completing OAuth authorization...")
    
    # Get tools from Klavis
    mcp_tools = klavis_client.mcp_server.list_tools(
        server_url=mcp_instance.server_url,
        format=ToolFormat.GEMINI,
    )
    
    contents = []
    
    # Chat loop
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
            
            response = gemini_client.models.generate_content(
                model='gemini-1.5-pro',
                contents=contents,
                config=types.GenerateContentConfig(tools=mcp_tools.tools)
            )
            
            if response.candidates and response.candidates[0].content.parts:
                contents.append(response.candidates[0].content)
                
                # Check if there are function calls to execute
                has_function_calls = False
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        print(f"\n🔧 Calling function: {part.function_call.name}")
                        
                        try:
                            # Execute tool call via Klavis
                            function_result = klavis_client.mcp_server.call_tools(
                                server_url=mcp_instance.server_url,
                                tool_name=part.function_call.name,
                                tool_args=dict(part.function_call.args),
                            )
                            
                            # Create function response in the proper format
                            function_response = {'result': function_result.result}
                            
                        except Exception as e:
                            print(f"Function call error: {e}")
                            function_response = {'error': str(e)}
                        
                        function_response_part = types.Part.from_function_response(
                            name=part.function_call.name,
                            response=function_response,
                        )
                        function_response_content = types.Content(
                            role='tool', 
                            parts=[function_response_part]
                        )
                        contents.append(function_response_content)
                
                if has_function_calls:
                    final_response = gemini_client.models.generate_content(
                        model='gemini-1.5-pro',
                        contents=contents,
                        config=types.GenerateContentConfig(tools=mcp_tools.tools)
                    )
                    
                    # Add final response to conversation history
                    contents.append(final_response.candidates[0].content)
                    print(f"🤖 Assistant: {final_response.text}")
                else:
                    # No function calls, just display the response
                    print(f"🤖 Assistant: {response.text}")
                    contents.append(response.candidates[0].content)
            else:
                # No response content, handle gracefully
                print("No response generated.")
            
            print()  # Add spacing
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 