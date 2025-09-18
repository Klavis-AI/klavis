import os
import webbrowser
from typing import List, Dict, Any
from openai import OpenAI
from klavis import Klavis
from klavis.types import McpServerName, ToolFormat
 

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main():
    """Main function - initialize MCP client and start chat."""
    
    klavis_client = Klavis(api_key=os.getenv("KLAVIS_API_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Step 1: Create strata server
    response = klavis_client.mcp_server.create_strata_server(
        user_id="demo_user",
        servers=[McpServerName.GMAIL, McpServerName.YOUTUBE]
    )
    
    oauth_urls = response.oauth_urls
    
    for server_name, oauth_url in oauth_urls.items():
        webbrowser.open(oauth_url)
        input(f"Press Enter after completing {server_name} OAuth authorization...")

    tools_info = klavis_client.mcp_server.list_tools(
        server_url=response.strata_server_url,
        format=ToolFormat.OPENAI
    )
    openai_tools = tools_info.tools

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant with access to MCP tools. Be concise and helpful."
        }
    ]

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                pass
                break

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})

            response_msg = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0.7
            )

            assistant_message = response_msg.choices[0].message
            messages.append(assistant_message.model_dump())

            if assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    import json
                    result = klavis_client.mcp_server.call_tools(
                        server_url=response.strata_server_url,
                        tool_name=tool_call.function.name,
                        tool_args=json.loads(tool_call.function.arguments)
                    )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })

                final_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7
                )

                final_message = final_response.choices[0].message
                messages.append(final_message.model_dump())
                pass
            else:
                pass

        except KeyboardInterrupt:
            pass
            break
        except Exception as e:
            pass


if __name__ == "__main__":
    main()
