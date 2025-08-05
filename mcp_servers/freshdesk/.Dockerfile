FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/freshdesk/pyproject.toml ./
COPY mcp_servers/freshdesk/.env.example .env
RUN uv init 
RUN uv pip sync

COPY mcp_servers/freshdesk/server.py .

EXPOSE 5000

CMD ["python", "server.py"] 