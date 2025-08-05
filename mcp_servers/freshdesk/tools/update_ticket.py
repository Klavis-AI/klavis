
import os
import requests

def update_ticket(ticket_id: int, priority: int = None, status: int = None):
    freshdesk_domain = os.environ.get("FRESHDESK_DOMAIN")
    api_key = os.environ.get("FRESHDESK_API_KEY")

    url = f"https://{freshdesk_domain}.freshdesk.com/api/v2/tickets/{ticket_id}"
    headers = {
        "Content-Type": "application/json",
    }
    auth = (api_key, "X")
    data = {}
    if priority:
        data['priority'] = priority
    if status:
        data['status'] = status

    response = requests.put(url, headers=headers, auth=auth, json=data)
    return response.json()
