# Use Node.js LTS as the base image
FROM node:20-slim AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json from notion-atlas directory
COPY mcp_servers/notion-atlas/package*.json ./

# Install dependencies
RUN npm ci --ignore-scripts --omit-dev

# Copy source code from notion-atlas directory
COPY mcp_servers/notion-atlas/ .

# Build the package
RUN npm run build

# Install package globally
RUN npm link

# Minimal image for runtime
FROM node:20-slim

# Copy built package from builder stage
COPY mcp_servers/notion-atlas/scripts/notion-openapi.json /usr/local/scripts/
COPY --from=builder /usr/local/lib/node_modules/@notionhq/notion-mcp-server /usr/local/lib/node_modules/@notionhq/notion-mcp-server
COPY --from=builder /usr/local/bin/notion-mcp-server /usr/local/bin/notion-mcp-server

# Set default environment variables
ENV OPENAPI_MCP_HEADERS="{}"

# Expose port for HTTP transport
EXPOSE 5000

# Set entrypoint with HTTP transport
ENTRYPOINT ["notion-mcp-server", "--transport", "http", "--port", "5000", "--disable-auth"]
