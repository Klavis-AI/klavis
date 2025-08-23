# Google Hotels MCP Server

A Model Context Protocol (MCP) server that provides AI agents with comprehensive hotel search and booking assistance capabilities through Google Hotels data via SerpApi.

## Features
🏨 Comprehensive Hotel Search: Search hotels by location, dates, and guest count.
🔍 Advanced Filtering: Filter by price range, ratings, amenities.
📊 Price Comparison: Compare prices and find the best value options.
🏷️ Hotel Details: Get comprehensive information about specific properties.
🛠️ Reference Data: Access supported amenities.

## Installation 

## Prerequisites

Python 3.8 or higher
A SerpApi account and API key(https://serpapi.com)

## Quick Setup

1. Create a virtual environment:
```
python uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
2. Get a SerpApi key from https://serpapi.com

3. Install dependencies:
```
mcp>=1.0.0
requests>=2.31.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```
4. Set up your environment variables in .env:
Edit .env and add your SerpApi key 
```
SERPAPI_API_KEY= YOUR_SERPAPI_API_KEY

OPTIONAL:
LOG_LEVEL=INFO # LOGGING CONFIGURATION 
```
5. Installation of Packages
```
uv pip install -e .
```
6. Running and testing server
```
python -m google_hotels_mcp
```

## Getting Your SerpApi Key

Visit SerpApi (https://serpapi.com)
API Limit has 250 searches per month free trial
Create an account (free tier available)
Go to your dashboard and copy your API key
Add it to your .env file:
SERPAPI_API_KEY=your_actual_api_key_here

## Configuration For Claude Desktop
1. Add claude_desktop_config.json file to this path for Windows: %APPDATA%\Claude\claude_desktop_config.json
  Here is the claude_desktop_config.json file:
  ```
  {
    "mcpServers": {
      "google-hotels": {
        "command": "C:\\Users\\tanma\\OneDrive\\Desktop\\google-hotels-mcp\\.venv\\Scripts\\python.exe",
        "args": [
          "-m",
          "google_hotels_mcp.server"
        ],
        "cwd": "C:\\Users\\tanma\\OneDrive\\Desktop\\google-hotels-mcp",
        "env": {
          "SERPAPI_API_KEY": "YOUR_SERPAPI_KEY"
        }
      }
    }
  }
  ```

## Tools Available

1. `search_hotels`
Search for hotels in a specific location with check-in and check-out dates
Parameters:

query (required): Location or hotel name
check_in_date (required): Check-in date (YYYY-MM-DD)
check_out_date (required): Check-out date (YYYY-MM-DD)
adults (optional): Number of adults (default: 2)
children (optional): Number of children (default: 0)
currency (optional): Currency code (default: USD)

2. `get_supported_amenities`
Get a list of all supported amenities for hotels from search_hotels

3. `compare_hotel_prices`
Compare prices and find the best value options in a location.

4. `get_booking_links`
Get booking links and options for a specific hotel

5. `search_hotels_with_filters`
Search for hotels with advanced filtering options, such as rating and/or amenities.

## Usage Examples
1. Find me hotels in San Francisco for 22 to 24 August 2025 for 2 adults. (tool_call: search_hotels)
2. Get me hotels with a minimum 4 star rating and free WiFi.(tool_call: search_hotels_with_filters)
3. Compare hotel A and B and give me best option.(tool_call: compare_hotel_prices)
4. Get me the booking link for hotel A. (tool_call:get_booking_links)

## Tool calling logs:
![Alt text](log_images\compare_hotel_prices_tool_call.png)
![Alt text](log_images\get_booking_links_tool_call.png)
![Alt text](log_images\get_supported_amenities_tool_call.png)
![Alt text](log_images\search_hotels_tool_call.png)
![Alt text](log_images\search_hotels_with_filters_tool_call.png)

## Usage Example live demo:
[Watch the demo] (https://drive.google.com/file/d/1Tsprx8hK5HHtXiTG_8kUBgD-0A7nQ7nV/view?usp=sharing)

## Acknowledgments
Anthropic for the Model Context Protocol
SerpApi for providing Google Hotels data access
Klavis AI for MCP server development guidelines

## License
MIT License