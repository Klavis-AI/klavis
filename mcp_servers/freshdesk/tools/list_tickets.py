
import os
import requests

def list_tickets(filter_name: str = None, query: str = None):
    freshdesk_domain = os.environ.get("FRESHDESK_DOMAIN")
    api_key = os.environ.get("FRESHDESK_API_KEY")

    url = f"https://{freshdesk_domain}.freshdesk.com/api/v2/tickets"
    headers = {
        "Content-Type": "application/json",
    }
    auth = (api_key, "X")
    params = {}
    if filter_name:
        params['filter'] = filter_name
    if query:
        params['query'] = query

    response = requests.get(url, headers=headers, auth=auth, params=params)
    return response.json()
