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

# Use Node.js image for proper npm install, then run with Bun
FROM node:22-slim AS deps

WORKDIR /app

# Copy package files
COPY mcp_servers/clinicaltrials/package.json ./

# Install dependencies with npm (more reliable than bun for complex packages)
RUN npm install --legacy-peer-deps --ignore-scripts

# Final image with Bun for runtime
FROM oven/bun:1

WORKDIR /app

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules /app/node_modules

# Copy source code
COPY mcp_servers/clinicaltrials .

# Set environment variables for streamable HTTP transport
ENV MCP_TRANSPORT_TYPE=http
ENV MCP_HTTP_HOST=0.0.0.0
ENV MCP_HTTP_PORT=5000
ENV MCP_LOG_LEVEL=info

# Expose the HTTP port
EXPOSE 5000

# Run TypeScript directly with Bun
ENTRYPOINT ["bun", "run", "src/index.ts"]
