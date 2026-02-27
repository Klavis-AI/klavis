FROM node:22-alpine AS builder

WORKDIR /app

COPY mcp_servers/exa_atlas/package.json mcp_servers/exa_atlas/package-lock.json* ./

RUN npm install --ignore-scripts

COPY mcp_servers/exa_atlas/src/ ./src/
COPY mcp_servers/exa_atlas/tsconfig.json ./

RUN npm run build

FROM node:22-slim AS release

WORKDIR /app

COPY --from=builder /app/build /app/build
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json* /app/

RUN npm ci --omit=dev --ignore-scripts

EXPOSE 5000

ENTRYPOINT ["node", "build/index.js"]
