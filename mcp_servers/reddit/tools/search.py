"""
Search Tools for Reddit MCP Server
Handles search functionality across Reddit.
"""

import logging
from typing import Dict, Any, List

from .base import RedditMCPClient

logger = logging.getLogger(__name__)

class SearchTools:
    """Search tools for Reddit MCP server."""
    
    def __init__(self):
        """Initialize search tools."""
        self.client = RedditMCPClient()
    
    async def search_posts(self, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for posts across Reddit using keywords or phrases."""
        try:
            query = arguments.get('query', '')
            limit = arguments.get('limit', 10)
            
            if not query:
                return [{"error": "Search query is required"}]
            
            logger.info(f"Searching Reddit for: {query}")
            response = self.client.search_posts(query, limit)
            
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
                'total_found': len(posts),
                'query': query
            }]
            
        except Exception as e:
            logger.error(f"Error searching posts: {str(e)}")
            return [{"error": f"Search failed: {str(e)}"}] 