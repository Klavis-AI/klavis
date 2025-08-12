# app.py
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP("Tavily") 