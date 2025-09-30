FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (gcc often needed for some Python deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to avoid annoying build errors
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first to leverage Docker cache
COPY mcp_servers/outlook/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your server and tools
COPY mcp_servers/outlook/server.py .
COPY mcp_servers/outlook/tools/ ./tools/

# Expose the port your server listens on
EXPOSE 5000

# Start the server with unbuffered output (logs show immediately)
CMD ["python", "-u", "server.py"]
