FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/google_sheets/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mcp_servers/google_sheets/server.py .
COPY mcp_servers/google_sheets/models.py .
COPY mcp_servers/google_sheets/utils.py .
COPY mcp_servers/google_sheets/exceptions.py .

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py"] 
