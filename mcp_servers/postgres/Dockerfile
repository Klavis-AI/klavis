# First, build the application in the `/app` directory.
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update \
  && apt-get install -y libpq-dev gcc \
  && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY mcp_servers/postgres/pyproject.toml ./
COPY mcp_servers/postgres/src ./src
COPY mcp_servers/postgres/LICENSE ./
COPY mcp_servers/postgres/README.md ./

# Create virtual environment and install dependencies
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -e .


FROM python:3.12-slim-bookworm
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

RUN groupadd -r app && useradd -r -g app app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
  libpq-dev \
  iputils-ping \
  dnsutils \
  net-tools \
  && rm -rf /var/lib/apt/lists/*

COPY mcp_servers/postgres/docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

USER app

# Expose the SSE port
EXPOSE 5000

# Run the postgres-mcp server
# Users can pass a database URI or individual connection arguments:
#   docker run -it --rm postgres-mcp postgres://user:pass@host:port/dbname
#   docker run -it --rm postgres-mcp -h myhost -p 5432 -U myuser -d mydb
ENTRYPOINT ["/app/docker-entrypoint.sh", "postgres-mcp"]
CMD []
