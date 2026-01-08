
"""
Google Hotels MCP Server

A Model Context Protocol server for hotel search and booking assistance.
"""

__version__ = "0.1.0"
__author__ = "Tanmay Naik"
__description__ = "A Model Context Protocol server for Google Hotels search and booking assistance"

from .api_client import GoogleHotelsApiClient, SerpApiError
from .tools import GoogleHotelsTools
from .schemas import HotelSearchRequest, HotelSummary

__all__ = [
    "GoogleHotelsApiClient",
    "SerpApiError", 
    "GoogleHotelsTools",
    "HotelSearchRequest",
    "HotelSummary"
]