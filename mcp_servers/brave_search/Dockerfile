FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (e.g., gcc for some Python deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements file first to leverage build cache
COPY mcp_servers/brave_search/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY mcp_servers/brave_search/server.py .
COPY mcp_servers/brave_search/tools/ ./tools/

# Expose the port used by the brave_search MCP server (change if needed)
EXPOSE 5000

# Default command to run the server
CMD ["python", "server.py"]
