#!/usr/bin/env python3
"""
Reddit MCP Server for Klavis AI
Provides atomic tools for interacting with Reddit API.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server


from tools.posts import PostsTools
from tools.subreddits import SubredditsTools
from tools.users import UsersTools
from tools.search import SearchTools

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedditMCPServer:
    """Reddit MCP Server implementation."""
    
    def __init__(self):
        """Initialize the Reddit MCP server with all tools."""
        self.server = Server("reddit-mcp")
        
        # Initialize tool modules
        self.posts_tools = PostsTools()
        self.subreddits_tools = SubredditsTools()
        self.users_tools = UsersTools()
        self.search_tools = SearchTools()
        
        # Register all tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all Reddit MCP tools."""
        
        # Search tools
        @self.server.list_tools()
        async def handle_list_tools():
            """List all available Reddit MCP tools."""
            return [
                # Search tools
                {
                    "name": "search_reddit_posts",
                    "description": "Search for posts across Reddit using keywords or phrases. Returns relevant posts with titles, authors, scores, and URLs.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (e.g., 'Python programming', 'machine learning')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of posts to return (default: 10, max: 25)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                },
                
                # Subreddit tools
                {
                    "name": "get_subreddit_posts",
                    "description": "Get the latest posts from a specific subreddit. Returns posts with titles, authors, scores, and engagement metrics.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "subreddit": {
                                "type": "string",
                                "description": "Subreddit name without 'r/' prefix (e.g., 'programming', 'python')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of posts to return (default: 10, max: 25)",
                                "default": 10
                            }
                        },
                        "required": ["subreddit"]
                    }
                },
                {
                    "name": "get_trending_subreddits",
                    "description": "Get currently trending subreddits. Returns popular subreddits with subscriber counts and descriptions.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of trending subreddits to return (default: 10, max: 25)",
                                "default": 10
                            }
                        }
                    }
                },
                
                # Post detail tools
                {
                    "name": "get_post_details",
                    "description": "Get detailed information about a specific Reddit post including full text, author, score, and engagement metrics.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "post_id": {
                                "type": "string",
                                "description": "Reddit post ID (found in post URL)"
                            }
                        },
                        "required": ["post_id"]
                    }
                },
                {
                    "name": "get_post_comments",
                    "description": "Get comments for a specific Reddit post. Returns comment threads with authors, scores, and text content.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "post_id": {
                                "type": "string",
                                "description": "Reddit post ID (found in post URL)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of comments to return (default: 10, max: 50)",
                                "default": 10
                            }
                        },
                        "required": ["post_id"]
                    }
                },
                
                # User tools
                {
                    "name": "get_user_profile",
                    "description": "Get information about a Reddit user including karma, account age, and recent activity.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Reddit username (without 'u/' prefix)"
                            }
                        },
                        "required": ["username"]
                    }
                }
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            """Handle tool calls and route to appropriate tool module."""
            try:
                # Route to appropriate tool module based on tool name
                if name == "search_reddit_posts":
                    return await self.search_tools.search_posts(arguments)
                elif name == "get_subreddit_posts":
                    return await self.subreddits_tools.get_posts(arguments)
                elif name == "get_trending_subreddits":
                    return await self.subreddits_tools.get_trending(arguments)
                elif name == "get_post_details":
                    return await self.posts_tools.get_details(arguments)
                elif name == "get_post_comments":
                    return await self.posts_tools.get_comments(arguments)
                elif name == "get_user_profile":
                    return await self.users_tools.get_profile(arguments)
                else:
                    return [{"error": f"Unknown tool: {name}"}]
                    
            except Exception as e:
                logger.error(f"Error calling tool {name}: {str(e)}")
                return [{"error": f"Tool execution failed: {str(e)}"}]

async def main():
    """Main entry point for the Reddit MCP server."""
    # Initialize the server
    server = RedditMCPServer()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="reddit-mcp",
                server_version="1.0.0",
                capabilities={
                    "tools": {}
                }
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 