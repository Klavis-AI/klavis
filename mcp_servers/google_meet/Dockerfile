FROM node:22-alpine AS builder

WORKDIR /app

COPY mcp_servers/google_meet/package.json mcp_servers/google_meet/package-lock.json ./
RUN npm install --ignore-scripts

COPY mcp_servers/google_meet .
RUN npm run build

FROM node:22-alpine AS release

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json /app/package-lock.json

RUN npm ci --ignore-scripts --omit=dev

EXPOSE 5000

ENTRYPOINT ["node", "dist/index.js"]