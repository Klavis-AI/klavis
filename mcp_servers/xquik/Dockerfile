FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XQUIK_MCP_SERVER_HOST=0.0.0.0

WORKDIR /app

COPY mcp_servers/xquik/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/xquik/server.py .

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import httpx; httpx.get('http://127.0.0.1:5000/health', timeout=5).raise_for_status()"]

CMD ["python", "server.py"]
