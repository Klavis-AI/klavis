# import os
# import httpx
# from dotenv import load_dotenv

# # Load variables from .env file
# load_dotenv()

# ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
# ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
# ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")

# def get_ticket_status(ticket_id: int):
#     """Fetch the status of a Zendesk ticket by its ID."""
#     url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
#     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

#     with httpx.Client() as client:
#         response = client.get(url, auth=auth)
        
#         if response.status_code == 200:
#             ticket = response.json()["ticket"]
#             status = ticket.get("status")
#             print(f"✅ Ticket {ticket_id} status: {status}")
            
#             return ticket
#         else:
#             print(f"❌ Failed to fetch ticket: {response.status_code}")
#             print(response.text)
#             return None

# # Example usage
# if __name__ == "__main__":
#     ticket_id = 12345  # Replace with your actual ticket ID
#     status = get_ticket_status(ticket_id)
#     print(status)
import httpx
from .common import get_zendesk_env, base_url, auth, client, safe_text

def get_ticket_status(ticket_id: int) -> dict:
    """
    Stateless fetch of a single ticket status.
    """
    email, token, subdomain = get_zendesk_env()
    url = f"{base_url(subdomain)}/api/v2/tickets/{ticket_id}.json"

    with client() as c:
        resp = c.get(url, auth=auth(email, token))
        if resp.status_code != 200:
            raise RuntimeError(f"Zendesk get status failed ({resp.status_code}): {safe_text(resp)}")
        t = resp.json().get("ticket", {})
        return {
            "ticket_id": t.get("id", ticket_id),
            "status": t.get("status"),
            "priority": t.get("priority"),
            "assignee_id": t.get("assignee_id"),
        }

