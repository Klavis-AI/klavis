import httpx
from dotenv import load_dotenv
import os

load_dotenv()

ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")

def add_comment_to_ticket(ticket_id: int, comment: str, public: bool = True):
    """Add a comment to a Zendesk ticket."""
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

    data = {
        "ticket": {
            "comment": {
                "body": comment,
                "public": public
            }
        }
    }

    with httpx.Client() as client:
        response = client.put(url, json=data, auth=auth)
        if response.status_code == 200:
            print(f"✅ Comment added to ticket {ticket_id}")
            return response.json()
        else:
            print(f"❌ Failed to add comment: {response.status_code}")
            print(response.text)
            return None
