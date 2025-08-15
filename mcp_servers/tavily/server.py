# server.py
from app import mcp

# Importing registers the tools with FastMCP
import tools.search   # noqa: F401
import tools.extract  # noqa: F401
import tools.crawl    # noqa: F401

if __name__ == "__main__":
    print("Starting MCP server 'Tavily' on stdio…")
    mcp.run()