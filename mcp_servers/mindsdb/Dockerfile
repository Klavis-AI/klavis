# MindsDB MCP Server Dockerfile
# Production-ready container for MindsDB MCP Server deployment

FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="Klavis AI"
LABEL description="MindsDB MCP Server - Production-ready Model Context Protocol server"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user for security
RUN groupadd -r mcpserver && useradd -r -g mcpserver mcpserver

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mindsdb_server.py .
COPY setup.py .
COPY README.md .
COPY CLAUDE.md .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R mcpserver:mcpserver /app

# Switch to non-root user
USER mcpserver

# Environment variables with defaults
ENV MINDSDB_BASE_URL="http://host.docker.internal:47334/api" \
    LOG_LEVEL="INFO" \
    PYTHONPATH="/app"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (if needed for future HTTP endpoint)
EXPOSE 8080

# Default command - run the MCP server
CMD ["python", "mindsdb_server.py"]