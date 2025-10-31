
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed (gcc is often required for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY mcp_servers/msteams/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY mcp_servers/msteams/server.py .
COPY mcp_servers/msteams/tools/ ./tools/

# Expose the port the server runs on in HTTP mode
EXPOSE 8791

# Set default port for HTTP mode
ENV MS_TEAMS_MCP_SERVER_PORT=8791

# The default command runs the server in HTTP mode.
# To run in stdio mode for Claude Desktop, override the command when running the container.
CMD ["python", "server.py"]
