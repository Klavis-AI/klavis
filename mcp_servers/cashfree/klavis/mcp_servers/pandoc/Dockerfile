FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    lmodern \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements first to leverage Docker cache
COPY mcp_servers/pandoc/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY mcp_servers/pandoc/server.py .
COPY mcp_servers/pandoc/.env.example .env

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py"] 