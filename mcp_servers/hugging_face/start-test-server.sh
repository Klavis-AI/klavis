#!/bin/bash
# Start server with environment variables from specified file

# Get env file from parameter, default to .env.test
ENV_FILE=${1:-.env.test}

# Load variables from specified env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE..."
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "No $ENV_FILE found, using defaults..."
fi

echo "Starting server with configuration from $ENV_FILE..."
pnpm dev:watch
