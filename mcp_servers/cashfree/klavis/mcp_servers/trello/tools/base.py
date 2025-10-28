import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")
TRELLO_API_URL = "https://api.trello.com/1"

class TrelloClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=TRELLO_API_URL,
            params={
                "key": TRELLO_API_KEY,
                "token": TRELLO_API_TOKEN,
            },
        )

    async def close(self):
        await self.client.aclose()

    async def make_request(self, method: str, endpoint: str, **kwargs):
        response = await self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response.json()

http_clients: dict[str, TrelloClient] = {}

async def init_http_clients():
    http_clients["trello"] = TrelloClient()

async def close_http_clients():
    for client in http_clients.values():
        await client.close()

def get_trello_client() -> TrelloClient:
    return http_clients["trello"]
