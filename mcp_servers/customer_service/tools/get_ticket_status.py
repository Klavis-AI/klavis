import os
import httpx
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")

def get_ticket_status(ticket_id: int):
    """Fetch the status of a Zendesk ticket by its ID."""
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)

    with httpx.Client() as client:
        response = client.get(url, auth=auth)
        
        if response.status_code == 200:
            ticket = response.json()["ticket"]
            status = ticket.get("status")
            print(f"✅ Ticket {ticket_id} status: {status}")
            
            return ticket
        else:
            print(f"❌ Failed to fetch ticket: {response.status_code}")
            print(response.text)
            return None

# Example usage
if __name__ == "__main__":
    ticket_id = 12345  # Replace with your actual ticket ID
    status = get_ticket_status(ticket_id)
    print(status)
