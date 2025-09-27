FROM python:3.12-slim

WORKDIR /app

# Install minimal build deps (google-api-python-client pulls grpcio which needs gcc)
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements first to leverage Docker cache layers
COPY mcp_servers/google_tasks/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY mcp_servers/google_tasks/server.py ./
COPY mcp_servers/google_tasks/auth.py ./
COPY mcp_servers/google_tasks/__init__.py ./
COPY mcp_servers/google_tasks/tools/ ./tools/

# Provide an example env file inside the container (replace or override with -e at runtime)
COPY mcp_servers/google_tasks/.env.example .env

EXPOSE 5000

# Run server on container start
CMD ["python", "server.py"]

