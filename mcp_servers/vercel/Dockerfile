# Stage 1: Build the application
FROM node:20.19-alpine AS builder

WORKDIR /app

# Copy only package files first (relative to context: mcp_servers/vercel)
COPY package.json package-lock.json ./


# Install all dependencies
RUN npm install --ignore-scripts

# Copy rest of the source code
COPY . .


# Build TypeScript
RUN npm run build

# Stage 2: Production image
FROM node:20-alpine AS release

WORKDIR /app

# Copy only necessary built files and package files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json


# Install only production dependencies
RUN npm ci --ignore-scripts --omit=dev

EXPOSE 5000

# Run the application
ENTRYPOINT ["node", "dist/index.js"]
