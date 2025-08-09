FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install optional build tools for dependencies that may need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY mcp_server_focused.py ./mcp_server_focused.py
COPY tools ./tools

# Default entrypoint runs the MCP server over stdio
ENTRYPOINT ["python", "mcp_server_focused.py"]


