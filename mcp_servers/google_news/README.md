# Google News MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **Model-Context Protocol (MCP)** server that exposes Google News through the
[SerpAPI](https://serpapi.com/) search API.
It is function-for-function compatible with other Klavis servers (dual transport,
JSON-RPC 2.0, deterministic JSON), so you can drop it into any LLM workflow that
already speaks MCP.

---

## ✨ Features

| Tool                                  | What it does                                                          |
| ------------------------------------- | --------------------------------------------------------------------- |
| **`google_news_search_news`**         | Full-text keyword search across Google News.                          |

* Strict, documented Pydantic models (`Article`, `Headline`, `Trend`, …).
* Dual transport out-of-the-box
  – **Server-Sent Events** (`/sse`) and **StreamableHTTP** (`/mcp`).
* One-shot JSON response mode (`--json-response` or `JSON_RESPONSE=true`).
* Production-grade logging: file + stderr, request body probe.

Personal opinion: The overall specturm (or most) of SerpAPI's clients can be wrapped into a single server. Maybe it could overcharge the context for the LLM, but a single server only for the google news api could be too much. 
---

## ⚙️ Prerequisites

* A free **SerpAPI** key – sign up at [https://serpapi.com/](https://serpapi.com/).
* Docker **or** Python ≥ 3.12.

Create a file `mcp_servers/google_news/.env` (or export in your shell):

```dotenv
SERPAPI_API_KEY = your_real_key_here
# Uncomment to force one-shot JSON instead of SSE
# JSON_RESPONSE = true
# GOOGLE_NEWS_MCP_SERVER_PORT = 5000   # default
```

---

## 🚀 Running locally

### Option A – Docker (Recommended)

```bash
# from the repo root
docker build -t google-news-mcp -f mcp_servers/google_news/Dockerfile .
docker run --env-file mcp_servers/google_news/.env -p 5000:5000 google-news-mcp
```

The server is now reachable at [http://localhost:5000](http://localhost:5000).

### Option B – Python virtual-env

```bash
cd mcp_servers/google_news
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m klavis_google_news.server --port 5000
```

Deactivate with `deactivate` when you are done.

---

## 🛠 Quick smoke test
From root directory "klavis", navigate to the mcp-clients\src\mcp_clients folder and launch the streamable_http_client.py file, while running the server.

```powershell
cd mcp-clients\src\mcp_clients
python streamable_http_client.py http://localhost:5000/mcp
```

And chat against the server.

---

## 🏗 Project layout (excerpt)

```
mcp_servers/google_news/
├── Dockerfile
├── README.md          ← you are here
├── .env               ← env file
├── requirements.txt          ← requirements
└── klavis_google_news
    ├── server.py      ← dual-transport MCP server
    ├── client.py      ← SerpAPI client interfacing
    ├── errors.py      
    ├── config.py      
    ├── utils.py     
    ├── tools/
    │   ├── search_news.py
    └── models/…
```

---

## 🤝 Contributing

1. Fork, branch, hack.
2. `pre-commit run --all-files`
3. Open a pull request – CI builds the image, runs unit & e2e tests.

Please follow the existing code style (ruff / black) and keep any new tools
strictly idempotent.

---

## 📜 License

This project is licensed under the **MIT License** – see `LICENSE` for details.
