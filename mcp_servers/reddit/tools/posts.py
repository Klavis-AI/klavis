"""
Post Tools for Reddit MCP Server
Handles post-related functionality.
"""

import logging
from typing import Dict, Any, List

from .base import RedditMCPClient

logger = logging.getLogger(__name__)

class PostsTools:
    """Post tools for Reddit MCP server."""
    
    def __init__(self):
        """Initialize post tools."""
        self.client = RedditMCPClient()
    
    async def get_details(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get detailed information about a specific Reddit post."""
        try:
            post_id = arguments.get('post_id', '')
            
            if not post_id:
                return [{"error": "Post ID is required"}]
            
            logger.info(f"Getting details for post: {post_id}")
            response = self.client.get_post_details(post_id)
            
            # Extract post details from Reddit API response
            if len(response) >= 2 and 'data' in response[0] and 'children' in response[0]['data']:
                post_data = response[0]['data']['children'][0]['data']
                
                post_details = {
                    'title': post_data.get('title', ''),
                    'author': post_data.get('author', ''),
                    'score': post_data.get('score', 0),
                    'subreddit': post_data.get('subreddit', ''),
                    'num_comments': post_data.get('num_comments', 0),
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'created_utc': post_data.get('created_utc', 0),
                    'selftext': post_data.get('selftext', ''),
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'is_self': post_data.get('is_self', False),
                    'is_video': post_data.get('is_video', False),
                    'domain': post_data.get('domain', ''),
                    'over18': post_data.get('over18', False),
                    'spoiler': post_data.get('spoiler', False),
                    'locked': post_data.get('locked', False),
                    'stickied': post_data.get('stickied', False)
                }
                
                return [post_details]
            else:
                return [{"error": "Post not found or invalid response"}]
            
        except Exception as e:
            logger.error(f"Error getting post details: {str(e)}")
            return [{"error": f"Failed to get post details: {str(e)}"}]
    
    async def get_comments(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get comments for a specific Reddit post."""
        try:
            post_id = arguments.get('post_id', '')
            limit = arguments.get('limit', 10)
            
            if not post_id:
                return [{"error": "Post ID is required"}]
            
            logger.info(f"Getting comments for post: {post_id}")
            response = self.client.get_post_comments(post_id, limit)
            
            # Extract comments from Reddit API response
            comments = []
            if len(response) >= 2 and 'data' in response[1] and 'children' in response[1]['data']:
                for child in response[1]['data']['children']:
                    comment_data = child['data']
                    
                    # Skip deleted comments and non-comment items
                    if comment_data.get('body') == '[deleted]' or comment_data.get('kind') != 't1':
                        continue
                    
                    comments.append({
                        'author': comment_data.get('author', ''),
                        'body': comment_data.get('body', ''),
                        'score': comment_data.get('score', 0),
                        'created_utc': comment_data.get('created_utc', 0),
                        'permalink': comment_data.get('permalink', ''),
                        'depth': comment_data.get('depth', 0),
                        'is_submitter': comment_data.get('is_submitter', False),
                        'distinguished': comment_data.get('distinguished', ''),
                        'edited': comment_data.get('edited', False)
                    })
            
            return [{
                'comments': comments,
                'post_id': post_id,
                'total_comments': len(comments)
            }]
            
        except Exception as e:
            logger.error(f"Error getting post comments: {str(e)}")
            return [{"error": f"Failed to get comments: {str(e)}"}] 