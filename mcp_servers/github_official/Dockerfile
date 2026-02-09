FROM golang:1.25.6-alpine AS build
ARG VERSION="dev"

# Set the working directory
WORKDIR /build

# Install git
RUN apk add --no-cache git

# Copy source code from the subdirectory (build context is repo root)
COPY mcp_servers/github_official/ .

# Build the server
RUN CGO_ENABLED=0 go build -ldflags="-s -w -X main.version=${VERSION} -X main.commit=$(git rev-parse HEAD) -X main.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    -o /bin/github-mcp-server ./cmd/github-mcp-server

# Make a stage to run the app
FROM gcr.io/distroless/base-debian12

# Add required MCP server annotation
LABEL io.modelcontextprotocol.server.name="io.github.github/github-mcp-server"

# Set the working directory
WORKDIR /server
# Copy the binary from the build stage
COPY --from=build /bin/github-mcp-server .
# Expose the default port
EXPOSE 5000
# Set the entrypoint to the server binary
ENTRYPOINT ["/server/github-mcp-server"]
# Default arguments for ENTRYPOINT
CMD ["http", "--port", "5000"]
