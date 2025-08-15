from mcp.server.fastmcp import FastMCP
from tools.create_ticket import create_ticket
from tools.get_ticket_status import get_ticket_status
from tools.list_recent_tickets import list_recent_tickets
from tools.add_comment_to_ticket import add_comment_to_ticket
import os, sys
from dotenv import load_dotenv


mcp = FastMCP()
load_dotenv()



@mcp.tool()
def create_ticket_tool(subject: str, description: str, email: str):
    """
    Create a new Zendesk ticket.
    """
    return create_ticket(subject, description, email)

@mcp.tool()
def get_ticket_status_tool(ticket_id: int):
    """
    Get the current status of a Zendesk ticket.
    """
    return get_ticket_status(ticket_id)

@mcp.tool()
def list_recent_tickets_tool(limit: int = 3):
    """
    List recent Zendesk tickets (default: 3).
    """
    return list_recent_tickets(limit)

@mcp.tool()
def add_comment_to_ticket_tool(ticket_id: int, comment: str):
    """
    Add a comment to a Zendesk ticket.
    """
    return add_comment_to_ticket(ticket_id, comment)


    # Your server start code here


if __name__ == "__main__":
    try:
        print("Starting script...")
        
        email = os.getenv("ZENDESK_EMAIL")
        api_token = os.getenv("ZENDESK_API_TOKEN")
        subdomain = os.getenv("ZENDESK_SUBDOMAIN")
        
        if not all([email, api_token, subdomain]):
            raise Exception("Missing environment variables")
        
        mcp.run(transport="stdio")

    except Exception as e:
        # Print error to stderr so Claude and Cursor logs can see it
        print(f"Server startup error: {e}", file=sys.stderr)
        raise
