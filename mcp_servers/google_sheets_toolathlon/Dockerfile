FROM alpine:latest AS base

WORKDIR /app
# Set environment variables for non-interactive installs and minimal locale
ENV LANG=C.UTF-8

# Update and install basic packages for a low resource machine
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        bash \
        curl \
        tini \
        coreutils \
        git

# Set tini as the init system to handle PID 1
ENTRYPOINT ["/sbin/tini", "-s", "--"]

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure uv is on PATH (installer places it in /root/.local/bin for root)
ENV PATH="/root/.local/bin:${PATH}"

COPY mcp_servers/google_sheets_toolathlon/.python-version .

RUN uv venv

FROM base AS builder

COPY mcp_servers/google_sheets_toolathlon/ .

RUN uv sync

# Build the project (produces dist/*.whl)
RUN uv build

FROM base AS runner

COPY --from=builder /app/dist/*.whl /app/

RUN uv pip install /app/*.whl

CMD ["uv", "run", "mcp-google-sheets"]
