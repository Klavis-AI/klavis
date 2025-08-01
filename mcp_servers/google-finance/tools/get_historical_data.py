import httpx
import os

def get_historical_data(ticker: str, start_date: str, end_date: str):
    """
    Fetches historical daily closing price data for the given ticker and date range.
    """
    API_KEY = os.getenv("TWELVE_API_KEY")  # Load inside function

    if not API_KEY:
        return {"error": "Missing API key. Please set TWELVE_API_KEY."}

    try:
        url = (
            f"https://api.twelvedata.com/time_series?"
            f"symbol={ticker}&interval=1day&start_date={start_date}&end_date={end_date}&apikey={API_KEY}"
        )
        response = httpx.get(url, timeout=10)
        data = response.json()

        if "values" not in data:
            return {"error": data.get("message", "No historical data found")}

        return [
            {
                "date": item["datetime"],
                "close_price": float(item["close"])
            }
            for item in data["values"]
        ]
    except Exception as e:
        return {"error": str(e)}
