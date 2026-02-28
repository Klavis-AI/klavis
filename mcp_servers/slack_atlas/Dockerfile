FROM golang:1.24 AS build

ENV CGO_ENABLED=0
ENV GOTOOLCHAIN=local
ENV GOCACHE=/go/pkg/mod

RUN apt-get update  \
  && apt-get install -y --no-install-recommends net-tools curl

WORKDIR /app

COPY mcp_servers/slack_atlas/go.mod mcp_servers/slack_atlas/go.sum ./

RUN --mount=type=cache,target=/go/pkg/mod go mod download

COPY mcp_servers/slack_atlas/ /app/

RUN --mount=type=cache,target=/go/pkg/mod \
    go build -ldflags="-s -w" -o /go/bin/mcp-server ./cmd/slack-mcp-server

FROM build AS dev

RUN --mount=type=cache,target=/go/pkg/mod \
    go install github.com/go-delve/delve/cmd/dlv@v1.25.0 && cp /go/bin/dlv /dlv

WORKDIR /app/mcp-server

EXPOSE 5000

CMD ["mcp-server", "--transport", "streamable-http"]

FROM alpine:3.22 AS production

RUN apk add --no-cache ca-certificates net-tools curl

COPY --from=build /go/bin/mcp-server /usr/local/bin/mcp-server

WORKDIR /app

ENV SLACK_MCP_PORT=5000

EXPOSE 5000

CMD ["mcp-server", "--transport", "streamable-http"]
