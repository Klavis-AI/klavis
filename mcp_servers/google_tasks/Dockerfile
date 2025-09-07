FROM python:3.12-slim

WORKDIR /app

# Install any system dependencies needed
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your server code
COPY . .

# Expose port if needed (e.g., if you run a web server, otherwise this is optional)
EXPOSE 5000

# Run your server
CMD ["python", "server.py"]
