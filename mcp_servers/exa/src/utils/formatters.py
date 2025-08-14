"""
Response formatting utilities for Exa MCP Server
"""

from typing import Any, Dict, List
from ..models.schemas import ExaSearchResult


class ResponseFormatter:
    """Formats API responses for AI agent consumption"""
    
    @staticmethod
    def format_search_results(
        results: List[Dict[str, Any]], 
        query: str, 
        search_type: str = "neural"
    ) -> str:
        """Format search results into readable text"""
        
        if not results:
            return f"""# Exa Search Results

**Query:** {query}
**Search Type:** {search_type}
**Results Found:** 0

No results found for this query. Try:
- Using different keywords
- Checking spelling
- Broadening your search terms
"""
        
        formatted_results = []
        for i, item in enumerate(results, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            score = item.get('score', 0)
            result_id = item.get('id', 'No ID')
            snippet = item.get('text', 'No snippet available')
            
            # Truncate snippet
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_results.append(f"""
{i}. **{title}**
   URL: {url}
   Score: {score:.4f}
   ID: {result_id}
   {snippet}
""")
        
        return f"""# Exa Search Results

**Query:** {query}
**Results Found:** {len(results)}
**Search Type:** {search_type}

## Results:
{''.join(formatted_results)}

**Note:** Use `get_page_contents` with the result IDs to retrieve full content from specific pages.
"""
    
    @staticmethod
    def format_contents(
        results: List[Dict[str, Any]], 
        params: Dict[str, Any]
    ) -> str:
        """Format page contents into readable text"""
        
        if not results:
            return """# Page Contents Retrieved

**Error:** No content could be retrieved for the provided IDs.
"""
        
        formatted_contents = []
        for i, item in enumerate(results, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            result_id = item.get('id', 'No ID')
            
            content_parts = [f"\n{i}. **{title}**"]
            content_parts.append(f"   URL: {url}")
            content_parts.append(f"   ID: {result_id}")
            
            # Add summary if requested and available
            if params.get('summary') and item.get('summary'):
                content_parts.append(f"\n   **AI Summary:**\n   {item.get('summary')}")
            
            # Add highlights if requested and available
            if params.get('highlights') and item.get('highlights'):
                content_parts.append(f"\n   **Key Highlights:**")
                for highlight in item.get('highlights', []):
                    content_parts.append(f"   • {highlight}")
            
            # Add full text if requested and available
            if params.get('text') and item.get('text'):
                text_content = item.get('text', '')
                # Truncate very long content
                if len(text_content) > 2000:
                    text_content = text_content[:2000] + "... [Content truncated]"
                content_parts.append(f"\n   **Full Text:**\n   {text_content}")
            
            formatted_contents.append('\n'.join(content_parts))
        
        return f"""# Page Contents Retrieved

**Number of Pages:** {len(results)}
**Include Text:** {params.get('text', False)}
**Include Highlights:** {params.get('highlights', False)}
**Include Summary:** {params.get('summary', False)}

## Content:
{''.join(formatted_contents)}
"""
    
    @staticmethod
    def format_similar_results(
        results: List[Dict[str, Any]], 
        original_url: str
    ) -> str:
        """Format similar content results"""
        
        if not results:
            return f"""# Similar Content Found

**Original URL:** {original_url}
**Similar Results Found:** 0

No similar content found for this URL.
"""
        
        formatted_results = []
        for i, item in enumerate(results, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            score = item.get('score', 0)
            result_id = item.get('id', 'No ID')
            snippet = item.get('text', 'No snippet available')
            
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_results.append(f"""
{i}. **{title}**
   URL: {url}
   Similarity Score: {score:.4f}
   ID: {result_id}
   {snippet}
""")
        
        return f"""# Similar Content Found

**Original URL:** {original_url}
**Similar Results Found:** {len(results)}

## Similar Pages:
{''.join(formatted_results)}

**Note:** Use `get_page_contents` with the result IDs to retrieve full content from specific similar pages.
"""
    
    @staticmethod
    def format_recent_results(
        results: List[Dict[str, Any]], 
        query: str, 
        date_range: str
    ) -> str:
        """Format recent content search results"""
        
        formatted_results = []
        for i, item in enumerate(results, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            score = item.get('score', 0)
            result_id = item.get('id', 'No ID')
            published_date = item.get('publishedDate', 'Date unknown')
            snippet = item.get('text', 'No snippet available')
            
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_results.append(f"""
{i}. **{title}**
   URL: {url}
   Score: {score:.4f}
   Published: {published_date}
   ID: {result_id}
   {snippet}
""")
        
        return f"""# Recent Content Search Results

**Query:** {query}
**Time Range:** {date_range}
**Recent Results Found:** {len(results)}

## Recent Content:
{''.join(formatted_results)}

**Note:** Use `get_page_contents` with the result IDs to retrieve full content from specific recent pages.
"""
    
    @staticmethod
    def format_academic_results(
        results: List[Dict[str, Any]], 
        query: str,
        domains_used: List[str]
    ) -> str:
        """Format academic content search results"""
        
        formatted_results = []
        for i, item in enumerate(results, 1):
            title = item.get('title', 'No title')
            url = item.get('url', 'No URL')
            score = item.get('score', 0)
            result_id = item.get('id', 'No ID')
            published_date = item.get('publishedDate', 'Date unknown')
            snippet = item.get('text', 'No snippet available')
            
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            
            formatted_results.append(f"""
{i}. **{title}**
   URL: {url}
   Score: {score:.4f}
   Published: {published_date}
   ID: {result_id}
   {snippet}
""")
        
        domains_text = ', '.join(domains_used[:5])
        if len(domains_used) > 5:
            domains_text += "..."
        
        return f"""# Academic Content Search Results

**Query:** {query}
**Academic Results Found:** {len(results)}
**Focused Domains:** {domains_text}

## Academic Sources:
{''.join(formatted_results)}

**Note:** Use `get_page_contents` with the result IDs to retrieve full content from specific academic sources.
"""
    
    @staticmethod
    def format_error(tool_name: str, error_message: str) -> str:
        """Format error messages consistently"""
        return f"""# Error in {tool_name}

**Error:** {error_message}

**Troubleshooting Tips:**
- Check your API key is valid and set correctly
- Verify your internet connection
- Ensure the request parameters are correct
- Check if you've exceeded API rate limits

**Need Help?** 
- Review the tool documentation
- Check the Exa API status
- Verify your environment variables
""" 