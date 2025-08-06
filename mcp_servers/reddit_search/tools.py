import os 
import logging
import requests

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
