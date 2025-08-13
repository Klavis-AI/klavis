FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/google_jobs/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code and tools
COPY mcp_servers/google_jobs/server.py .
COPY mcp_servers/google_jobs/tools/ ./tools/

# Expose port (change if your server uses another)
EXPOSE 5000

# Run the server
CMD ["python", "server.py"]
