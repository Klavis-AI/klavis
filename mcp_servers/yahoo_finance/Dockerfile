FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY mcp_servers/yahoo_finance/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code, tools, and configuration samples
COPY mcp_servers/yahoo_finance/ ./

EXPOSE 5000

CMD ["python", "server.py"]
