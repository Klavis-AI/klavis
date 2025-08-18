# Use Python slim base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and force stdout flush
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the whole project
COPY . /app

# Run your MCP server (update filename if needed)
CMD ["python", "server.py"]
