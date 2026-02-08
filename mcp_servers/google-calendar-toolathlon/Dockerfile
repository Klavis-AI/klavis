FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY mcp_servers/google-calendar-toolathlon/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY mcp_servers/google-calendar-toolathlon/ .

# Build the application
RUN npx tsc

# Create data directory
RUN mkdir -p /app/calendar-data

# Set permissions for the data directory
RUN chown -R node:node /app/calendar-data

# Switch to non-root user
USER node

# Expose the HTTP port
EXPOSE 5000

# Start the server
CMD ["node", "build/index.js"]