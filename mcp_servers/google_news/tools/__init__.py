# klavis_google_news/tools/__init__.py
"""
Expose ToolSpec objects so Klavis can auto-register them.
"""
from .search_news import spec as search_news_spec, run as search_news

__all__ = [
    "search_news_spec",
    "search_news",
]
