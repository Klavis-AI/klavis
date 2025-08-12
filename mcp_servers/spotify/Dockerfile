# Use official Python runtime as a parent image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the project
COPY . .

# Expose port 5001
EXPOSE 5001

# Run the MCP server
CMD ["python", "server.py", "--port", "5001"]
