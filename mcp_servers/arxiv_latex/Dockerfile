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

COPY mcp_servers/arxiv_latex/.python-version .

RUN uv venv

FROM base AS builder

COPY mcp_servers/arxiv_latex/ .

RUN uv sync

RUN uv build

FROM base AS runner

COPY --from=builder /app/dist/*.whl /app/

RUN uv pip install /app/*.whl

# Webshare proxy: set these env vars at runtime to route traffic through a proxy.
#   PROXY_USERNAME  – required
#   PROXY_PASSWORD  – required
#   PROXY_HOST      – default: p.webshare.io
#   PROXY_PORT      – default: 80

CMD ["uv", "run", "arxiv-latex-mcp"]
