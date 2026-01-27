# Copyright 2025 Klavis AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file is part of a derivative work based on clinicaltrialsgov-mcp-server
# by Casey Hand (@cyanheads), available at:
# https://github.com/cyanheads/clinicaltrialsgov-mcp-server

# Use Node.js image as the base for building the application
FROM node:22-alpine AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and bun.lock (we'll convert to npm)
COPY mcp_servers/clinicaltrials/package.json ./

# Install dependencies (use --legacy-peer-deps to handle Bun's looser peer dep resolution)
RUN npm install --ignore-scripts --legacy-peer-deps

# Install esbuild separately as a build tool
RUN npm install -D esbuild --legacy-peer-deps

# Copy the rest of the application source code
COPY mcp_servers/clinicaltrials .

# Create tsconfig.json for TypeScript compilation (Bun projects often rely on defaults)
RUN echo '{ \
  "compilerOptions": { \
    "target": "ES2022", \
    "module": "ESNext", \
    "moduleResolution": "bundler", \
    "esModuleInterop": true, \
    "strict": true, \
    "skipLibCheck": true, \
    "declaration": true, \
    "outDir": "./dist", \
    "rootDir": "./src", \
    "baseUrl": ".", \
    "paths": { \
      "@/*": ["src/*"] \
    }, \
    "experimentalDecorators": true, \
    "emitDecoratorMetadata": true \
  }, \
  "include": ["src/**/*.ts"], \
  "exclude": ["node_modules", "dist"] \
}' > tsconfig.json

# Build with esbuild (bundles and handles path aliases)
RUN npx esbuild src/index.ts \
    --bundle \
    --platform=node \
    --target=node22 \
    --outfile=dist/index.js \
    --format=esm \
    --packages=external \
    --sourcemap \
    --alias:@=./src

# Use a smaller Node.js image for the final image
FROM node:22-slim AS release

# Set the working directory inside the container
WORKDIR /app

# Copy the built application from the builder stage
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/package.json /app/package.json

# Install all dependencies (many "devDependencies" are actually runtime deps in this Bun project)
RUN npm install --ignore-scripts --legacy-peer-deps

# Set environment variables for streamable HTTP transport
ENV MCP_TRANSPORT_TYPE=http
ENV MCP_HTTP_HOST=0.0.0.0
ENV MCP_HTTP_PORT=5000
ENV MCP_LOG_LEVEL=info

# Expose the HTTP port
EXPOSE 5000

# Specify the command to run the application
ENTRYPOINT ["node", "dist/index.js"]
