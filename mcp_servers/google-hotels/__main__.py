"""
Entry point for running the MCP server as a module
Usage: python -m google_hotels_mcp
"""
import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())