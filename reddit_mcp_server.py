#!/usr/bin/env python3
"""
Reddit MCP Server

A Model Context Protocol (MCP) server that provides atomic tools for interacting with Reddit's API.
This server enables AI agents to search, read, and analyze Reddit content through natural language commands.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import praw
from dotenv import load_dotenv
from mcp import ServerSession, StdioServerParameters
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reddit API configuration
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MCP_Reddit_Server/1.0")

# Initialize Reddit client
reddit_client = None
if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
    try:
        reddit_client = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        logger.info("Reddit client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {e}")
        reddit_client = None
else:
    logger.warning("Reddit API credentials not found. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.")


class RedditMCPServer:
    """Reddit MCP Server implementation with atomic tools for Reddit API interactions."""

    def __init__(self):
        self.server = Server("reddit-mcp-server")
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List all available tools."""
            tools = [
                Tool(
                    name="search_reddit_posts",
                    description="Search for posts across Reddit or within specific subreddits. Use this when the user wants to find posts about a topic, keyword, or within a specific community. Returns a list of posts with titles, URLs, scores, and basic metadata.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search terms to find posts about"
                            },
                            "subreddit": {
                                "type": "string",
                                "description": "Optional: Limit search to specific subreddit (without r/ prefix)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10, max: 100)",
                                "default": 10
                            },
                            "time_filter": {
                                "type": "string",
                                "description": "Time period for search: hour, day, week, month, year, all",
                                "enum": ["hour", "day", "week", "month", "year", "all"],
                                "default": "all"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_post_details",
                    description="Get detailed information about a specific Reddit post including comments, scores, and metadata. Use this when the user wants to see the full content of a post, read comments, or get detailed information about a specific post.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "post_id": {
                                "type": "string",
                                "description": "Reddit post ID (e.g., t3_abc123) or full Reddit URL"
                            }
                        },
                        "required": ["post_id"]
                    }
                ),
                Tool(
                    name="list_subreddits",
                    description="Get information about subreddits, including trending topics and community information. Use this when the user wants to discover subreddits, find communities about a topic, or get information about specific subreddits.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Optional: Search for specific subreddits by name or topic"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="get_user_profile",
                    description="Get information about a Reddit user and their recent activity. Use this when the user wants to see a user's profile, recent posts, karma, or activity history.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Reddit username (with or without u/ prefix)"
                            }
                        },
                        "required": ["username"]
                    }
                ),
                Tool(
                    name="search_comments",
                    description="Search for comments across Reddit. Use this when the user wants to find specific comments, discussions, or responses about a topic.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search terms to find comments about"
                            },
                            "subreddit": {
                                "type": "string",
                                "description": "Optional: Limit search to specific subreddit (without r/ prefix)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_trending_posts",
                    description="Get trending posts from a specific subreddit. Use this when the user wants to see the most popular posts from a community, trending topics, or top posts from a subreddit.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subreddit": {
                                "type": "string",
                                "description": "Subreddit name (without r/ prefix)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return (default: 10)",
                                "default": 10
                            },
                            "time_filter": {
                                "type": "string",
                                "description": "Time period: hour, day, week, month, year, all",
                                "enum": ["hour", "day", "week", "month", "year", "all"],
                                "default": "day"
                            }
                        },
                        "required": ["subreddit"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "search_reddit_posts":
                    return await self.search_reddit_posts(arguments)
                elif name == "get_post_details":
                    return await self.get_post_details(arguments)
                elif name == "list_subreddits":
                    return await self.list_subreddits(arguments)
                elif name == "get_user_profile":
                    return await self.get_user_profile(arguments)
                elif name == "search_comments":
                    return await self.search_comments(arguments)
                elif name == "get_trending_posts":
                    return await self.get_trending_posts(arguments)
                else:
                    return CallToolResult(
                        content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                        isError=True
                    )
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return CallToolResult(
                    content=[{"type": "text", "text": f"Error executing {name}: {str(e)}"}],
                    isError=True
                )

    async def search_reddit_posts(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for posts across Reddit or within specific subreddits."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        query = arguments.get("query", "")
        subreddit = arguments.get("subreddit")
        limit = min(arguments.get("limit", 10), 100)
        time_filter = arguments.get("time_filter", "all")

        try:
            if subreddit:
                # Search within specific subreddit
                subreddit_obj = reddit_client.subreddit(subreddit)
                search_results = subreddit_obj.search(query, limit=limit, time_filter=time_filter)
            else:
                # Search across all of Reddit
                search_results = reddit_client.subreddit("all").search(query, limit=limit, time_filter=time_filter)

            posts = []
            for post in search_results:
                posts.append({
                    "title": post.title,
                    "url": f"https://reddit.com{post.permalink}",
                    "subreddit": post.subreddit.display_name,
                    "author": str(post.author) if post.author else "[deleted]",
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "selftext": post.selftext[:500] + "..." if len(post.selftext) > 500 else post.selftext,
                    "is_self": post.is_self,
                    "domain": post.domain
                })

            result_text = f"Found {len(posts)} posts for query '{query}'"
            if subreddit:
                result_text += f" in r/{subreddit}"
            result_text += f" (time filter: {time_filter}):\n\n"

            for i, post in enumerate(posts, 1):
                result_text += f"{i}. **{post['title']}**\n"
                result_text += f"   Subreddit: r/{post['subreddit']}\n"
                result_text += f"   Author: u/{post['author']}\n"
                result_text += f"   Score: {post['score']} (↑{post['upvote_ratio']:.1%})\n"
                result_text += f"   Comments: {post['num_comments']}\n"
                result_text += f"   URL: {post['url']}\n"
                if post['selftext']:
                    result_text += f"   Content: {post['selftext']}\n"
                result_text += "\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error searching Reddit posts: {str(e)}"}],
                isError=True
            )

    async def get_post_details(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get detailed information about a specific Reddit post."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        post_id = arguments.get("post_id", "")
        
        try:
            # Extract post ID from URL if full URL is provided
            if post_id.startswith("http"):
                # Parse URL to extract post ID
                parsed_url = urlparse(post_id)
                path_parts = parsed_url.path.split("/")
                if "comments" in path_parts:
                    comment_index = path_parts.index("comments")
                    if len(path_parts) > comment_index + 1:
                        post_id = path_parts[comment_index + 1]
            
            # Remove t3_ prefix if present
            if post_id.startswith("t3_"):
                post_id = post_id[3:]

            post = reddit_client.submission(id=post_id)
            
            # Get comments (limit to first 10 top-level comments)
            post.comment_sort = "top"
            post.comments.replace_more(limit=0)  # Don't load MoreComments objects
            
            result_text = f"**Post Details:**\n\n"
            result_text += f"**Title:** {post.title}\n"
            result_text += f"**Subreddit:** r/{post.subreddit.display_name}\n"
            result_text += f"**Author:** u/{post.author if post.author else '[deleted]'}\n"
            result_text += f"**Score:** {post.score} (↑{post.upvote_ratio:.1%})\n"
            result_text += f"**Comments:** {post.num_comments}\n"
            result_text += f"**Created:** {post.created_utc}\n"
            result_text += f"**URL:** {post.url}\n"
            result_text += f"**Permalink:** https://reddit.com{post.permalink}\n\n"
            
            if post.selftext:
                result_text += f"**Content:**\n{post.selftext}\n\n"
            
            result_text += f"**Top Comments:**\n"
            for i, comment in enumerate(post.comments[:10], 1):
                result_text += f"{i}. **u/{comment.author if comment.author else '[deleted]'}** (Score: {comment.score})\n"
                result_text += f"   {comment.body[:200]}{'...' if len(comment.body) > 200 else ''}\n\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error getting post details: {str(e)}"}],
                isError=True
            )

    async def list_subreddits(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get information about subreddits."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)

        try:
            if query:
                # Search for subreddits
                subreddits = list(reddit_client.subreddits.search(query, limit=limit))
            else:
                # Get popular subreddits
                subreddits = list(reddit_client.subreddits.popular(limit=limit))

            result_text = f"Found {len(subreddits)} subreddits"
            if query:
                result_text += f" matching '{query}'"
            result_text += ":\n\n"

            for i, subreddit in enumerate(subreddits, 1):
                result_text += f"{i}. **r/{subreddit.display_name}**\n"
                result_text += f"   Subscribers: {subreddit.subscribers:,}\n"
                result_text += f"   Active users: {subreddit.active_user_count}\n"
                result_text += f"   Description: {subreddit.public_description[:200]}{'...' if len(subreddit.public_description) > 200 else ''}\n"
                result_text += f"   URL: https://reddit.com/r/{subreddit.display_name}\n\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error listing subreddits: {str(e)}"}],
                isError=True
            )

    async def get_user_profile(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get information about a Reddit user."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        username = arguments.get("username", "")
        
        # Remove u/ prefix if present
        if username.startswith("u/"):
            username = username[2:]

        try:
            user = reddit_client.redditor(username)
            
            # Get recent submissions and comments
            recent_submissions = list(user.submissions.new(limit=5))
            recent_comments = list(user.comments.new(limit=5))

            result_text = f"**User Profile: u/{username}**\n\n"
            result_text += f"**Karma:**\n"
            result_text += f"  - Post Karma: {user.link_karma:,}\n"
            result_text += f"  - Comment Karma: {user.comment_karma:,}\n"
            result_text += f"**Account Created:** {user.created_utc}\n\n"
            
            if hasattr(user, 'is_gold') and user.is_gold:
                result_text += "**Gold Member:** Yes\n\n"
            
            result_text += f"**Recent Submissions:**\n"
            for i, submission in enumerate(recent_submissions, 1):
                result_text += f"{i}. **{submission.title}**\n"
                result_text += f"   r/{submission.subreddit.display_name} - Score: {submission.score}\n"
                result_text += f"   https://reddit.com{submission.permalink}\n\n"
            
            result_text += f"**Recent Comments:**\n"
            for i, comment in enumerate(recent_comments, 1):
                result_text += f"{i}. In r/{comment.subreddit.display_name} (Score: {comment.score})\n"
                result_text += f"   {comment.body[:150]}{'...' if len(comment.body) > 150 else ''}\n"
                result_text += f"   https://reddit.com{comment.permalink}\n\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error getting user profile: {str(e)}"}],
                isError=True
            )

    async def search_comments(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for comments across Reddit."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        query = arguments.get("query", "")
        subreddit = arguments.get("subreddit")
        limit = arguments.get("limit", 10)

        try:
            if subreddit:
                # Search comments in specific subreddit
                subreddit_obj = reddit_client.subreddit(subreddit)
                search_results = subreddit_obj.search(query, limit=limit, sort="comments")
            else:
                # Search comments across all of Reddit
                search_results = reddit_client.subreddit("all").search(query, limit=limit, sort="comments")

            comments = []
            for post in search_results:
                post.comment_sort = "top"
                post.comments.replace_more(limit=0)
                
                for comment in post.comments[:3]:  # Get top 3 comments from each post
                    comments.append({
                        "body": comment.body,
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "score": comment.score,
                        "subreddit": post.subreddit.display_name,
                        "post_title": post.title,
                        "permalink": f"https://reddit.com{comment.permalink}",
                        "created_utc": comment.created_utc
                    })

            # Sort by score and limit results
            comments.sort(key=lambda x: x["score"], reverse=True)
            comments = comments[:limit]

            result_text = f"Found {len(comments)} comments for query '{query}'"
            if subreddit:
                result_text += f" in r/{subreddit}"
            result_text += ":\n\n"

            for i, comment in enumerate(comments, 1):
                result_text += f"{i}. **u/{comment['author']}** in r/{comment['subreddit']} (Score: {comment['score']})\n"
                result_text += f"   Post: {comment['post_title']}\n"
                result_text += f"   Comment: {comment['body'][:300]}{'...' if len(comment['body']) > 300 else ''}\n"
                result_text += f"   URL: {comment['permalink']}\n\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error searching comments: {str(e)}"}],
                isError=True
            )

    async def get_trending_posts(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get trending posts from a specific subreddit."""
        if not reddit_client:
            return CallToolResult(
                content=[{"type": "text", "text": "Reddit API credentials not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."}],
                isError=True
            )

        subreddit = arguments.get("subreddit", "")
        limit = arguments.get("limit", 10)
        time_filter = arguments.get("time_filter", "day")

        try:
            subreddit_obj = reddit_client.subreddit(subreddit)
            
            # Get top posts for the specified time period
            posts = list(subreddit_obj.top(time_filter=time_filter, limit=limit))

            result_text = f"**Top posts from r/{subreddit} ({time_filter}):**\n\n"

            for i, post in enumerate(posts, 1):
                result_text += f"{i}. **{post.title}**\n"
                result_text += f"   Author: u/{post.author if post.author else '[deleted]'}\n"
                result_text += f"   Score: {post.score:,} (↑{post.upvote_ratio:.1%})\n"
                result_text += f"   Comments: {post.num_comments}\n"
                result_text += f"   URL: {post.url}\n"
                result_text += f"   Permalink: https://reddit.com{post.permalink}\n"
                if post.selftext:
                    result_text += f"   Content: {post.selftext[:200]}{'...' if len(post.selftext) > 200 else ''}\n"
                result_text += "\n"

            return CallToolResult(content=[{"type": "text", "text": result_text}])

        except Exception as e:
            return CallToolResult(
                content=[{"type": "text", "text": f"Error getting trending posts: {str(e)}"}],
                isError=True
            )

    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream=read_stream,
                write_stream=write_stream,
                initialization_options=InitializationOptions(
                    server_name="reddit-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Main entry point."""
    server = RedditMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 