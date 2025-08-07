FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the MCP server files
COPY server.py .
COPY tools/ ./tools/
COPY .env.example .env

# Expose the port the server runs on
EXPOSE 8080

# Command to run the MCP server
CMD ["python", "server.py"]