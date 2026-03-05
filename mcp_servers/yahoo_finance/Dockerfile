FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY mcp_servers/yahoo_finance/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/yahoo_finance/server.py .

CMD ["python", "server.py"]
