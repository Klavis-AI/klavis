import requests
import os
from auth import authenticate

def list_vendors(limit=10):
    session_id = authenticate()
    url = "https://api.bill.com/api/v2/Vendor/List.json"
    params = {
        "sessionId": session_id,
        "devKey": os.getenv("BILL_DEV_KEY"),
        "pageSize": limit
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
