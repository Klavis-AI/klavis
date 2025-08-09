# Use the Python base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY mcp_servers/tavily/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mcp_servers/tavily/src /app/src

# Create a sample .env file (optional and for documentation/testing only)
RUN echo "TAVILY_API_KEY=your_api_key\nTAVILY_MCP_SERVER_PORT=5002" > .env

# Expose the port the server runs on
EXPOSE 5002

# Command to run the server
CMD ["python", "src/server.py"]
