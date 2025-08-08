import os
import requests
from dotenv import load_dotenv
load_dotenv()

def authenticate():
    url = "https://api.bill.com/api/v2/Login.json"
    data = {
        "userName": os.getenv("BILL_USER_EMAIL"),
        "password": os.getenv("BILL_PASSWORD"),
        "orgId": os.getenv("BILL_ORG_ID"),
        "devKey": os.getenv("BILL_DEV_KEY")
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["sessionId"]
