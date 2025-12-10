FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and source code
COPY mcp_servers/scholarly/requirements.txt .
COPY mcp_servers/scholarly/src ./src

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH to include src directory
ENV PYTHONPATH=/app/src

# Expose the default port
EXPOSE 5000

# Run the MCP server
CMD ["python", "-m", "mcp_scholarly", "--port", "5000"]
