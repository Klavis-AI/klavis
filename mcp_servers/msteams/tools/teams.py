from .base import make_graph_api_request

async def list_all_teams():
    """Lists all teams in the organization."""
    return await make_graph_api_request("GET", "/groups?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')")

async def list_joined_teams():
    """Lists all teams the current user has joined."""
    return await make_graph_api_request("GET", "/me/joinedTeams")

async def get_team(team_id: str):
    """Gets the details of a specific team by its ID."""
    return await make_graph_api_request("GET", f"/teams/{team_id}")

async def list_channels(team_id: str):
    """Lists all channels in a specified Microsoft Team."""
    return await make_graph_api_request("GET", f"/teams/{team_id}/channels")

async def create_channel(team_id: str, display_name: str, description: str = None):
    """Creates a new standard channel in a team."""
    payload = {"displayName": display_name, "description": description, "membershipType": "standard"}
    return await make_graph_api_request("POST", f"/teams/{team_id}/channels", json_data=payload)

async def send_channel_message(team_id: str, channel_id: str, message: str):
    """Sends a message to a specific channel in a Team."""
    payload = {"body": {"content": message}}
    return await make_graph_api_request("POST", f"/teams/{team_id}/channels/{channel_id}/messages", json_data=payload)
