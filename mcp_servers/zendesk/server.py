from mcp.server.fastmcp import FastMCP
import os, sys

# Tools (pure functions, stateless)
from tools.create_ticket import create_ticket
from tools.get_ticket_status import get_ticket_status
from tools.list_recent_tickets import list_recent_tickets
from tools.add_comment_to_ticket import add_comment_to_ticket
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP()

def _require_env():
    # Fail fast if required env vars are missing (no state kept)
    
    missing = [k for k in ("ZENDESK_EMAIL", "ZENDESK_API_TOKEN", "ZENDESK_SUBDOMAIN") if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

@mcp.tool()
def create_ticket_tool(subject: str, description: str, requester_email: str, requester_name: str | None = None) -> dict:
    """
    Create a new Zendesk ticket (stateless).
    """
    _require_env()
    return create_ticket(subject=subject, description=description, requester_email=requester_email, requester_name=requester_name)

@mcp.tool()
def get_ticket_status_tool(ticket_id: int) -> dict:
    """
    Get current status/assignee/priority of a Zendesk ticket (stateless).
    """
    _require_env()
    return get_ticket_status(ticket_id=ticket_id)

@mcp.tool()
def list_recent_tickets_tool(limit: int = 5) -> dict:
    """
    List recent Zendesk tickets (stateless). Limit 1..50.
    """
    _require_env()
    return list_recent_tickets(limit=limit)

@mcp.tool()
def add_comment_to_ticket_tool(ticket_id: int, comment: str, public: bool = True) -> dict:
    """
    Add a comment to an existing Zendesk ticket (stateless).
    """
    _require_env()
    return add_comment_to_ticket(ticket_id=ticket_id, comment=comment, public=public)

if __name__ == "__main__":
    try:
        _require_env()
        # STDIO transport so Claude/Cursor can spawn it
        print("Starting Zendesk MCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"Server startup error: {e}", file=sys.stderr)
        raise
