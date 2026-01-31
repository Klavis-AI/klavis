FROM node:lts-alpine

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY mcp_servers/google_workspace_atlas/package.json mcp_servers/google_workspace_atlas/package-lock.json ./

# Install dependencies without running lifecycle scripts, then build
RUN npm install --ignore-scripts

# Copy the rest of the files
COPY mcp_servers/google_workspace_atlas/ .

# Build the TypeScript project
RUN npm run build

# Expose the HTTP server port
EXPOSE 5000

# Run the MCP server
CMD ["node", "build/index.js"]
