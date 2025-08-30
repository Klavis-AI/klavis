#!/bin/bash

# Entrypoint Wrapper Script
# This script wraps the original MCP server entrypoint to add OAuth support

set -e

# Parse arguments
SERVER_NAME=""
EXEC_COMMAND=()

# Check environment variable to skip OAuth (default: false)
SKIP_OAUTH="${SKIP_OAUTH:-false}"

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
echo "Skip OAuth: $SKIP_OAUTH"

if [[ "$SKIP_OAUTH" == "true" ]]; then
    echo "Skipping OAuth authentication - executing command directly"
    echo "========================================="
else
    # Execute OAuth token acquisition if needed
    echo "Executing OAuth token acquisition..."
    cd /klavis_oauth
    if ! source ./oauth_acquire.sh "$SERVER_NAME"; then
        oauth_exit_code=$?
        echo "OAuth token acquisition failed"
        exit $oauth_exit_code
    fi

    cd - >/dev/null && echo "Back to work folder: $(pwd)"
fi

# Add AUTH_DATA to .env if it exists
if [[ -n "$AUTH_DATA" ]]; then
    echo "AUTH_DATA=$AUTH_DATA" >> .env
    echo "Added AUTH_DATA to .env file"
fi
echo "Executing command: ${EXEC_COMMAND[*]}"
echo "========================================="

# Display Klavis AI Logo before starting the server with rainbow colors
echo ""
printf "    \033[1;31m██╗  ██╗\033[1;33m██╗      \033[1;32m█████╗ \033[1;36m██╗   ██╗\033[1;34m██╗\033[1;35m███████╗     \033[1;91m█████╗ \033[1;93m██╗\033[0m\n"
printf "    \033[1;31m██║ ██╔╝\033[1;33m██║     \033[1;32m██╔══██╗\033[1;36m██║   ██║\033[1;34m██║\033[1;35m██╔════╝    \033[1;91m██╔══██╗\033[1;93m██║\033[0m\n"
printf "    \033[1;31m█████╔╝ \033[1;33m██║     \033[1;32m███████║\033[1;36m██║   ██║\033[1;34m██║\033[1;35m███████╗    \033[1;91m███████║\033[1;93m██║\033[0m\n"
printf "    \033[1;31m██╔═██╗ \033[1;33m██║     \033[1;32m██╔══██║\033[1;36m╚██╗ ██╔╝\033[1;34m██║\033[1;35m╚════██║    \033[1;91m██╔══██║\033[1;93m██║\033[0m\n"
printf "    \033[1;31m██║  ██╗\033[1;33m███████╗\033[1;32m██║  ██║ \033[1;36m╚████╔╝ \033[1;34m██║\033[1;35m███████║    \033[1;91m██║  ██║\033[1;93m██║\033[0m\n"
printf "    \033[1;31m╚═╝  ╚═╝\033[1;33m╚══════╝\033[1;32m╚═╝  ╚═╝  \033[1;36m╚═══╝  \033[1;34m╚═╝\033[1;35m╚══════╝    \033[1;91m╚═╝  ╚═╝\033[1;93m╚═╝\033[0m\n"
echo ""
printf "\033[1;32m    Empowering AI with Seamless Integration\033[0m\n"
printf "\033[1;33m    Starting MCP Server...\033[0m\n"
echo ""

# Execute the original command with all arguments and environment variables preserved
exec "${EXEC_COMMAND[@]}"
