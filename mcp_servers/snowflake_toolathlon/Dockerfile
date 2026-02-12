FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY mcp_servers/snowflake_toolathlon/pyproject.toml .
COPY mcp_servers/snowflake_toolathlon/runtime_config.json .
COPY mcp_servers/snowflake_toolathlon/src/ ./src/

# Install project dependencies
RUN pip install --no-cache-dir .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the port the server runs on
EXPOSE 5000

# Command to run the server with HTTP transport
# Connection credentials must be provided at runtime via environment variables
# (e.g. SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_DATABASE, etc.)
CMD ["mcp_snowflake_server", "--transport", "http", "--port", "5000"]
