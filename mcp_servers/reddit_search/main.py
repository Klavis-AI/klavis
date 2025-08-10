import logging
import json
from mcp.server.fastmcp import FastMCP
from tools import (
    find_relevant_subreddits as find_subreddits_impl,
    search_subreddit_posts as search_posts_impl,
    get_post_and_top_comments as get_comments_impl,
    find_similar_posts_reddit as find_similar_impl,
)

logger = logging.getLogger(__name__)
mcp = FastMCP()

# define the tools
@mcp.tool()
async def find_relevant_subreddits(query: str) -> str:
    """
    Finds relevant subreddits based on a query.
    Use this first to discover communities when a user does not specify one.
    """
    logger.info(f"Executing tool 'find_subreddits' with query: '{query}'")   

    subreddits = await find_subreddits_impl(query)
    return json.dumps(subreddits, indent=2)


@mcp.tool()
async def search_subreddit_posts(subreddit: str, query: str) -> str:
    """
    Searches a subreddit for posts matching a query.
    """
    logger.info(f"Executing tool 'search_subreddit_posts' with subreddit: '{subreddit}' and query: '{query}'")
    posts = await search_posts_impl(subreddit, query)
    return json.dumps(posts, indent=2)

@mcp.tool()
async def get_subreddit_post_comments(subreddit: str, post_id: str) -> str:
    """
    Gets the comments for a specific post in a subreddit.
    """
    logger.info(f"Executing tool 'get_subreddit_post_comments' with subreddit: '{subreddit}' and post_id: '{post_id}'")
    comments = await get_comments_impl(post_id, subreddit)
    return json.dumps(comments, indent=2)


@mcp.tool()
async def find_similar_posts_reddit(post_id: str, limit: int = 10) -> str:
    """
    Finds posts similar to a given Reddit post using the post's title as the query.
    Searches in the same subreddit first, then site-wide, and ranks semantically.
    """
    logger.info(f"Executing tool 'find_similar_posts_reddit' with post_id: '{post_id}', limit: {limit}")
    results = await find_similar_impl(post_id, limit)
    return json.dumps(results, indent=2)

def main():
    print("Hello from reddit-search!")


if __name__ == "__main__":
    main()
    mcp.run()
