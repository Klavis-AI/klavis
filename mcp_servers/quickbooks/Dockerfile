FROM python:3.12-slim

WORKDIR /app

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/quickbooks/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_servers/quickbooks/server.py .
COPY mcp_servers/quickbooks/errors.py .
COPY mcp_servers/quickbooks/session_manager.py .
COPY mcp_servers/quickbooks/tools/ ./tools/

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py"] 