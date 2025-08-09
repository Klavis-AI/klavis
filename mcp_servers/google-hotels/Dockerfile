FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY mcp_servers/google-hotels/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mcp_servers/google-hotels/ .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_HOTELS_MCP_SERVER_PORT=5000

# Create a non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp
RUN chown -R mcp:mcp /app
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/sse || exit 1

# Run the server (note the correct path based on your structure)
CMD ["python", "server.py"] 