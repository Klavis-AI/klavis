# Build stage
FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files
COPY mcp_servers/playwright/package.json mcp_servers/playwright/package-lock.json* ./

# Install dependencies (ignoring scripts to prevent running the prepare script)
RUN npm install --ignore-scripts

# Copy source code
COPY mcp_servers/playwright .

# Build TypeScript
RUN npm run build

# Production stage - using Microsoft's Playwright Docker image
FROM mcr.microsoft.com/playwright:v1.49.1-noble AS release

WORKDIR /app

# Copy built application from builder stage
COPY --from=builder /app/build /app/build
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json* /app/

# Install only production dependencies
RUN npm ci --omit=dev --ignore-scripts

# Set environment variables
ENV HEADLESS=true
ENV PORT=5000

EXPOSE 5000

# Run the server
ENTRYPOINT ["node", "build/src/index.js"]
