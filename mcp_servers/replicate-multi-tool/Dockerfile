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
COPY server.py ./server.py
COPY tools ./tools
 
EXPOSE 8000

# Default entrypoint runs the MCP server over HTTP via uvicorn
ENTRYPOINT ["python", "server.py"]


