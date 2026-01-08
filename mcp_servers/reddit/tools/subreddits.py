"""
Subreddit Tools for Reddit MCP Server
Handles subreddit-related functionality.
"""

import logging
from typing import Dict, Any, List

from .base import RedditMCPClient

logger = logging.getLogger(__name__)

class SubredditsTools:
    """Subreddit tools for Reddit MCP server."""
    
    def __init__(self):
        """Initialize subreddit tools."""
        self.client = RedditMCPClient()
    
    async def get_posts(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get the latest posts from a specific subreddit."""
        try:
            subreddit = arguments.get('subreddit', '')
            limit = arguments.get('limit', 10)
            
            if not subreddit:
                return [{"error": "Subreddit name is required"}]
            
            logger.info(f"Getting posts from r/{subreddit}")
            response = self.client.get_subreddit_posts(subreddit, limit)
            
            # Extract posts from Reddit API response
            posts = []
            if 'data' in response and 'children' in response['data']:
                for child in response['data']['children']:
                    post_data = child['data']
                    posts.append({
                        'title': post_data.get('title', ''),
                        'author': post_data.get('author', ''),
                        'score': post_data.get('score', 0),
                        'subreddit': post_data.get('subreddit', ''),
                        'num_comments': post_data.get('num_comments', 0),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}",
                        'created_utc': post_data.get('created_utc', 0),
                        'selftext': post_data.get('selftext', '')[:500] + '...' if len(post_data.get('selftext', '')) > 500 else post_data.get('selftext', '')
                    })
            
            return [{
                'posts': posts,
                'subreddit': subreddit,
                'total_found': len(posts)
            }]
            
        except Exception as e:
            logger.error(f"Error getting subreddit posts: {str(e)}")
            return [{"error": f"Failed to get posts: {str(e)}"}]
    
    async def get_trending(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get currently trending subreddits."""
        try:
            limit = arguments.get('limit', 10)
            
            logger.info("Getting trending subreddits")
            response = self.client.get_trending_subreddits(limit)
            
            # Extract subreddits from Reddit API response
            subreddits = []
            if 'data' in response and 'children' in response['data']:
                for child in response['data']['children']:
                    subreddit_data = child['data']
                    subreddits.append({
                        'name': subreddit_data.get('display_name', ''),
                        'title': subreddit_data.get('title', ''),
                        'description': subreddit_data.get('public_description', ''),
                        'subscribers': subreddit_data.get('subscribers', 0),
                        'active_users': subreddit_data.get('active_user_count', 0),
                        'url': f"https://reddit.com/r/{subreddit_data.get('display_name', '')}",
                        'created_utc': subreddit_data.get('created_utc', 0),
                        'over18': subreddit_data.get('over18', False)
                    })
            
            return [{
                'subreddits': subreddits,
                'total_found': len(subreddits)
            }]
            
        except Exception as e:
            logger.error(f"Error getting trending subreddits: {str(e)}")
            return [{"error": f"Failed to get trending subreddits: {str(e)}"}] 