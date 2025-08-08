import os
from dotenv import load_dotenv
from mcp import MCPServer

# Load environment variables
load_dotenv()

from tools.track_events import track_event
from tools.identify_user import identify_user
from tools.list_event_categories import list_event_categories
from tools.get_user_profile import get_user_profile



def register_tools(server: MCPServer):
    server.register_tool(track_event)
    server.register_tool(identify_user)
    server.register_tool(list_event_categories)
    server.register_tool(get_user_profile)

if __name__ == "__main__":
    server = MCPServer()
    register_tools(server)
    server.run()