import os
import requests
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

class TavilySearch:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.base_url = "https://api.tavily.com"
        
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY is not set")
    
    def search(self, query: str, search_depth: str = "basic", 
               include_domains: List[str] = None, exclude_domains: List[str] = None,
               max_results: int = 10) -> Dict:
        # Perform a web search using Tavily
        url = f"{self.base_url}/search"
        
        payload = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        response = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "query": query,
                "results": data.get("results", []),
                "search_depth": search_depth,
                "total_results": len(data.get("results", []))
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def summarize_url(self, url: str, include_images: bool = False) -> Dict:
        # Summarize content from a URL
        api_url = f"{self.base_url}/search"
        
        payload = {
            "query": f"summarize this webpage: {url}",
            "search_depth": "basic",
            "max_results": 1
        }
        
        response = requests.post(
            api_url,
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return {
                    "success": True,
                    "url": url,
                    "summary": results[0].get("content", ""),
                    "title": results[0].get("title", ""),
                    "content": results[0].get("content", "")
                }
            else:
                return {
                    "success": False,
                    "error": "No summary available"
                }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def search_and_summarize(self, query: str, search_depth: str = "basic") -> Dict:
        # Search and then summarize the top result
        # First, perform the search
        search_result = self.search(query, search_depth, max_results=1)
        
        if not search_result.get("success"):
            return search_result
        
        results = search_result.get("results", [])
        if not results:
            return {
                "success": False,
                "error": "No search results found"
            }
        
        # Get the URL of the first result
        top_result = results[0]
        url = top_result.get("url")
        
        if not url:
            return {
                "success": False,
                "error": "No URL found in search results"
            }
        
        # Summarize the URL
        summary_result = self.summarize_url(url)
        
        return {
            "success": True,
            "query": query,
            "search_result": top_result,
            "summary": summary_result.get("summary", ""),
            "title": summary_result.get("title", ""),
            "url": url
        }

def summarize_webpage(url: str) -> Dict:
    # Webpage summarization function
    try:
        tavily = TavilySearch()
        return tavily.summarize_url(url)
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_with_tavily(query: str, search_depth: str = "basic") -> Dict:
    # Tavily search function
    try:
        tavily = TavilySearch()
        return tavily.search(query, search_depth)
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_and_summarize(query: str) -> Dict:
    # Search and summarize function
    try:
        tavily = TavilySearch()
        return tavily.search_and_summarize(query)
    except Exception as e:
        return {"success": False, "error": str(e)}
