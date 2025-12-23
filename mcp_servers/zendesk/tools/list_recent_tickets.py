# import os
# import httpx
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
# ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
# ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")

# def list_recent_tickets(limit: int = 5):
#     """List recent Zendesk tickets."""
#     url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json?sort_by=created_at&sort_order=desc"
#     auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

#     with httpx.Client() as client:
#         response = client.get(url, auth=auth)
#         if response.status_code == 200:
#             tickets = response.json().get("tickets", [])
#             recent = tickets[:limit]
#             print(f"✅ Found {len(recent)} recent tickets")
#             return recent
#         else:
#             print(f"❌ Failed to list tickets: {response.status_code}")
#             print(response.text)
#             return []
# if __name__ == "__main__":
#     # List last 3 tickets
#     tickets = list_recent_tickets(limit=3)
#     for t in tickets:
#         print(f"ID: {t['id']}, Subject: {t['subject']}, Status: {t['status']}")

#     # Add a comment to a ticket
import httpx
from .common import get_zendesk_env, base_url, auth, client, safe_text

def list_recent_tickets(limit: int = 5) -> dict:
    """
    Stateless list of recent tickets. Uses first page; trims to 'limit' (1..50).
    """
    if limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")

    email, token, subdomain = get_zendesk_env()
    url = f"{base_url(subdomain)}/api/v2/tickets.json?sort_by=created_at&sort_order=desc"

    with client() as c:
        resp = c.get(url, auth=auth(email, token))
        if resp.status_code != 200:
            raise RuntimeError(f"Zendesk list failed ({resp.status_code}): {safe_text(resp)}")
        tickets = resp.json().get("tickets", [])[:limit]
        out = [
            {
                "id": t.get("id"),
                "subject": t.get("subject"),
                "status": t.get("status"),
                "created_at": t.get("created_at"),
            }
            for t in tickets
        ]
        return {"tickets": out}
