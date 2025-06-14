FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY mcp_servers/gong/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY mcp_servers/gong/server.py ./
COPY mcp_servers/gong/tools/ ./tools/

# Optionally copy example env file (not required for runtime)
# COPY mcp_servers/gong/.env.example .env

EXPOSE 5000

CMD ["python", "server.py"] 