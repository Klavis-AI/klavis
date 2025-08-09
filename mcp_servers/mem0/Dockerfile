FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY mcp_servers/mem0/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/mem0/server.py .
COPY mcp_servers/mem0/tools/ ./tools/

# Expose the port the server runs on
EXPOSE 5000

# Command to run the MCP server
CMD ["uv", "run",  "server.py"]