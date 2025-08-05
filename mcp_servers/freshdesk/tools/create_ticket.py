import os
import requests

def create_ticket(subject: str, description: str, email: str, priority: int, status: int):
    freshdesk_domain = os.environ.get("FRESHDESK_DOMAIN")
    api_key = os.environ.get("FRESHDESK_API_KEY")

    url = f"https://{freshdesk_domain}.freshdesk.com/api/v2/tickets"
    headers = {
        "Content-Type": "application/json",
    }
    auth = (api_key, "X")
    data = {
        "subject": subject,
        "description": description,
        "email": email,
        "priority": priority,
        "status": status,
    }

    response = requests.post(url, headers=headers, auth=auth, json=data)
    return response.json()