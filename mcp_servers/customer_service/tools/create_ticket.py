import os
import httpx
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")

def create_ticket(subject, description, requester_email):
    """Create a ticket in Zendesk using HTTPX."""
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets.json"
    
    ticket_data = {
        "ticket": {
            "subject": subject,
            "comment": {
                "body": description
            },
            "requester": {
                "name": requester_email.split("@")[0],
                "email": requester_email
            }
        }
    }
    
    auth = (f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    
    with httpx.Client() as client:
        response = client.post(url, json=ticket_data, auth=auth)
        
        if response.status_code == 201:
            print("✅ Ticket created successfully!")
            return response.json()
        else:
            print(f"❌ Failed to create ticket: {response.status_code}")
            print(response.text)
            return None

# Example usage
if __name__ == "__main__":
    result = create_ticket(
        subject="Issue with MCP integration",
        description="The MCP server is not returning the expected data.",
        requester_name="John Doe",
        requester_email="john.doe@example.com"
    )
    print(result)
