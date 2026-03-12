FROM node:16-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Set execution permission for CLI
RUN chmod +x dist/cli.js

# Command is provided by smithery.yaml
CMD ["node", "dist/index.js"]