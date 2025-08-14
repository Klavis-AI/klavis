FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/mixpanel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/mixpanel/server.py .
COPY mcp_servers/mixpanel/tools/ ./tools/

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py"] 