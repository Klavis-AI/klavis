import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)
mcp = FastMCP()

@mcp.tool()
async def find_subreddit(query: str) -> str :
    """
    Finds relevant subreddits based on a query.
    Use this first to discover communities when a user does not specify one.
    """
    logger.info(f"Executing tool 'find_subreddits' with query: '{query}'")   

    # TODO: Implement the logic to find relevant subreddits.
    return "Subreddit search not implemented yet."

@mcp.tool()
async def search_subreddit_posts(subreddit: str, query: str) -> str:
    """
    Searches a subreddit for posts matching a query.
    """
    logger.info(f"Executing tool 'search_subreddit_posts' with subreddit: '{subreddit}' and query: '{query}'")
    return "Subreddit post search not implemented yet."

@mcp.tool()
async def get_subreddit_post_comments(subreddit: str, post_id: str) -> str:
    """
    Gets the comments for a specific post in a subreddit.
    """
    logger.info(f"Executing tool 'get_subreddit_post_comments' with subreddit: '{subreddit}' and post_id: '{post_id}'")
    return "Subreddit post comments not implemented yet."

def main():
    print("Hello from reddit-search!")


if __name__ == "__main__":
    main()
    mcp.run()
