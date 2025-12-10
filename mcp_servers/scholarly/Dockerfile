FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire scholarly directory
COPY mcp_servers/scholarly/ .

# Install dependencies using pip
RUN pip install --no-cache-dir .

# Expose the default port
EXPOSE 5000

# Run the MCP server using the installed package
CMD ["python", "-m", "mcp_scholarly", "--port", "5000"]
