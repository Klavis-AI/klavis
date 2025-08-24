# amplitude/Dockerfile
FROM python:3.11-slim

# System hardening + build deps (kept minimal)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Do not bake secrets into the image. Use -e / --env-file at runtime.
# Expose nothing; MCP uses stdio.

# Default command: run MCP server over stdio
# Change to "main.py" if you keep that filename
CMD ["python", "server.py"]