#!/usr/bin/env bash
set -euo pipefail

python3 mcp_server_focused.py << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

echo "Smoke test OK"


