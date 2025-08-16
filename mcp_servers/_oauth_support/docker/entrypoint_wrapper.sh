#!/bin/bash

# Entrypoint Wrapper Script
# This script wraps the original MCP server entrypoint to add OAuth support

set -e

# Parse arguments
SERVER_NAME=""
EXEC_COMMAND=()

while [[ $# -gt 0 ]]; do
    case $1 in
    --server-name)
        SERVER_NAME="$2"
        shift 2
        ;;
    --exec)
        shift
        # Collect all remaining arguments as the exec command
        EXEC_COMMAND=("$@")
        break
        ;;
    *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

echo "OAuth Support Layer - Entrypoint Wrapper"
echo "========================================="
echo "Server Name: $SERVER_NAME"
echo "Exec Command: ${EXEC_COMMAND[*]}"

# Execute OAuth token acquisition if needed
echo "Executing OAuth token acquisition..."
cd /klavis_oauth
if ! source ./oauth_acquire.sh "$SERVER_NAME"; then
    oauth_exit_code=$?
    echo "OAuth token acquisition failed"
    exit $oauth_exit_code
fi
cd -

echo "Executing command: ${EXEC_COMMAND[*]}"
echo "========================================="

# Execute the original command with all arguments and environment variables preserved
exec "${EXEC_COMMAND[@]}"
