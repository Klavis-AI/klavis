import os
from fastapi import FastAPI
from dotenv import load_dotenv

from tools.get_stock_price import get_stock_price
from tools.get_historical_data import get_historical_data
from tools.get_market_news import get_market_news
from tools.get_company_info import get_company_info

# Load environment variables
load_dotenv()

# Debug print to check if API key is loaded
print("DEBUG: TWELVE_API_KEY =", os.getenv("TWELVE_API_KEY"))

app = FastAPI(title="Google Finance MCP Server")

@app.get("/get_stock_price")
def stock_price(ticker: str):
    """
    Returns current stock price for a ticker.
    """
    return get_stock_price(ticker)

@app.get("/get_historical_data")
def historical_data(ticker: str, start_date: str, end_date: str):
    """
    Returns historical daily closing prices for a ticker in a date range.
    """
    return get_historical_data(ticker, start_date, end_date)

@app.get("/get_market_news")
def market_news():
    """
    Returns trending tickers (mock data).
    """
    return get_market_news()

@app.get("/get_company_info")
def company_info(ticker: str):
    """
    Returns basic company info for a ticker.
    """
    return get_company_info(ticker)
