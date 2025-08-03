"""
Base Reddit MCP Client
Handles authentication and API requests to Reddit.
"""

import logging
import os
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Reddit API endpoints
REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"

class RedditMCPClient:
    """Reddit API client for MCP server."""
    
    def __init__(self):
        """Initialize Reddit API client with credentials."""
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "klavis-reddit-mcp/1.0")
        self.access_token = None
        
        if not all([self.client_id, self.client_secret]):
            raise ValueError("Missing required Reddit API credentials (client_id and client_secret) in environment variables")
    
    def authenticate(self):
        """Authenticate with Reddit API using client credentials flow."""
        auth_data = {
            'grant_type': 'client_credentials'
        }
        logger.info("Attempting authentication with client credentials")
        response = requests.post(
            REDDIT_AUTH_URL,
            data=auth_data,
            auth=(self.client_id, self.client_secret),
            headers={'User-Agent': self.user_agent}
        )
        logger.info(f"Authentication response status: {response.status_code}")
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response data keys: {list(response_data.keys())}")
            if 'access_token' in response_data:
                self.access_token = response_data['access_token']
                logger.info("Successfully authenticated with Reddit API using client credentials")
                logger.info(f"Token type: {response_data.get('token_type', 'unknown')}")
                logger.info(f"Token length: {len(self.access_token) if self.access_token else 0}")
                logger.info(f"Token expires in: {response_data.get('expires_in', 'unknown')} seconds")
            else:
                logger.error(f"No access_token in response: {response_data}")
                raise Exception(f"No access_token in response: {response_data}")
        else:
            logger.error(f"Authentication failed: {response.status_code} - {response.text}")
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make authenticated request to Reddit API."""
        if not self.access_token:
            self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': self.user_agent
        }
        
        url = f"{REDDIT_API_BASE}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 401:
            # Token expired, re-authenticate
            logger.info("Token expired, re-authenticating...")
            self.authenticate()
            headers['Authorization'] = f'Bearer {self.access_token}'
            response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 429:
            raise Exception("Rate limit exceeded. Please wait before making more requests.")
        elif response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        return response.json()
    
    def search_posts(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for posts across Reddit."""
        params = {
            'q': query,
            'limit': min(limit, 25),
            'type': 'link',
            'sort': 'relevance'
        }
        return self.make_request('/search', params)
    
    def get_subreddit_posts(self, subreddit: str, limit: int = 10) -> Dict[str, Any]:
        """Get posts from a specific subreddit."""
        params = {
            'limit': min(limit, 25)
        }
        return self.make_request(f'/r/{subreddit}/hot', params)
    
    def get_trending_subreddits(self, limit: int = 10) -> Dict[str, Any]:
        """Get trending subreddits."""
        params = {
            'limit': min(limit, 25)
        }
        return self.make_request('/subreddits/popular', params)
    
    def get_post_details(self, post_id: str) -> Dict[str, Any]:
        """Get details of a specific post."""
        return self.make_request(f'/comments/{post_id}')
    
    def get_post_comments(self, post_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get comments for a specific post."""
        params = {
            'limit': min(limit, 50)
        }
        return self.make_request(f'/comments/{post_id}', params)
    
    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Get user profile information."""
        return self.make_request(f'/user/{username}/about') 