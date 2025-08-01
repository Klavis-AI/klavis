import httpx
import os

def get_company_info(ticker: str):
    """
    Fetches basic company information for the given ticker.
    """
    API_KEY = os.getenv("TWELVE_API_KEY")  # Load inside function

    if not API_KEY:
        return {"error": "Missing API key. Please set TWELVE_API_KEY."}

    try:
        url = f"https://api.twelvedata.com/symbol_search?symbol={ticker}&apikey={API_KEY}"
        response = httpx.get(url, timeout=10)
        data = response.json()

        if "data" not in data or len(data["data"]) == 0:
            return {"error": data.get("message", "No company info found")}

        info = data["data"][0]
        return {
            "ticker": ticker,
            "name": info.get("instrument_name"),
            "exchange": info.get("exchange"),
            "country": info.get("country")
        }
    except Exception as e:
        return {"error": str(e)}
