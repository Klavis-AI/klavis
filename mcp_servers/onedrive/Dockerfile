FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage cache
COPY mcp_servers/onedrive/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY mcp_servers/onedrive/server.py .
COPY mcp_servers/onedrive/tools/ ./tools/

# Expose whatever port your onedrive server uses (adjust if different)
EXPOSE 5000

# Command to run
CMD ["python", "server.py"]
