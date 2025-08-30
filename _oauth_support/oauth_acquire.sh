#!/bin/bash

# OAuth Token Acquisition Script
# This script handles the OAuth token acquisition process for MCP servers

set -e

SERVER_NAME="$1"

echo "Starting OAuth token acquisition process for: $SERVER_NAME"

# Check if AUTH_DATA environment variable exists and is empty
if [ -z "${AUTH_DATA:-}" ]; then
    echo "AUTH_DATA is not set or empty. Starting OAuth flow for $SERVER_NAME..."

    # Check for required KLAVIS_API_KEY
    if [ -z "${KLAVIS_API_KEY:-}" ]; then
        echo "Error: KLAVIS_API_KEY environment variable must be set for OAuth flow"
        echo "Please set your Klavis API key: https://www.klavis.ai/home/api-keys"
        return 128
    fi

    # Step 1: Create OAuth instance
    echo "Creating OAuth instance for $SERVER_NAME..."
    INSTANCE_RESPONSE=$(curl --silent --request POST \
        --url https://api.klavis.ai/mcp-server/self-hosted/instance/create \
        --header "Authorization: Bearer $KLAVIS_API_KEY" \
        --header 'Content-Type: application/json' \
        --data "{\"serverName\": \"$SERVER_NAME\", \"userId\": \"local_mcp_server\"}")

    INSTANCE_ID=$(echo "$INSTANCE_RESPONSE" | jq -r '.instanceId')
    OAUTH_URL=$(echo "$INSTANCE_RESPONSE" | jq -r '.oauthUrl')

    if [ "$INSTANCE_ID" = "null" ] || [ "$OAUTH_URL" = "null" ]; then
        echo "Error: Failed to create OAuth instance"
        echo "Response: $INSTANCE_RESPONSE"
        return 1
    fi

    # Check if already authorized first, then show URL if needed
    echo "Checking authorization status..."

    # Poll for auth completion with 10 minute timeout
    MSG_FILE=$(mktemp)

    timeout 600 bash -c "
        FIRST_CHECK=true
        while true; do
            AUTH_RESPONSE=\$(curl --silent --request GET \\
                --url \"https://api.klavis.ai/mcp-server/instance/get-auth/$INSTANCE_ID\" \\
                --header \"Authorization: Bearer $KLAVIS_API_KEY\")

            SUCCESS=\$(echo \"\$AUTH_RESPONSE\" | jq -r '.success')

            if [ \"\$SUCCESS\" = \"true\" ]; then
                AUTH_DATA_JSON=\$(echo \"\$AUTH_RESPONSE\" | jq -r '.authData')
                echo \"\$AUTH_DATA_JSON\" > \"$MSG_FILE\"
                exit 0
            elif [ \"\$FIRST_CHECK\" = \"true\" ]; then
                echo \"\"
                printf \"\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n\"
                printf \"\033[1;32m🔗 Please click the link below to authorize access:\033[0m\n\"
                printf \"\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n\"
                echo \"\"
                printf \"\033[1;36m%s\033[0m\n\" \"$OAUTH_URL\"
                echo \"\"
                printf \"\033[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n\"
                echo \"\"
                echo \"Waiting for authorization (timeout: 10 minutes)...\"
                FIRST_CHECK=false
            fi
            sleep 1
        done
    "

    AUTH_DATA=$(cat "$MSG_FILE")
    AUTH_DATA=$(echo $AUTH_DATA | jq -c)
    rm -f "$MSG_FILE"
    TIMEOUT_EXIT_CODE=$?

    if [ $TIMEOUT_EXIT_CODE -eq 124 ]; then
        echo "Timeout: OAuth authorization was not completed within 5 minutes"
        return 1
    elif [ $TIMEOUT_EXIT_CODE -eq 0 ] && [ -f "$MSG_FILE" ]; then
        export AUTH_DATA
        echo "OAuth token acquisition completed successfully for $SERVER_NAME"
    fi
else
    echo "AUTH_DATA already exists, skipping OAuth flow for $SERVER_NAME"
fi

echo "OAuth preparation complete for $SERVER_NAME"
