FROM node:20-slim AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json from the correct location
COPY mcp_servers/notion-mcp-server/package*.json ./

# Install dependencies
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts

# Copy source code from the correct location
COPY mcp_servers/notion-mcp-server/ ./

# Build the package
RUN --mount=type=cache,target=/root/.npm npm run build

# Minimal image for runtime
FROM node:20-slim

WORKDIR /app

# Copy necessary files for runtime
COPY --from=builder /app/build ./build
COPY --from=builder /app/src ./src
COPY --from=builder /app/scripts/notion-openapi.json ./scripts/
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/index.ts ./

# Set environment variables
ENV PORT=5000
ENV NODE_ENV=production

# Expose the port
EXPOSE 5000

# Install tsx for running TypeScript files directly
RUN npm install -g tsx

# Set entrypoint to run the server with tsx
CMD ["tsx", "index.ts"]