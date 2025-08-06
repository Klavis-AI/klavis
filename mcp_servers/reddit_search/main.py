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

    # This log message will appear in our terminal every time the AI uses this tool.
    logger.info(f"Executing tool 'find_subreddits' with query: '{query}'")   

    # This is where we would call the Reddit API to find relevant subreddits.
    # For now, we'll just return a placeholder response.
    
    return "Subreddit search not implemented yet."


def main():
    print("Hello from reddit-search!")


if __name__ == "__main__":
    main()
