# Google Finance MCP Server

📌 **Model Context Protocol (MCP) Server for Google Finance**  
This project is a Model Context Protocol (MCP) server that provides atomic tools for interacting with Google Finance (via Twelve Data API) using FastAPI. It can fetch stock prices, historical data, trending tickers, and company profiles.

---

## **⚙️ Features**

- ✅ Real-time stock price lookup  
- ✅ Historical price data with date range  
- ✅ Market news with trending tickers  
- ✅ Detailed company profiles (industry, sector, website, summary)  
- ✅ Built following **Klavis AI MCP Server Guidelines**  
- ✅ Modular, atomic tool design for AI agents  

---

## **🧩 Tools Overview (Endpoints)**

| Endpoint              | Purpose                                           |
|-----------------------|---------------------------------------------------|
| `/get_stock_price`    | Fetch the current stock price for a ticker        |
| `/get_historical_data`| Retrieve historical closing prices for a ticker   |
| `/get_market_news`    | Get trending tickers and market news              |
| `/get_company_info`   | Fetch detailed company profile information        |

---

## **🚀 Setup Instructions**

### **🔧 Local Setup**

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd klavis/mcp_servers/google-finance
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install python-dotenv
   ```

3. **Set your Twelve Data API Key:**  
   Create a `.env` file:
   ```
   TWELVE_API_KEY=your_api_key_here
   ```

4. **Start the server:**
   ```bash
   uvicorn server:app --reload
   ```

5. **Access the server:**
   ```
   http://127.0.0.1:8000
   ```

6. **Swagger UI (optional):**
   ```
   http://127.0.0.1:8000/docs
   ```

---

## **📡 Example API Calls**

### 1. **Get Stock Price**
```bash
GET /get_stock_price?ticker=AAPL
```
**Response:**
```json
{
  "ticker": "AAPL",
  "price": 190.23,
  "currency": "USD"
}
```

### 2. **Get Historical Data**
```bash
GET /get_historical_data?ticker=AAPL&start_date=2024-01-01&end_date=2024-02-01
```

### 3. **Get Market News**
```bash
GET /get_market_news
```

### 4. **Get Company Info**
```bash
GET /get_company_info?ticker=AAPL
```

---

## **🏗️ System Architecture**

```
google-finance/
├── server.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── tools/
│   ├── __init__.py
│   ├── get_stock_price.py
│   ├── get_historical_data.py
│   ├── get_market_news.py
│   └── get_company_info.py
├── README.md
```

Each tool is independent and focused on a single function.  
`server.py` orchestrates these tools and exposes them via FastAPI.

---

## **⚠️ Limitations & Future Improvements**

### Current Limitations
- Uses Twelve Data API (may have rate limits)  
- No caching or authentication implemented  

### Future Enhancements
- Add caching for improved performance  
- Support additional financial metrics and endpoints  
- Improve error handling and add retry logic  

---

## **🙋 Contact**
**Badhri Srinivasan**
