FROM node:22.12-alpine AS builder

COPY . /app

WORKDIR /app

# Install all dependencies
RUN npm install

# Build the project
RUN npm run build

FROM node:22-alpine AS release

# Copy build artifacts and dependencies
COPY --from=builder /app/build /app/build
COPY --from=builder /app/bin /app/bin
COPY --from=builder /app/package.json /app/package.json
COPY --from=builder /app/package-lock.json /app/package-lock.json
COPY --from=builder /app/src /app/src
COPY --from=builder /app/scripts /app/scripts
COPY --from=builder /app/index.ts /app/index.ts

ENV NODE_ENV=production

EXPOSE 5000

WORKDIR /app

# Install dependencies including tsx for running TypeScript directly
RUN npm install --production && npm install -g tsx

# Run the server using the index.ts at the root level
CMD ["tsx", "index.ts"]