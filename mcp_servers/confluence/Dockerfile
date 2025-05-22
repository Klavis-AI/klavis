FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY mcp_servers/confluence/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mcp_servers/confluence/server.py .
COPY mcp_servers/confluence/tools /app/tools

# Create a sample .env file
RUN echo "CONFLUENCE_BASE_URL=https://your-instance.atlassian.net/wiki\nCONFLUENCE_API_TOKEN=your-api-token\nCONFLUENCE_USERNAME=your-email@example.com\nCONFLUENCE_MCP_SERVER_PORT=5001" > .env

# Expose the port the server runs on
EXPOSE 5001

# Command to run the server
CMD ["python", "server.py"] 