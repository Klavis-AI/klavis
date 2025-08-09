#!/usr/bin/env python3
"""
Focused MCP Server with essential tools only.

Design notes (aligned with Klavis AI guidelines):
- Tools are atomic and clearly named.
- Descriptions explicitly state purpose, inputs, and outputs to aid LLM usage.
- External API errors are handled and surfaced in a structured shape the AI can self-correct from.
"""

import json
import sys
from typing import Dict, List, Any

# Import essential tools only (via tools package public API)
from tools import (
    generate_voice_from_text,
    search_web_query,
    search_with_tavily,
    summarize_webpage,
    generate_image,
)

class FocusedMCPServer:
    def __init__(self):
        # Due to cursor's limit of 40 tools (35 from replicate's direct API, 5 here), I only included the most essential tools for this server, although in the respective code files, there are more tools available.
        self.tools = {
            "generate_voice": {
                "description": (
                    "Convert text into speech using ElevenLabs. "
                    "Inputs: text (required), voice_id (optional, default '21m00Tcm4TlvDq8ikWAM'). "
                    "Returns: JSON with {success: bool, audio_path: string if success, error: string if failure}."
                ),
                "parameters": {
                    "text": {"type": "string", "description": "Text to convert to speech (required)"},
                    "voice_id": {"type": "string", "description": "Voice ID to use (optional)", "default": "21m00Tcm4TlvDq8ikWAM"}
                }
            },
            "search_web": {
                "description": (
                    "Search the web using SerpAPI's Google engine. "
                    "Inputs: query (required), num_results (optional, default 10). "
                    "Returns: JSON {success: bool, organic_results: list, total_results: int, error?: string}."
                ),
                "parameters": {
                    "query": {"type": "string", "description": "Search query text (required)"},
                    "num_results": {"type": "integer", "description": "Max results to return (optional)", "default": 10}
                }
            },
            "search_tavily": {
                "description": (
                    "Perform an AI-powered web search using Tavily. "
                    "Inputs: query (required), search_depth (optional, 'basic'|'advanced', default 'basic'). "
                    "Returns: JSON {success: bool, results: list, total_results: int, error?: string}."
                ),
                "parameters": {
                    "query": {"type": "string", "description": "Search query text (required)"},
                    "search_depth": {"type": "string", "description": "Search depth: 'basic' or 'advanced' (optional)", "default": "basic"}
                }
            },
            "summarize_webpage": {
                "description": (
                    "Summarize the content of a webpage using Tavily. "
                    "Inputs: url (required). "
                    "Returns: JSON {success: bool, url: string, title: string, summary: string, error?: string}."
                ),
                "parameters": {
                    "url": {"type": "string", "description": "URL to summarize (required)"}
                }
            },
            "generate_image": {
                "description": (
                    "Generate an image using a Replicate model (Flux Schnell). "
                    "Inputs: prompt (required). "
                    "Returns: JSON {image_url: string|null}; may return null if generation fails."
                ),
                "parameters": {
                    "prompt": {"type": "string", "description": "Image generation prompt (required)"}
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
