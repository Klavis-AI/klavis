FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY mcp_servers/google_cloud_toolathlon/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_servers/google_cloud_toolathlon/src/ ./src/
COPY mcp_servers/google_cloud_toolathlon/main.py .

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server
CMD ["python", "-m", "src.server"]
