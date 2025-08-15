#!/usr/bin/env python3
"""
Reddit MCP Server

A Model Context Protocol server for Reddit integration.
Provides tools for browsing subreddits, searching posts, getting comments,
posting content, and managing Reddit interactions.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"), override=False)

import praw
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    INVALID_REQUEST,
    INTERNAL_ERROR
)
from pydantic import AnyUrl

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("reddit-mcp-server")

class RedditConfig:
    """Configuration for Reddit API."""
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "MCP-Reddit-Server/1.0")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        
        # Validate required credentials
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Missing required Reddit credentials. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")

class RedditClient:
    """Reddit API client wrapper."""
    
    def __init__(self, config: RedditConfig):
        self.config = config
        self._reddit = None
        
    @property
    def reddit(self) -> praw.Reddit:
        """Get or create Reddit instance."""
        if self._reddit is None:
            auth_params = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "user_agent": self.config.user_agent,
            }
            
            # Add username/password for script app authentication if provided
            if self.config.username and self.config.password:
                auth_params.update({
                    "username": self.config.username,
                    "password": self.config.password
                })
            
            self._reddit = praw.Reddit(**auth_params)
            
        return self._reddit

    def get_subreddit_posts(self, subreddit_name: str, sort_by: str = "hot", limit: int = 10) -> List[Dict[str, Any]]:
        """Get posts from a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            if sort_by == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort_by == "new":
                posts = subreddit.new(limit=limit)
            elif sort_by == "top":
                posts = subreddit.top(limit=limit)
            elif sort_by == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                posts = subreddit.hot(limit=limit)
            
            results = []
            for post in posts:
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author) if post.author else "[deleted]",
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "selftext": post.selftext[:500] if post.selftext else "",  # Truncate long text
                    "is_self": post.is_self,
                    "over_18": post.over_18,
                    "spoiler": post.spoiler,
                    "locked": post.locked,
                    "subreddit": str(post.subreddit),
                    "flair_text": post.link_flair_text,
                }
                results.append(post_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting subreddit posts: {e}")
            return []

    def search_posts(self, query: str, subreddit_name: Optional[str] = None, sort: str = "relevance", time_filter: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Search for posts."""
        try:
            if subreddit_name:
                search_results = self.reddit.subreddit(subreddit_name).search(
                    query, sort=sort, time_filter=time_filter, limit=limit
                )
            else:
                search_results = self.reddit.subreddit("all").search(
                    query, sort=sort, time_filter=time_filter, limit=limit
                )
            
            results = []
            for post in search_results:
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "author": str(post.author) if post.author else "[deleted]",
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "selftext": post.selftext[:500] if post.selftext else "",
                    "is_self": post.is_self,
                    "subreddit": str(post.subreddit),
                    "flair_text": post.link_flair_text,
                }
                results.append(post_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching posts: {e}")
            return []

    def get_post_comments(self, post_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get comments for a specific post."""
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "more comments" objects
            
            def extract_comment_data(comment) -> Dict[str, Any]:
                return {
                    "id": comment.id,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body,
                    "created_utc": comment.created_utc,
                    "score": comment.score,
                    "is_submitter": comment.is_submitter,
                    "replies": [extract_comment_data(reply) for reply in comment.replies[:5]]  # Limit replies
                }
            
            post_data = {
                "id": submission.id,
                "title": submission.title,
                "author": str(submission.author) if submission.author else "[deleted]",
                "created_utc": submission.created_utc,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "selftext": submission.selftext,
                "url": submission.url,
                "permalink": f"https://reddit.com{submission.permalink}",
                "comments": [extract_comment_data(comment) for comment in submission.comments[:limit]]
            }
            
            return post_data
            
        except Exception as e:
            logger.error(f"Error getting post comments: {e}")
            return {}

    def get_user_posts(self, username: str, sort: str = "new", limit: int = 10) -> List[Dict[str, Any]]:
        """Get posts from a specific user."""
        try:
            user = self.reddit.redditor(username)
            
            if sort == "new":
                posts = user.submissions.new(limit=limit)
            elif sort == "hot":
                posts = user.submissions.hot(limit=limit)
            elif sort == "top":
                posts = user.submissions.top(limit=limit)
            else:
                posts = user.submissions.new(limit=limit)
            
            results = []
            for post in posts:
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "url": post.url,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "selftext": post.selftext[:500] if post.selftext else "",
                    "subreddit": str(post.subreddit),
                }
                results.append(post_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting user posts: {e}")
            return []

    def get_subreddit_info(self, subreddit_name: str) -> Dict[str, Any]:
        """Get information about a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            return {
                "name": subreddit.display_name,
                "title": subreddit.title,
                "description": subreddit.public_description,
                "subscribers": subreddit.subscribers,
                "created_utc": subreddit.created_utc,
                "over18": subreddit.over18,
                "description_html": subreddit.description_html[:1000] if subreddit.description_html else "",
                "rules": [{"short_name": rule.short_name, "description": rule.description} for rule in subreddit.rules()[:10]],
                "url": f"https://reddit.com/r/{subreddit.display_name}"
            }
            
        except Exception as e:
            logger.error(f"Error getting subreddit info: {e}")
            return {}

    def submit_post(self, subreddit_name: str, title: str, content: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """Submit a new post to a subreddit."""
        if not (self.config.username and self.config.password):
            return {"error": "Authentication required for posting. Please provide REDDIT_USERNAME and REDDIT_PASSWORD."}
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            if url:
                # Link post
                submission = subreddit.submit(title=title, url=url)
            else:
                # Text post
                submission = subreddit.submit(title=title, selftext=content or "")
            
            return {
                "id": submission.id,
                "title": submission.title,
                "url": submission.url,
                "permalink": f"https://reddit.com{submission.permalink}",
                "created_utc": submission.created_utc,
                "subreddit": str(submission.subreddit)
            }
            
        except Exception as e:
            logger.error(f"Error submitting post: {e}")
            return {"error": str(e)}

# Initialize Reddit client
config = RedditConfig()
reddit_client = RedditClient(config)

# Create MCP server
server = Server("reddit-mcp-server")

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available Reddit resources."""
    return [
        Resource(
            uri=AnyUrl("reddit://subreddits"),
            name="Popular Subreddits",
            description="Browse popular subreddits",
            mimeType="application/json",
        ),
        Resource(
            uri=AnyUrl("reddit://search"),
            name="Search Posts",
            description="Search Reddit posts",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a specific Reddit resource."""
    if str(uri) == "reddit://subreddits":
        # Return some popular subreddits
        popular_subs = ["python", "programming", "technology", "news", "worldnews", "askreddit", "todayilearned"]
        return json.dumps({"popular_subreddits": popular_subs})
    elif str(uri) == "reddit://search":
        return json.dumps({"message": "Use the search_posts tool to search Reddit"})
    else:
        raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available Reddit tools."""
    return [
        Tool(
            name="get_subreddit_posts",
            description="Get posts from a specific subreddit",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Name of the subreddit (without r/)",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["hot", "new", "top", "rising"],
                        "default": "hot",
                        "description": "How to sort the posts",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "Number of posts to retrieve",
                    },
                },
                "required": ["subreddit"],
            },
        ),
        Tool(
            name="search_posts",
            description="Search for posts across Reddit or within a specific subreddit",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Optional: limit search to specific subreddit (without r/)",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["relevance", "hot", "top", "new", "comments"],
                        "default": "relevance",
                        "description": "How to sort search results",
                    },
                    "time_filter": {
                        "type": "string",
                        "enum": ["all", "year", "month", "week", "day", "hour"],
                        "default": "all",
                        "description": "Time period to search within",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "Number of results to return",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_post_comments",
            description="Get comments for a specific Reddit post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "string",
                        "description": "Reddit post ID",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 50,
                        "description": "Maximum number of top-level comments to retrieve",
                    },
                },
                "required": ["post_id"],
            },
        ),
        Tool(
            name="get_user_posts",
            description="Get posts from a specific Reddit user",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Reddit username (without u/)",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["new", "hot", "top"],
                        "default": "new",
                        "description": "How to sort the user's posts",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "Number of posts to retrieve",
                    },
                },
                "required": ["username"],
            },
        ),
        Tool(
            name="get_subreddit_info",
            description="Get detailed information about a subreddit",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Name of the subreddit (without r/)",
                    },
                },
                "required": ["subreddit"],
            },
        ),
        Tool(
            name="submit_post",
            description="Submit a new post to a subreddit (requires authentication)",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Name of the subreddit (without r/)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Post title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Post content (for text posts)",
                    },
                    "url": {
                        "type": "string",
                        "description": "URL (for link posts)",
                    },
                },
                "required": ["subreddit", "title"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_subreddit_posts":
            posts = reddit_client.get_subreddit_posts(
                subreddit_name=arguments["subreddit"],
                sort_by=arguments.get("sort_by", "hot"),
                limit=arguments.get("limit", 10)
            )
            return [TextContent(type="text", text=json.dumps(posts, indent=2))]
        
        elif name == "search_posts":
            results = reddit_client.search_posts(
                query=arguments["query"],
                subreddit_name=arguments.get("subreddit"),
                sort=arguments.get("sort", "relevance"),
                time_filter=arguments.get("time_filter", "all"),
                limit=arguments.get("limit", 10)
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]
        
        elif name == "get_post_comments":
            post_data = reddit_client.get_post_comments(
                post_id=arguments["post_id"],
                limit=arguments.get("limit", 50)
            )
            return [TextContent(type="text", text=json.dumps(post_data, indent=2))]
        
        elif name == "get_user_posts":
            posts = reddit_client.get_user_posts(
                username=arguments["username"],
                sort=arguments.get("sort", "new"),
                limit=arguments.get("limit", 10)
            )
            return [TextContent(type="text", text=json.dumps(posts, indent=2))]
        
        elif name == "get_subreddit_info":
            info = reddit_client.get_subreddit_info(
                subreddit_name=arguments["subreddit"]
            )
            return [TextContent(type="text", text=json.dumps(info, indent=2))]
        
        elif name == "submit_post":
            result = reddit_client.submit_post(
                subreddit_name=arguments["subreddit"],
                title=arguments["title"],
                content=arguments.get("content"),
                url=arguments.get("url")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    logger.info("Starting Reddit MCP Server")
    logger.info(f"Client ID configured: {'Yes' if config.client_id else 'No'}")
    logger.info(f"Authentication enabled: {'Yes' if config.username else 'No'}")
    
    try:
        reddit = reddit_client.reddit
        logger.info("Reddit client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Reddit client: {e}")
        raise
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.debug(f"Starting server with read_stream: {read_stream}, write_stream: {write_stream}")
            await server.run(read_stream, write_stream, initialization_options={})
    except Exception as e:
        logger.error(f"Server runtime error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)