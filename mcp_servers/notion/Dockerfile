FROM node:22.12-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY mcp_servers/notion/package.json mcp_servers/notion/package-lock.json ./

# Install dependencies (ignoring scripts to prevent running the prepare script)
RUN npm install --ignore-scripts

# Copy the rest of the application source code
COPY mcp_servers/notion .

# Build the application using TypeScript
RUN npm run build

FROM node:22-alpine AS release

# Copy build artifacts and dependencies
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