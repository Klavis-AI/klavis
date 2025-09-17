FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_servers/reddit_search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/reddit_search/server.py .
COPY mcp_servers/reddit_search/tools/ ./tools/

# Expose the port the server runs on
EXPOSE 5001

# Command to run the server
CMD ["python", "server.py"] 
