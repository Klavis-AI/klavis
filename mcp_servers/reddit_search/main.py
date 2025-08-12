import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from tools import (
    find_relevant_subreddits as find_subreddits_impl,
    search_subreddit_posts as search_posts_impl,
    get_post_and_top_comments as get_comments_impl,
    find_similar_posts_reddit as find_similar_impl,
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server instance - global for MCP dev command
mcp = FastMCP("reddit-mcp-server")

@mcp.tool()
async def reddit_find_subreddits(query: str) -> str:
    """Find relevant subreddits based on a query. Use this first to discover communities when a user does not specify one.
    
    Args:
        query: Search query to find relevant subreddits
        
    Returns:
        JSON string containing relevant subreddits
    """
    try:
        logger.info("Tool call: reddit_find_subreddits(query=%r)", query)
        result = await find_subreddits_impl(query)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error executing reddit_find_subreddits: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def reddit_search_posts(subreddit: str, query: str) -> str:
    """Search for posts in a specific subreddit matching a query.
    
    Args:
        subreddit: Name of the subreddit to search in (without r/ prefix)
        query: Search query to find relevant posts
        
    Returns:
        JSON string containing matching posts
    """
    try:
        logger.info(
            "Tool call: reddit_search_posts(subreddit=%r, query=%r)",
            subreddit,
            query,
        )
        result = await search_posts_impl(subreddit, query)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error executing reddit_search_posts: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def reddit_get_post_comments(post_id: str, subreddit: str) -> str:
    """Get the top comments for a specific Reddit post.
    
    Args:
        post_id: Reddit post ID (without t3_ prefix)
        subreddit: Name of the subreddit containing the post
        
    Returns:
        JSON string containing post and top comments
    """
    try:
        logger.info(
            "Tool call: reddit_get_post_comments(post_id=%r, subreddit=%r)",
            post_id,
            subreddit,
        )
        result = await get_comments_impl(post_id, subreddit)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error executing reddit_get_post_comments: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def reddit_find_similar_posts(post_id: str, limit: int = 10) -> str:
    """Find posts similar to a given Reddit post using semantic matching.
    
    Args:
        post_id: Reddit post ID to find similar posts for
        limit: Maximum number of similar posts to return (default: 10, max: 50)
        
    Returns:
        JSON string containing similar posts
    """
    try:
        logger.info(
            "Tool call: reddit_find_similar_posts(post_id=%r, limit=%r)",
            post_id,
            limit,
        )
        # Ensure limit is within bounds
        limit = max(1, min(50, limit))
        result = await find_similar_impl(post_id, limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception(f"Error executing reddit_find_similar_posts: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print("Starting Reddit MCP Server...")
    mcp.run()
    print("Reddit MCP Server finished.")
