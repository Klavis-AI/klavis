#!/usr/bin/env python3
"""
Focused MCP Server with essential tools only
"""

import json
import sys
from typing import Dict, List, Any

# Import essential tools only
from tools.elevenlabs_voice import generate_voice_from_text
from tools.serpapi_search import search_web_query
from tools.tavily_search import search_with_tavily, summarize_webpage
from tools.generate_image import generate_image

class FocusedMCPServer:
    def __init__(self):
        # Due to cursor's limit of 40 tools (35 from replicate's direct API, 5 here), I only included the most essential tools for this server, although in the respective code files, there are more tools available.
        self.tools = {
            "generate_voice": {
                "description": "Generate speech from text using ElevenLabs",
                "parameters": {
                    "text": {"type": "string", "description": "Text to convert to speech"},
                    "voice_id": {"type": "string", "description": "Voice ID to use", "default": "21m00Tcm4TlvDq8ikWAM"}
                }
            },
            "search_web": {
                "description": "Search the web using SerpAPI",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 10}
                }
            },
            "search_tavily": {
                "description": "Advanced web search using Tavily",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "search_depth": {"type": "string", "description": "Search depth", "default": "basic"}
                }
            },
            "summarize_webpage": {
                "description": "Summarize a webpage using Tavily",
                "parameters": {
                    "url": {"type": "string", "description": "URL to summarize"}
                }
            },
            "generate_image": {
                "description": "Generate an image using Replicate",
                "parameters": {
                    "prompt": {"type": "string", "description": "Image generation prompt"}
                }
            }
        }
    
    def handle_request(self, request: Dict) -> Dict:
        # Handle MCP requests
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "focused-tools-mcp",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": tool["description"],
                            "inputSchema": {
                                "type": "object",
                                "properties": tool["parameters"],
                                "required": [k for k, v in tool["parameters"].items() if "default" not in v]
                            }
                        }
                        for name, tool in self.tools.items()
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            try:
                result = self.call_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -1,
                        "message": str(e)
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        # Call the appropriate tool based on name
        if tool_name == "generate_voice":
            return generate_voice_from_text(
                arguments["text"], 
                arguments.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
            )
        
        elif tool_name == "search_web":
            return search_web_query(
                arguments["query"], 
                arguments.get("num_results", 10)
            )
        
        elif tool_name == "search_tavily":
            return search_with_tavily(
                arguments["query"], 
                arguments.get("search_depth", "basic")
            )
        
        elif tool_name == "summarize_webpage":
            return summarize_webpage(arguments["url"])
        
        elif tool_name == "generate_image":
            return {"image_url": generate_image(arguments["prompt"])}
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

def main():
    # Main function to run the focused MCP server
    server = FocusedMCPServer()
    
    # Read from stdin and write to stdout for MCP protocol
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
