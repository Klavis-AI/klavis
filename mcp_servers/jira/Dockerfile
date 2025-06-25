FROM node:22.12-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY mcp_servers/jira/package.json mcp_servers/jira/package-lock.json ./

# Install dependencies (ignoring scripts to prevent running the prepare script)
RUN npm install --ignore-scripts

# Copy the rest of the application source code
COPY mcp_servers/jira .

# Build the application using TypeScript
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