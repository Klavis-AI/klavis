import os 
import logging
import requests
from typing import Dict,List, TypedDict

from dotenv import load_dotenv

load_dotenv()

logger =  logging.getLogger(__name__)

# load the reddit api key
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

# base api urls
REDDIT_API_BASE = "https://oauth.reddit.com"
REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

# cached access token
_ACCESS_TOKEN = None

def _get_reddit_auth_header() -> dict[str, str]:
    """
    Authenticates with the Reddit API and returns the required authorization header.
    It cleverly caches the access token in memory.
    """
    global _access_token

    # if the access token is already cached, return it
    if _access_token:
        return {"Authorization": f"Bearer {_access_token}"}

    # if the client_ID and client_secret are not set, raise an error
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")
    
    auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": "klavis.ai.mcp.server.test/0.1"}

    logger.info("No cached token found. Requesting new Reddit API access token...")

    # make the post request to get the access token
    response = requests.post(REDDIT_TOKEN_URL, auth=auth, data=data, headers=headers)
    response.raise_for_status()

    token_data = response.json()
    _access_token = token_data["access_token"]
    logger.info("Successfully obtained and cached new Reddit API access token.")

    return {"Authorization": f"Bearer {_ACCESS_TOKEN}"}

# define the structure of the returned data
class SubredditInfo(TypedDict):
    """Structured data for a single subreddit."""
    name: str
    subscriber_count: int
    description: str

class PostInfo(TypedDict):
    """Structured data for a Reddit post summary."""
    id: str
    subreddit: str
    title: str
    score: int
    url: str
    comment_count: int

class CommentInfo(TypedDict):
    """Structured data for a single comment."""
    author: str
    text: str
    score: int

class PostDetails(TypedDict):
    """The combined structure for a post and its top comments."""
    title: str
    author: str
    text: str
    score: int
    top_comments: List[CommentInfo]

# implement the functions utilised by the tools
async def find_relevant_subreddits(query: str) -> List[SubredditInfo]:
    """ find subreddits that are relevant to the query and clean up the data """
    header = _get_reddit_auth_header()
    params = {"query": query, "limit": 10}

    logger.info(f"Making API call to Reddit to find subreddits for query: '{query}'")
    response = requests.get(f"{REDDIT_API_BASE}/subreddits/search", headers=header, params=params)
    response.raise_for_status()

    subreddits = response.json()["subreddits"]
    # We loop through the raw results and build a clean list of our SubredditInfo objects.
    return [
        SubredditInfo(
            name=sub["name"],
            subscriber_count=sub["subscriber_count"],
            description=sub.get("public_description", "No description provided."),
        )
        for sub in subreddits
    ]

async def search_subreddit_posts(subreddit: str, query: str) -> List[PostInfo]:
    """ search for posts in a subreddit and clean up the data """
    headers = _get_reddit_auth_header()
    params = {"q": query, "limit": 10, "restrict_sr": "true"}

    logger.info(f"making API call to search for posts in subreddit: '{subreddit}' with query: '{query}'")
    response = requests.get(f"{REDDIT_API_BASE}/r/{subreddit}/search", headers=headers, params=params)
    response.raise_for_status()

    posts = response.json()["data"]["children"]

    return [
        PostInfo(
            id=post["data"]["id"],
            subreddit=post["data"]["subreddit"],
            title=post["data"]["title"],
            score=post["data"]["score"],
            url=post["data"]["url"],
            comment_count=post["data"]["num_comments"],
        )
        for post in posts
    ]