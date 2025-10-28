FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY mcp_servers/google_slides/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY mcp_servers/google_slides/ .

# Set the default port
ENV GOOGLE_SLIDES_MCP_SERVER_PORT=5000

# Command to run
CMD ["python", "server.py"]
