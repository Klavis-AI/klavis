# Coinbase MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Coinbase API](https://img.shields.io/badge/Coinbase_API-Advanced_Trade-1652f0.svg)](https://docs.cloud.coinbase.com/advanced-trade/)

## 📖 Overview

The Coinbase MCP Server is a Model Context Protocol (MCP) implementation that provides seamless integration with Coinbase's cryptocurrency platform. This server enables AI applications and language models to access real-time market data, manage cryptocurrency accounts, analyze portfolios, and retrieve trading information through a standardized MCP interface.

The server leverages Coinbase's Advanced Trade API and public market data endpoints to provide comprehensive cryptocurrency functionality while maintaining secure authentication patterns.

## ✨ Features

This server provides the following capabilities through MCP tools:

### 📊 Market Data Tools (No API key required)
- **Real-time Prices**: Get current cryptocurrency prices for any trading pair
- **Historical Data**: Retrieve historical price data with customizable timeframes and granularity
- **Market Analysis**: Access OHLC data, volume, and market statistics

### 💼 Account & Portfolio Tools (Requires API key)
- **Account Management**: List and manage cryptocurrency accounts
- **Balance Tracking**: Get real-time balances for specific accounts
- **Transaction History**: Retrieve detailed transaction records
- **Portfolio Analytics**: Calculate total portfolio value and performance metrics

### 🔍 Product Information Tools (No API key required)
- **Trading Pairs**: Get detailed information about available cryptocurrency products
- **Market Status**: Check trading status and availability for different assets

## 🚀 Quick Start

The server works out of the box with smart defaults. For basic market data usage, you only need:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server (public data only)
python server.py
```

For account features, set your API credentials:

```bash
# Set your API credentials
export COINBASE_API_KEY=your_api_key
export COINBASE_API_SECRET=your_api_secret

# Run the server
python server.py
```

**That's it!** The server includes intelligent rate limiting and error handling by default.

## 📋 Prerequisites

Before you begin, ensure you have the following:

- **Python 3.11+**: Required for running the server
- **Docker** (optional): For containerized deployment
- **Coinbase Account**: For accessing private account data (optional for public market data)
- **API Credentials**: Coinbase API key and secret for account features

## 🛠️ Installation & Setup

### 1. Clone and Navigate

```bash
# Navigate to the Coinbase MCP server directory
cd mcp_servers/coinbase
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the `mcp_servers/coinbase/` directory:

```bash
# Create environment file
touch .env
```

Add the following configuration to your `.env` file:

```env
# === Required API Credentials (for account features) ===
COINBASE_API_KEY=organizations/1234/apiKeys/abcd1234
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIExample123PrivateKey456Content789\nA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC...\n-----END EC PRIVATE KEY-----"

# === Server Configuration ===
COINBASE_MCP_SERVER_PORT=5000
COINBASE_API_BASE_URL=https://api.coinbase.com
COINBASE_EXCHANGE_URL=https://api.exchange.coinbase.com
```

**🔑 Important .env File Notes:**
- The `COINBASE_API_SECRET` **must be enclosed in double quotes** (`"`) to preserve newlines
- Replace the example values with your actual Coinbase API credentials
- Never commit the `.env` file to version control

## 🔑 API Credentials & Configuration

### Obtaining Coinbase API Credentials

#### Step 1: Create a Coinbase Account
1. Sign up at [coinbase.com](https://www.coinbase.com)
2. Complete identity verification if required
3. Enable two-factor authentication (recommended)

#### Step 2: Access API Settings
1. Go to [Coinbase Advanced Trade](https://www.coinbase.com/advanced-trade)
2. Navigate to **Settings** → **API**
3. Or directly visit: [API Settings](https://www.coinbase.com/settings/api)

#### Step 3: Create API Key
1. Click **"Create New API Key"** or **"Generate API Key"**
2. **Choose Permissions**:
   - For **account features**: Select `wallet:accounts:read`, `wallet:transactions:read`
   - For **market data only**: No special permissions needed
3. **Set Signature Algorithm**:
   - **⚠️ IMPORTANT**: For account features, choose **`ECDSA`** signature algorithm
   - If not using account features, **`Ed25519`** signature algorithm will work as well
4. **Add IP Restrictions** (recommended for production):
   - Add your server's IP address
   - Leave blank for development/testing
5. Click **"Create API Key"**

#### Step 4: Save Credentials
1. **Copy API Key**: Save the generated API key (starts with your organization ID)
2. **Copy Private Key**: Save the private key securely
3. **⚠️ Security Note**: The private key is shown only once. Store it securely.

#### Environment Variable Setup

Add your credentials to the `.env` file:

```env
# Your API credentials from Coinbase
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYourPrivateKeyHere\n-----END EC PRIVATE KEY-----"
```

**⚠️ Important**: The `COINBASE_API_SECRET` must be enclosed in double quotes (`"`) in the .env file to preserve the private key format with newlines.

**Important Notes:**
- **Signature Algorithm**: Use `ECDSA` for account features, `Ed25519` for market data only
- **Private Key Format**: Include the full private key with headers and newlines
- **Security**: Never commit credentials to version control
- **Permissions**: Only grant necessary permissions for your use case

### API Key Permissions

| Permission | Required For | Description |
|------------|--------------|-------------|
| `wallet:accounts:read` | Account Tools | View account balances and details |
| `wallet:transactions:read` | Transaction Tools | Access transaction history |

**Note**: Market data and product information tools work without any API credentials.

## 🚀 Running the Server

### Method 1: Direct Python Execution

```bash
# Basic startup
python server.py

# With custom port and logging
python server.py --port 5000 --log-level INFO

# With environment file
python server.py --env-file .env
```

### Method 2: Docker (Recommended)

#### Build Docker Image

```bash
# Build the Docker image
docker build -t coinbase-mcp-server .
```

#### Run Docker Container

```bash
# Run with environment file
docker run -p 5000:5000 --env-file .env coinbase-mcp-server

# Run with inline environment variables
docker run -p 5000:5000 \
  -e COINBASE_API_KEY=your_api_key \
  -e COINBASE_API_SECRET=your_api_secret \
  coinbase-mcp-server
```

### Method 3: Development Mode

```bash
# Install in development mode
pip install -e .

# Run with auto-reload
uvicorn server:app --reload --port 5000
```

## 🔌 API Endpoints

Once the server is running, it exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sse` | GET | Server-Sent Events for MCP communication |
| `/mcp` | POST | Streamable HTTP for MCP requests |

**Default server address**: `http://localhost:5000`

## 🛠️ Available Tools

### Market Data Tools (Public Access)

#### `coinbase_get_prices`
Get current cryptocurrency prices for specified trading pairs.

**Parameters:**
- `symbols` (required): List of trading pairs (e.g., ["BTC-USD", "ETH-USD"])

**Example:**
```json
{
  "name": "coinbase_get_prices",
  "arguments": {
    "symbols": ["BTC-USD", "ETH-USD", "ADA-USD"]
  }
}
```

#### `coinbase_get_historical_prices`
Retrieve historical price data with customizable timeframes.

**Parameters:**
- `symbol` (required): Trading pair (e.g., "BTC-USD")
- `start` (required): Start date in ISO format
- `end` (required): End date in ISO format
- `granularity` (optional): Time interval in seconds (default: 3600)

**Example:**
```json
{
  "name": "coinbase_get_historical_prices",
  "arguments": {
    "symbol": "BTC-USD",
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "granularity": 3600
  }
}
```

#### `coinbase_get_product_details`
Get detailed information about cryptocurrency products and trading pairs.

**Parameters:**
- `product_id` (required): Product identifier (e.g., "BTC-USD")

**Example:**
```json
{
  "name": "coinbase_get_product_details",
  "arguments": {
    "product_id": "BTC-USD"
  }
}
```

### Account & Portfolio Tools (Requires API Key)

#### `coinbase_get_accounts`
List all cryptocurrency accounts associated with your Coinbase profile.

**Parameters:**
- `limit` (optional): Maximum number of accounts to return

**Example:**
```json
{
  "name": "coinbase_get_accounts",
  "arguments": {
    "limit": 50
  }
}
```

#### `coinbase_get_account_balance`
Get the current balance for a specific account.

**Parameters:**
- `account_id` (required): Account identifier

**Example:**
```json
{
  "name": "coinbase_get_account_balance",
  "arguments": {
    "account_id": "your_account_id"
  }
}
```

#### `coinbase_get_transactions`
Retrieve transaction history for an account.

**Parameters:**
- `account_id` (required): Account identifier
- `limit` (optional): Maximum number of transactions to return

**Example:**
```json
{
  "name": "coinbase_get_transactions",
  "arguments": {
    "account_id": "your_account_id",
    "limit": 100
  }
}
```

#### `coinbase_get_portfolio_value`
Calculate the total value of your cryptocurrency portfolio.

**Parameters:**
- `currency` (optional): Currency for valuation (default: "USD")

**Example:**
```json
{
  "name": "coinbase_get_portfolio_value",
  "arguments": {
    "currency": "USD"
  }
}
```

## 🔐 Authentication & Security

### JWT Token Authentication

The server uses JWT (JSON Web Token) authentication for accessing private Coinbase API endpoints:

- **Token Expiration**: JWT tokens expire after 2 minutes for security
- **Automatic Generation**: Fresh tokens are generated for each API request
- **Signature Algorithm**: Uses ECDSA or Ed25519 based on your API key configuration
- **Secure Headers**: All requests include proper authentication headers

### Public & Private Endpoints

#### Public Endpoints (No Authentication Required)
- Market data (current prices, historical data)
- Product information and trading pairs
- General market statistics

#### Private Endpoints (API Key Required)
- Account information and balances
- Transaction history
- Portfolio data and analytics


## 📊 Rate Limits & Performance

### Coinbase API Rate Limits

For the latest and most accurate rate limit information, please refer to the official Coinbase documentation:

- **Coinbase Consumer APIs**: [Coinbase App API Rate Limiting](https://docs.cdp.coinbase.com/coinbase-app/api-architecture/rate-limiting#coinbase-app-rate-limiting)
- **Coinbase Exchange APIs**: [Coinbase Exchange API Rate Limits](https://docs.cdp.coinbase.com/exchange/rest-api/rate-limits)

### Server Configuration

The server includes built-in rate limiting with configurable limits:

```env
# Conservative defaults to avoid hitting API limits
COINBASE_DEFAULT_RATE_LIMIT=2
COINBASE_MARKET_DATA_RATE_LIMIT=3
COINBASE_ACCOUNTS_RATE_LIMIT=2
COINBASE_PRODUCTS_RATE_LIMIT=2
```

### Retry Configuration

Automatic retry with exponential backoff:

```env
COINBASE_MAX_RETRY_ATTEMPTS=3
COINBASE_INITIAL_DELAY=1.0
COINBASE_MAX_DELAY=10.0
COINBASE_BACKOFF_FACTOR=2.0
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Error**: `Invalid API key or signature`

**Solutions:**
```bash
# Verify your credentials
echo $COINBASE_API_KEY
echo $COINBASE_API_SECRET

# Check signature algorithm
# Use ECDSA for account features, Ed25519 for market data only

# Verify private key format
cat .env | grep COINBASE_API_SECRET
```

#### 2. Rate Limiting

**Error**: `Rate limit exceeded`

**Solutions:**
```bash
# Increase delays in .env file
COINBASE_DEFAULT_RATE_LIMIT=1  # Slower requests
COINBASE_INITIAL_DELAY=2.0     # Longer delays

# Check your API usage in Coinbase dashboard
```

#### 3. Network Connectivity

**Error**: `Connection timeout` or `DNS resolution failed`

**Solutions:**
```bash
# Test API connectivity
curl -I https://api.coinbase.com/v2/time

# Check firewall settings
# Verify internet connection
# Check if running behind corporate proxy
```

#### 4. Docker Issues

**Error**: `Environment variables not found`

**Solutions:**
```bash
# Verify .env file exists
ls -la .env

# Check Docker environment loading
docker run --env-file .env coinbase-mcp-server env | grep COINBASE

# Rebuild image if needed
docker build --no-cache -t coinbase-mcp-server .
```


## 📝 Example Usage

### Basic Market Analysis

```python
import asyncio
import aiohttp

async def get_bitcoin_price():
    async with aiohttp.ClientSession() as session:
        payload = {
            "method": "tools/call",
            "params": {
                "name": "coinbase_get_prices",
                "arguments": {"symbols": ["BTC-USD"]}
            }
        }
        
        async with session.post(
            "http://localhost:5000/mcp",
            json=payload
        ) as response:
            result = await response.json()
            print(f"Bitcoin Price: {result}")

# Run the example
asyncio.run(get_bitcoin_price())
```

### Portfolio Analysis

```python
async def analyze_portfolio():
    # Get all accounts
    accounts_payload = {
        "method": "tools/call",
        "params": {
            "name": "coinbase_get_accounts",
            "arguments": {}
        }
    }
    
    # Get portfolio value
    portfolio_payload = {
        "method": "tools/call", 
        "params": {
            "name": "coinbase_get_portfolio_value",
            "arguments": {"currency": "USD"}
        }
    }
    
    # Process results...
```

## 📖 Additional Resources

- **[Coinbase API Documentation](https://docs.cloud.coinbase.com/advanced-trade/)** - Official API reference
- **[Rate Limiting Best Practices](https://docs.cloud.coinbase.com/advanced-trade/docs/auth#rate-limiting)** - Coinbase rate limit guidelines


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Follow the existing code structure.
2. Add new tools to the appropriate files in the `tools/` directory.
3. Update `tools/__init__.py` to export new functions
4. Add tools calls and definitions to server.py
5. Update the README with new functionalities


## 📜 License

This project follows the same license as the parent Klavis project.