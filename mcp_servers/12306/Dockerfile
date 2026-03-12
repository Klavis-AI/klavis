# Use a Node.js image as the base for building the application
FROM node:22-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY mcp_servers/12306/package.json mcp_servers/12306/package-lock.json* ./

# Install dependencies (ignoring scripts to prevent running the prepare script)
RUN npm install --ignore-scripts

# Copy the rest of the application source code
COPY mcp_servers/12306 .

# Build the application using TypeScript
RUN npm run build

# ---------------------------------------------------------------------------
# Runtime stage
# ---------------------------------------------------------------------------
FROM node:22-slim AS release

# Set the working directory inside the container
WORKDIR /app

# Copy the built application from the builder stage
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json* /app/

# Install only production dependencies
RUN npm ci --omit=dev --ignore-scripts 2>/dev/null || npm install --omit=dev --ignore-scripts

EXPOSE 5000

# Env vars for proxy (set at runtime):
#   PROXY_USERNAME
#   PROXY_PASSWORD
#   PROXY_HOST     – default: p.webshare.io
#   PROXY_PORT     – default: 80
# Alternatively, set HTTPS_PROXY or HTTP_PROXY directly.
CMD ["node", "--dns-result-order=ipv4first", "dist/index.js"]