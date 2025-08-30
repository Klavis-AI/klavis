FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY mcp_servers/datadog/requirements.txt .
COPY mcp_servers/datadog/.env.example .env
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY mcp_servers/datadog/server.py .

# Expose the port the server runs on
EXPOSE 5000

# Set default command (update if your main file is different)
CMD ["python", "server.py"]
