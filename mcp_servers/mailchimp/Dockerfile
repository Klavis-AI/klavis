FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/mailchimp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server files
COPY mcp_servers/mailchimp/server.py .
COPY mcp_servers/mailchimp/tools/ ./tools/

# Copy environment file (optional - can be overridden at runtime)
#COPY mcp_servers/mailchimp/.env .env

# Expose the port the server runs on
EXPOSE 5001

# Command to run the server
CMD ["python", "server.py"]