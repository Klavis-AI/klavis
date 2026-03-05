import json
from enum import Enum

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP


# Define an enum for the type of financial statement
class FinancialType(str, Enum):
    income_stmt = "income_stmt"
    quarterly_income_stmt = "quarterly_income_stmt"
    balance_sheet = "balance_sheet"
    quarterly_balance_sheet = "quarterly_balance_sheet"
    cashflow = "cashflow"
    quarterly_cashflow = "quarterly_cashflow"


class HolderType(str, Enum):
    major_holders = "major_holders"
    institutional_holders = "institutional_holders"
    mutualfund_holders = "mutualfund_holders"
    insider_transactions = "insider_transactions"
    insider_purchases = "insider_purchases"
    insider_roster_holders = "insider_roster_holders"


class RecommendationType(str, Enum):
    recommendations = "recommendations"
    upgrades_downgrades = "upgrades_downgrades"


# Initialize FastMCP server
yfinance_server = FastMCP(
    "yfinance",
    host="0.0.0.0",
    port=5000,
    instructions="""
# Yahoo Finance MCP Server

This server is used to get information about a given ticker symbol from yahoo finance.

Available tools:
- get_historical_stock_prices: Get historical stock prices for a given ticker symbol from yahoo finance. Include the following information: Date, Open, High, Low, Close, Volume, Adj Close.
- get_stock_price_by_date: Get stock price for a specific date. More efficient than historical prices when you only need one date. Can find nearest trading day for weekends/holidays.
- get_stock_info: Get stock information for a given ticker symbol from yahoo finance. Include the following information: Stock Price & Trading Info, Company Information, Financial Metrics, Earnings & Revenue, Margins & Returns, Dividends, Balance Sheet, Ownership, Analyst Coverage, Risk Metrics, Other.
- get_yahoo_finance_news: Get news for a given ticker symbol from yahoo finance.
- get_stock_actions: Get stock dividends and stock splits for a given ticker symbol from yahoo finance.
- get_financial_statement: Get financial statement for a given ticker symbol from yahoo finance. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.
- get_holder_info: Get holder information for a given ticker symbol from yahoo finance. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.
- get_option_expiration_dates: Fetch the available options expiration dates for a given ticker symbol.
- get_option_chain: Fetch the option chain for a given ticker symbol, expiration date, and option type.
- get_recommendations: Get recommendations or upgrades/downgrades for a given ticker symbol from yahoo finance. You can also specify the number of months back to get upgrades/downgrades for, default is 12.
""",
)


@yfinance_server.tool(
    name="get_historical_stock_prices",
    description="""Get historical stock prices for a given ticker symbol from yahoo finance. Include the following information: Date, Open, High, Low, Close, Volume, Dividends, Stock Splits, and optionally Adj Close.

Args:
    ticker: str
        The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
    period : str
        Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        Used only when both start_date and end_date are not provided
        Default is "1mo"
    interval : str
        Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        Intraday data cannot extend last 60 days
        Default is "1d"
    start_date: str (optional)
        The start date for historical data (format: 'YYYY-MM-DD'), e.g. "2024-01-01"
        If provided, period parameter will be ignored
    end_date: str (optional)
        The end date for historical data (format: 'YYYY-MM-DD'), e.g. "2024-12-31"
        If not provided, defaults to current date
    auto_adjust: bool (optional)
        If True (default), returns prices adjusted for dividends and stock splits (Open, High, Low, Close are adjusted)
        If False, returns raw unadjusted prices and includes 'Adj Close' column
        Default is True
""",
)
async def get_historical_stock_prices(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d",
    start_date: str | None = None,
    end_date: str | None = None,
    auto_adjust: bool = True
) -> str:
    """Get historical stock prices for a given ticker symbol

    Args:
        ticker: str
            The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            Used only when both start_date and end_date are not provided
            Default is "1mo"
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Intraday data cannot extend last 60 days
            Default is "1d"
        start_date: str (optional)
            The start date for historical data (format: 'YYYY-MM-DD')
            If provided, period parameter will be ignored
        end_date: str (optional)
            The end date for historical data (format: 'YYYY-MM-DD')
            If not provided, defaults to current date
        auto_adjust: bool (optional)
            If True (default), returns prices adjusted for dividends and stock splits
            If False, returns raw unadjusted prices and includes 'Adj Close' column
            Default is True
    """
    import datetime

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting historical stock prices for {ticker}: {e}")
        return f"Error: getting historical stock prices for {ticker}: {e}"

    # Calculate the actual start and end dates based on provided parameters
    actual_start = None
    actual_end = None
    use_period = True

    # If start_date or end_date is provided, we don't use period
    if start_date is not None or end_date is not None:
        use_period = False

        # Parse and validate dates
        try:
            if start_date is not None:
                actual_start = pd.to_datetime(start_date)
            if end_date is not None:
                actual_end = pd.to_datetime(end_date)
        except Exception as e:
            return f"Error: Invalid date format. Please use YYYY-MM-DD format, e.g. '2024-01-15'. {e}"

        # Apply date calculation logic
        if start_date is not None and end_date is not None:
            # Both provided: use as is
            pass
        elif start_date is not None and end_date is None:
            # Only start_date: end defaults to current date
            actual_end = pd.Timestamp.now()
        elif start_date is None and end_date is not None:
            # Only end_date: start = end - period
            actual_end_temp = actual_end
            # Calculate start based on period
            period_map = {
                "1d": pd.DateOffset(days=1),
                "5d": pd.DateOffset(days=5),
                "1mo": pd.DateOffset(months=1),
                "3mo": pd.DateOffset(months=3),
                "6mo": pd.DateOffset(months=6),
                "1y": pd.DateOffset(years=1),
                "2y": pd.DateOffset(years=2),
                "5y": pd.DateOffset(years=5),
                "10y": pd.DateOffset(years=10),
                "ytd": None,  # Will be calculated separately
                "max": None   # Will use a very old date
            }

            if period == "ytd":
                # Year to date: start from beginning of current year
                actual_start = pd.Timestamp(datetime.datetime(actual_end_temp.year, 1, 1))
            elif period == "max":
                # Max: use a date far in the past
                actual_start = pd.Timestamp("1900-01-01")
            elif period in period_map:
                actual_start = actual_end_temp - period_map[period]
            else:
                return f"Error: Invalid period '{period}'. Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"

    # Get historical data with unified logic
    try:
        if use_period:
            # Use period parameter (original behavior)
            hist_data = company.history(period=period, interval=interval, auto_adjust=auto_adjust)
        else:
            # Use start and end dates
            hist_data = company.history(start=actual_start, end=actual_end, interval=interval, auto_adjust=auto_adjust)

        hist_data = hist_data.reset_index(names="Date")
        hist_data = hist_data.to_json(orient="records", date_format="iso")
        return hist_data
    except Exception as e:
        print(f"Error: getting historical stock prices for {ticker}: {e}")
        return f"Error: getting historical stock prices for {ticker}: {e}"


@yfinance_server.tool(
    name="get_stock_price_by_date",
    description="""Get stock price for a specific date. This tool is more efficient than getting historical prices when you only need data for one specific date.

Args:
    ticker: str
        The ticker symbol of the stock to get price for, e.g. "AAPL"
    date: str
        The specific date to get price for (format: 'YYYY-MM-DD'), e.g. "2024-01-15"
    find_nearest: bool
        If True and the exact date has no trading data (weekend/holiday), return the nearest trading day data.
        If False, return error for non-trading days. Default is True.
    auto_adjust: bool (optional)
        If True (default), returns prices adjusted for dividends and stock splits
        If False, returns raw unadjusted prices
        Default is True
""",
)
async def get_stock_price_by_date(ticker: str, date: str, find_nearest: bool = True, auto_adjust: bool = True) -> str:
    """Get stock price for a specific date

    Args:
        ticker: The ticker symbol of the stock
        date: The specific date (format: 'YYYY-MM-DD')
        find_nearest: Whether to find nearest trading day if exact date has no data
        auto_adjust: If True, returns adjusted prices; if False, returns raw prices
    """
    import datetime
    
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting stock price for {ticker}: {e}")
        return f"Error: getting stock price for {ticker}: {e}"
    
    # Validate date format
    try:
        target_date = pd.to_datetime(date).tz_localize(None)  # Remove timezone info
    except Exception as e:
        return f"Error: Invalid date format '{date}'. Please use YYYY-MM-DD format, e.g. '2024-01-15'"
    
    # Check if date is in the future
    if target_date > pd.Timestamp.now().tz_localize(None):  # Remove timezone info for comparison
        return f"Error: Cannot get stock price for future date {date}"
    
    try:
        if find_nearest:
            # Get data for a wider range to find nearest trading day
            start_date = target_date - pd.Timedelta(days=7)
            end_date = target_date + pd.Timedelta(days=7)
            hist_data = company.history(start=start_date, end=end_date, interval="1d", auto_adjust=auto_adjust)
            
            if hist_data.empty:
                return f"No trading data found for {ticker} around date {date}"
            
            # Find the closest date
            hist_data = hist_data.reset_index()
            # Remove timezone info from Date column for comparison
            hist_data['Date'] = hist_data['Date'].dt.tz_localize(None)
            hist_data['date_diff'] = abs(hist_data['Date'] - target_date)
            closest_row = hist_data.loc[hist_data['date_diff'].idxmin()]
            
            # Format the result
            result = {
                "ticker": ticker,
                "requested_date": date,
                "actual_date": closest_row['Date'].strftime('%Y-%m-%d'),
                "open": float(closest_row['Open']),
                "high": float(closest_row['High']), 
                "low": float(closest_row['Low']),
                "close": float(closest_row['Close']),
                "volume": int(closest_row['Volume']),
                "dividends": float(closest_row.get('Dividends', 0)),
                "stock_splits": float(closest_row.get('Stock Splits', 0))
            }
            
            if closest_row['Date'].strftime('%Y-%m-%d') != date:
                result["note"] = f"Requested date {date} was not a trading day. Showing nearest trading day."
            
        else:
            # Get data for exact date only
            start_date = target_date
            end_date = target_date + pd.Timedelta(days=1)
            hist_data = company.history(start=start_date, end=end_date, interval="1d", auto_adjust=auto_adjust)
            
            if hist_data.empty:
                return f"No trading data found for {ticker} on {date}. This might be a weekend or holiday. Use find_nearest=true to get nearest trading day."
            
            # Get the exact date data
            hist_data = hist_data.reset_index()
            # Remove timezone info from Date column
            hist_data['Date'] = hist_data['Date'].dt.tz_localize(None)
            row = hist_data.iloc[0]
            
            result = {
                "ticker": ticker,
                "date": row['Date'].strftime('%Y-%m-%d'),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']), 
                "close": float(row['Close']),
                "volume": int(row['Volume']),
                "dividends": float(row.get('Dividends', 0)),
                "stock_splits": float(row.get('Stock Splits', 0))
            }
        
        return json.dumps(result)
        
    except Exception as e:
        print(f"Error: getting stock price by date for {ticker}: {e}")
        return f"Error: getting stock price by date for {ticker}: {e}"


@yfinance_server.tool(
    name="get_stock_info",
    description="""Get stock information for a given ticker symbol from yahoo finance. Include the following information:
Stock Price & Trading Info, Company Information, Financial Metrics, Earnings & Revenue, Margins & Returns, Dividends, Balance Sheet, Ownership, Analyst Coverage, Risk Metrics, Other.

Args:
    ticker: str
        The ticker symbol of the stock to get information for, e.g. "AAPL"
""",
)
async def get_stock_info(ticker: str) -> str:
    """Get stock information for a given ticker symbol"""
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting stock information for {ticker}: {e}")
        return f"Error: getting stock information for {ticker}: {e}"
    info = company.info
    return json.dumps(info)


@yfinance_server.tool(
    name="get_yahoo_finance_news",
    description="""Get news for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get news for, e.g. "AAPL"
""",
)
async def get_yahoo_finance_news(ticker: str) -> str:
    """Get news for a given ticker symbol

    Args:
        ticker: str
            The ticker symbol of the stock to get news for, e.g. "AAPL"
    """
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting news for {ticker}: {e}")
        return f"Error: getting news for {ticker}: {e}"

    # If the company is found, get the news
    try:
        news = company.news
    except Exception as e:
        print(f"Error: getting news for {ticker}: {e}")
        return f"Error: getting news for {ticker}: {e}"

    news_list = []
    for news in company.news:
        if news.get("content", {}).get("contentType", "") == "STORY":
            title = news.get("content", {}).get("title", "")
            summary = news.get("content", {}).get("summary", "")
            description = news.get("content", {}).get("description", "")
            url = news.get("content", {}).get("canonicalUrl", {}).get("url", "")
            news_list.append(
                f"Title: {title}\nSummary: {summary}\nDescription: {description}\nURL: {url}"
            )
    if not news_list:
        print(f"No news found for company that searched with {ticker} ticker.")
        return f"No news found for company that searched with {ticker} ticker."
    return "\n\n".join(news_list)


@yfinance_server.tool(
    name="get_stock_actions",
    description="""Get stock dividends and stock splits for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get stock actions for, e.g. "AAPL"
""",
)
async def get_stock_actions(ticker: str) -> str:
    """Get stock dividends and stock splits for a given ticker symbol"""
    try:
        company = yf.Ticker(ticker)
    except Exception as e:
        print(f"Error: getting stock actions for {ticker}: {e}")
        return f"Error: getting stock actions for {ticker}: {e}"
    actions_df = company.actions
    actions_df = actions_df.reset_index(names="Date")
    return actions_df.to_json(orient="records", date_format="iso")


@yfinance_server.tool(
    name="get_financial_statement",
    description="""Get financial statement for a given ticker symbol from yahoo finance. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.

Args:
    ticker: str
        The ticker symbol of the stock to get financial statement for, e.g. "AAPL"
    financial_type: str
        The type of financial statement to get. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.
""",
)
async def get_financial_statement(ticker: str, financial_type: str) -> str:
    """Get financial statement for a given ticker symbol"""

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting financial statement for {ticker}: {e}")
        return f"Error: getting financial statement for {ticker}: {e}"

    if financial_type == FinancialType.income_stmt:
        financial_statement = company.income_stmt
    elif financial_type == FinancialType.quarterly_income_stmt:
        financial_statement = company.quarterly_income_stmt
    elif financial_type == FinancialType.balance_sheet:
        financial_statement = company.balance_sheet
    elif financial_type == FinancialType.quarterly_balance_sheet:
        financial_statement = company.quarterly_balance_sheet
    elif financial_type == FinancialType.cashflow:
        financial_statement = company.cashflow
    elif financial_type == FinancialType.quarterly_cashflow:
        financial_statement = company.quarterly_cashflow
    else:
        return f"Error: invalid financial type {financial_type}. Please use one of the following: {FinancialType.income_stmt}, {FinancialType.quarterly_income_stmt}, {FinancialType.balance_sheet}, {FinancialType.quarterly_balance_sheet}, {FinancialType.cashflow}, {FinancialType.quarterly_cashflow}."

    # Create a list to store all the json objects
    result = []

    # Loop through each column (date)
    for column in financial_statement.columns:
        if isinstance(column, pd.Timestamp):
            date_str = column.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD
        else:
            date_str = str(column)

        # Create a dictionary for each date
        date_obj = {"date": date_str}

        # Add each metric as a key-value pair
        for index, value in financial_statement[column].items():
            # Add the value, handling NaN values
            date_obj[index] = None if pd.isna(value) else value

        result.append(date_obj)

    return json.dumps(result)


@yfinance_server.tool(
    name="get_holder_info",
    description="""Get holder information for a given ticker symbol from yahoo finance. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.

Args:
    ticker: str
        The ticker symbol of the stock to get holder information for, e.g. "AAPL"
    holder_type: str
        The type of holder information to get. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.
""",
)
async def get_holder_info(ticker: str, holder_type: str) -> str:
    """Get holder information for a given ticker symbol"""

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting holder info for {ticker}: {e}")
        return f"Error: getting holder info for {ticker}: {e}"

    if holder_type == HolderType.major_holders:
        return company.major_holders.reset_index(names="metric").to_json(orient="records")
    elif holder_type == HolderType.institutional_holders:
        return company.institutional_holders.to_json(orient="records")
    elif holder_type == HolderType.mutualfund_holders:
        return company.mutualfund_holders.to_json(orient="records", date_format="iso")
    elif holder_type == HolderType.insider_transactions:
        return company.insider_transactions.to_json(orient="records", date_format="iso")
    elif holder_type == HolderType.insider_purchases:
        return company.insider_purchases.to_json(orient="records", date_format="iso")
    elif holder_type == HolderType.insider_roster_holders:
        return company.insider_roster_holders.to_json(orient="records", date_format="iso")
    else:
        return f"Error: invalid holder type {holder_type}. Please use one of the following: {HolderType.major_holders}, {HolderType.institutional_holders}, {HolderType.mutualfund_holders}, {HolderType.insider_transactions}, {HolderType.insider_purchases}, {HolderType.insider_roster_holders}."


@yfinance_server.tool(
    name="get_option_expiration_dates",
    description="""Fetch the available options expiration dates for a given ticker symbol.

Args:
    ticker: str
        The ticker symbol of the stock to get option expiration dates for, e.g. "AAPL"
""",
)
async def get_option_expiration_dates(ticker: str) -> str:
    """Fetch the available options expiration dates for a given ticker symbol."""

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting option expiration dates for {ticker}: {e}")
        return f"Error: getting option expiration dates for {ticker}: {e}"
    return json.dumps(company.options)


@yfinance_server.tool(
    name="get_option_chain",
    description="""Fetch the option chain for a given ticker symbol, expiration date, and option type.

Args:
    ticker: str
        The ticker symbol of the stock to get option chain for, e.g. "AAPL"
    expiration_date: str
        The expiration date for the options chain (format: 'YYYY-MM-DD')
    option_type: str
        The type of option to fetch ('calls' or 'puts')
""",
)
async def get_option_chain(ticker: str, expiration_date: str, option_type: str) -> str:
    """Fetch the option chain for a given ticker symbol, expiration date, and option type.

    Args:
        ticker: The ticker symbol of the stock
        expiration_date: The expiration date for the options chain (format: 'YYYY-MM-DD')
        option_type: The type of option to fetch ('calls' or 'puts')

    Returns:
        str: JSON string containing the option chain data
    """

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting option chain for {ticker}: {e}")
        return f"Error: getting option chain for {ticker}: {e}"

    # Check if the expiration date is valid
    if expiration_date not in company.options:
        return f"Error: No options available for the date {expiration_date}. You can use `get_option_expiration_dates` to get the available expiration dates."

    # Check if the option type is valid
    if option_type not in ["calls", "puts"]:
        return "Error: Invalid option type. Please use 'calls' or 'puts'."

    # Get the option chain
    option_chain = company.option_chain(expiration_date)
    if option_type == "calls":
        return option_chain.calls.to_json(orient="records", date_format="iso")
    elif option_type == "puts":
        return option_chain.puts.to_json(orient="records", date_format="iso")
    else:
        return f"Error: invalid option type {option_type}. Please use one of the following: calls, puts."


@yfinance_server.tool(
    name="get_recommendations",
    description="""Get recommendations or upgrades/downgrades for a given ticker symbol from yahoo finance. You can also specify the number of months back to get upgrades/downgrades for, default is 12.

Args:
    ticker: str
        The ticker symbol of the stock to get recommendations for, e.g. "AAPL"
    recommendation_type: str
        The type of recommendation to get. You can choose from the following recommendation types: recommendations, upgrades_downgrades.
    months_back: int
        The number of months back to get upgrades/downgrades for, default is 12.
""",
)
async def get_recommendations(ticker: str, recommendation_type: str, months_back: int = 12) -> str:
    """Get recommendations or upgrades/downgrades for a given ticker symbol"""
    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting recommendations for {ticker}: {e}")
        return f"Error: getting recommendations for {ticker}: {e}"
    try:
        if recommendation_type == RecommendationType.recommendations:
            return company.recommendations.to_json(orient="records")
        elif recommendation_type == RecommendationType.upgrades_downgrades:
            # Get the upgrades/downgrades based on the cutoff date
            upgrades_downgrades = company.upgrades_downgrades.reset_index()
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months_back)
            upgrades_downgrades = upgrades_downgrades[
                upgrades_downgrades["GradeDate"] >= cutoff_date
            ]
            upgrades_downgrades = upgrades_downgrades.sort_values("GradeDate", ascending=False)
            # Get the first occurrence (most recent) for each firm
            latest_by_firm = upgrades_downgrades.drop_duplicates(subset=["Firm"])
            return latest_by_firm.to_json(orient="records", date_format="iso")
    except Exception as e:
        print(f"Error: getting recommendations for {ticker}: {e}")
        return f"Error: getting recommendations for {ticker}: {e}"


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting Yahoo Finance MCP server...")
    yfinance_server.run(transport="streamable-http")
