# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY mcp_servers/figma/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Figma MCP server code
COPY mcp_servers/figma/ .

# Copy environment file (optional, can be overridden at runtime)
COPY mcp_servers/figma/.env.example .env

# Expose the port
EXPOSE 5002

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["python", "server.py"]