FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Create data directory
RUN mkdir -p /app/calendar-data

# Set permissions for the data directory
RUN chown -R node:node /app/calendar-data

# Switch to non-root user
USER node

# Start the server
CMD ["node", "build/index.js"]