FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 reddit-mcp && \
    chown -R reddit-mcp:reddit-mcp /app
USER reddit-mcp

# Expose port (if needed for future HTTP server)
EXPOSE 8000

# Run the MCP server
CMD ["python", "server.py"] 