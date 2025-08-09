import os
from dotenv import load_dotenv
import httpx
from typing import Any

load_dotenv()


class TavilyClient:
    def __init__(self) -> None:
        self.base_url = "https://api.tavily.com"
        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY is not set. Please set it in your environment or .env file."
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._timeout = httpx.Timeout(30.0, connect=10.0)

    async def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Surface API error body for easier debugging by LLMs
                try:
                    err_json = e.response.json()
                except Exception:
                    err_json = {"detail": e.response.text}
                raise RuntimeError(
                    f"Tavily API request failed with status {e.response.status_code}: {err_json}"
                ) from e
            except httpx.RequestError as e:
                raise RuntimeError(
                    f"Network error while calling Tavily API: {str(e)}"
                ) from e
