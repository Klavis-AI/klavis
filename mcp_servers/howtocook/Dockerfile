FROM node:20-alpine AS builder

WORKDIR /app

COPY mcp_servers/howtocook/package.json mcp_servers/howtocook/package-lock.json* ./
RUN npm install --ignore-scripts

COPY mcp_servers/howtocook/tsconfig.json ./
COPY mcp_servers/howtocook/src/ ./src/
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY mcp_servers/howtocook/package.json ./
RUN npm install --omit=dev --ignore-scripts

COPY --from=builder /app/build ./build

EXPOSE 5000

CMD ["node", "build/index.js", "--transport", "http", "--port", "5000"]
