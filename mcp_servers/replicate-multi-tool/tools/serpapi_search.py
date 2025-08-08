import os
import requests
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

class SerpAPISearch:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search.json"
        
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is not set")
    
    def search(self, query: str, num_results: int = 10, search_type: str = "google") -> Dict:
        # Perform a web search
        params = {
            "q": query,
            "api_key": self.api_key,
            "num": num_results,
            "engine": search_type
        }
        
        response = requests.get(self.base_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "query": query,
                "total_results": data.get("search_information", {}).get("total_results", 0),
                "organic_results": data.get("organic_results", [])[:num_results],
                "related_questions": data.get("related_questions", []),
                "related_searches": data.get("related_searches", [])
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def search_images(self, query: str, num_results: int = 10) -> Dict:
        # Search for images
        return self.search(query, num_results, "google_images")
    
    def search_news(self, query: str, num_results: int = 10) -> Dict:
        # Search for news
        return self.search(query, num_results, "google_news")
    
    def search_shopping(self, query: str, num_results: int = 10) -> Dict:
        # Search for shopping results
        return self.search(query, num_results, "google_shopping")

def search_web_query(query: str, num_results: int = 10) -> Dict:
    # Web search function
    try:
        serpapi = SerpAPISearch()
        return serpapi.search(query, num_results)
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_images(query: str, num_results: int = 10) -> Dict:
    # Image search function
    try:
        serpapi = SerpAPISearch()
        return serpapi.search_images(query, num_results)
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_news(query: str, num_results: int = 10) -> Dict:
    # News search function
    try:
        serpapi = SerpAPISearch()
        return serpapi.search_news(query, num_results)
    except Exception as e:
        return {"success": False, "error": str(e)}
