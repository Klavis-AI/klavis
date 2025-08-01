import httpx
import os

def get_stock_price(ticker: str):
    """
    Fetches the current price for the given stock ticker.
    """
    API_KEY = os.getenv("TWELVE_API_KEY")  # Load inside function

    if not API_KEY:
        return {"error": "Missing API key. Please set TWELVE_API_KEY."}

    try:
        url = f"https://api.twelvedata.com/price?symbol={ticker}&apikey={API_KEY}"
        response = httpx.get(url, timeout=10)
        data = response.json()

        if "price" not in data:
            return {"error": data.get("message", "No data found")}

        return {
            "ticker": ticker,
            "price": float(data["price"]),
            "currency": "USD"
        }
    except Exception as e:
        return {"error": str(e)}
