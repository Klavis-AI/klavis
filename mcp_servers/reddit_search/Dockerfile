FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_servers/reddit_search/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/reddit_search/main.py .
COPY mcp_servers/reddit_search/tools.py .

# Expose the port the server runs on
EXPOSE 5001

# Command to run the server
CMD ["python", "main.py", "--port", "5001"] 
