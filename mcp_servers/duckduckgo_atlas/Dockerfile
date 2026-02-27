FROM alpine:latest AS base

WORKDIR /app

ENV LANG=C.UTF-8

RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        bash \
        curl \
        tini \
        coreutils \
        git

ENTRYPOINT ["/sbin/tini", "-s", "--"]

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

COPY mcp_servers/duckduckgo_atlas/.python-version .

RUN uv venv

FROM base AS builder

COPY mcp_servers/duckduckgo_atlas/ .

RUN uv sync

RUN uv build

FROM base AS runner

COPY --from=builder /app/dist/*.whl /app/

RUN uv pip install /app/*.whl

CMD ["uv", "run", "duckduckgo-mcp-server"]
