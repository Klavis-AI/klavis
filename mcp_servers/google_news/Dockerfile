# mcp_servers/google_news/Dockerfile
FROM python:3.12-slim

# ───────────────────────────── base image tweaks ─────────────────────────── #
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# 1️⃣  Install Python deps first (leverages Docker layer-cache)
COPY mcp_servers/google_news/requirements.txt ./requirements.txt
COPY mcp_servers/google_news/.env ./.env
RUN pip install --no-cache-dir -r requirements.txt

# 2️⃣  Copy the application package
COPY mcp_servers/google_news/klavis_google_news ./klavis_google_news

# 3️⃣  Expose & launch
#    The server defaults to port 5000 but respects GOOGLE_NEWS_MCP_SERVER_PORT
EXPOSE 5000
CMD ["python", "-m", "klavis_google_news.server"]
