
import os
import requests

def delete_ticket(ticket_id: int):
    freshdesk_domain = os.environ.get("FRESHDESK_DOMAIN")
    api_key = os.environ.get("FRESHDESK_API_KEY")

    url = f"https://{freshdesk_domain}.freshdesk.com/api/v2/tickets/{ticket_id}"
    auth = (api_key, "X")

    response = requests.delete(url, auth=auth)
    return response.status_code
