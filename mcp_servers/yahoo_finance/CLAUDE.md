# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that provides comprehensive financial data from Yahoo Finance. The server exposes 9 tools through MCP for retrieving stock information, financial statements, options data, holder information, and news.

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .
```

### Running the Server
```bash
# Start the MCP server in development mode
uv run server.py
```

### Code Quality Tools
```bash
# Format code with Black (line length: 100)
black .

# Sort imports with isort
isort .

# Type checking (configured for Python 3.11+)
mypy server.py

# Security scanning
bandit server.py
```

### Development Dependencies
Install development tools with:
```bash
uv pip install -e ".[dev]"
```

## Architecture

### Core Structure
- **server.py**: Main MCP server implementation with all tool definitions
- **pyproject.toml**: Project configuration with dependencies and tool settings
- **Single-file architecture**: All functionality is contained in one Python file for simplicity

### MCP Tools Organization
The server implements 9 MCP tools organized into categories:

1. **Stock Information**
   - `get_historical_stock_prices`: OHLCV data with customizable periods/intervals
   - `get_stock_info`: Comprehensive stock data and company details
   - `get_yahoo_finance_news`: Latest news articles
   - `get_stock_actions`: Dividends and splits history

2. **Financial Statements**
   - `get_financial_statement`: Income statement, balance sheet, cash flow (annual/quarterly)
   - `get_holder_info`: Major holders, institutional holders, insider transactions

3. **Options Data**
   - `get_option_expiration_dates`: Available expiration dates
   - `get_option_chain`: Options chain for specific expiration and type

4. **Analyst Information**
   - `get_recommendations`: Analyst recommendations and upgrades/downgrades

### Key Dependencies
- **mcp[cli]**: Model Context Protocol framework (>=1.6.0)
- **yfinance**: Yahoo Finance API client (>=0.2.62)
- **pandas**: Data manipulation for financial data
- **FastMCP**: MCP server framework used for tool definitions

### Data Processing Patterns
- All financial data is returned as JSON strings
- Historical data includes date formatting as ISO strings
- Error handling checks for valid ticker symbols using `company.isin`
- Enum classes define valid options for financial statement types, holder types, and recommendation types

### Configuration Notes
- Python 3.11+ required
- Black formatter configured for 100-character line length
- Type checking enabled with strict mypy configuration
- Uses uv for dependency management instead of pip