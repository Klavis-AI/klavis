FROM node:22.12-alpine AS builder

COPY . /app

WORKDIR /app

RUN --mount=type=cache,target=/root/.npm npm install

RUN npm run build

FROM node:22-alpine AS release

COPY --from=builder /app/build /app/build
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json /app/package-lock.json

ENV NODE_ENV=production

EXPOSE 5000

WORKDIR /app

RUN npm ci --ignore-scripts --omit-dev

ENTRYPOINT ["node", "build/index.js"] 