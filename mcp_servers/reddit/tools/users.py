"""
User Tools for Reddit MCP Server
Handles user-related functionality.
"""

import logging
from typing import Dict, Any, List

from .base import RedditMCPClient

logger = logging.getLogger(__name__)

class UsersTools:
    """User tools for Reddit MCP server."""
    
    def __init__(self):
        """Initialize user tools."""
        self.client = RedditMCPClient()
    
    async def get_profile(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get information about a Reddit user."""
        try:
            username = arguments.get('username', '')
            
            if not username:
                return [{"error": "Username is required"}]
            
            logger.info(f"Getting profile for user: {username}")
            response = self.client.get_user_profile(username)
            
            # Extract user profile from Reddit API response
            if 'data' in response:
                user_data = response['data']
                
                profile = {
                    'username': user_data.get('name', ''),
                    'total_karma': user_data.get('total_karma', 0),
                    'link_karma': user_data.get('link_karma', 0),
                    'comment_karma': user_data.get('comment_karma', 0),
                    'created_utc': user_data.get('created_utc', 0),
                    'is_gold': user_data.get('is_gold', False),
                    'is_mod': user_data.get('is_mod', False),
                    'has_verified_email': user_data.get('has_verified_email', False),
                    'hide_from_robots': user_data.get('hide_from_robots', False),
                    'link_karma': user_data.get('link_karma', 0),
                    'comment_karma': user_data.get('comment_karma', 0),
                    'is_suspended': user_data.get('is_suspended', False),
                    'is_employee': user_data.get('is_employee', False),
                    'created': user_data.get('created', 0),
                    'url': f"https://reddit.com/user/{user_data.get('name', '')}",
                    'subreddit': {
                        'title': user_data.get('subreddit', {}).get('title', ''),
                        'public_description': user_data.get('subreddit', {}).get('public_description', ''),
                        'subscribers': user_data.get('subreddit', {}).get('subscribers', 0)
                    } if user_data.get('subreddit') else None
                }
                
                return [profile]
            else:
                return [{"error": "User not found or invalid response"}]
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return [{"error": f"Failed to get user profile: {str(e)}"}] 