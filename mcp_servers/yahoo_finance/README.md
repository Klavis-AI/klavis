# Yahoo Finance MCP Server

A Model Context Protocol (MCP) server that exposes real-time quotes, symbol search, corporate actions, option chains, and historical price data from Yahoo Finance. This server wraps the `yfinance` SDK and presents curated, JSON-friendly tool outputs suitable for LLMs and agent workflows.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended)

If you use the Klavis platform, you can get instant access to hosted MCP servers and managed keys. See the Klavis dashboard for details and keys.

### 🐳 Using Docker (Self-hosting)

Build and run locally:

```bash
docker build -t yahoo-finance-mcp mcp_servers/yahoo_finance
docker run -p 5000:5000 yahoo-finance-mcp
```

### Run prebuilt image

If you'd prefer to run a prebuilt image from the GitHub Container Registry:

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/yahoo-finance-mcp-server:latest

# Run Yahoo Finance MCP Server
docker run -p 5000:5000 \
	ghcr.io/klavis-ai/yahoo-finance-mcp-server:latest
```

> Note: Yahoo Finance doesn't require an API key as it uses free public data from Yahoo Finance.


## 🛠️ Available Tools

- `get_yahoo_finance_quote` — Live market snapshot (price, range, volume + profile metadata).
- `get_yahoo_finance_historical_prices` — Historical OHLCV candles with range/interval and optional start/end.
- `get_yahoo_finance_dividends` — Declared cash dividends, date-windowed and limited.
- `get_yahoo_finance_splits` — Stock split history with optional date filters.
- `get_yahoo_finance_option_chain` — Option chain (calls/puts/both) for a chosen expiration.
- `search_yahoo_finance_entities` — Free-text search for tickers, funds, and companies.


## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | https://www.klavis.ai/docs |
| **💬 Community** | https://discord.gg/p7TuTEcssn |
| **🐛 Issues** | https://github.com/klavis-ai/klavis/issues |

## 🤝 Contributing

Contributions are welcome — please follow the repository guidelines in [CONTRIBUTING.md](../../CONTRIBUTING.md). Per the MCP Server Guide, include a short demo (video/screenshots) proving tool discovery and usage when adding new tools.

## 📜 License

Apache 2.0 - see [LICENSE](../../LICENSE) for details.

---

<div align="center">
	<p><strong>🚀 Supercharge AI Workflows with Real-time Market Data</strong></p>
	<p>
		<a href="https://www.klavis.ai">Klavis</a> •
		<a href="https://www.klavis.ai/docs">Documentation</a> •
		<a href="https://discord.gg/p7TuTEcssn">Community</a>
	</p>
</div>
