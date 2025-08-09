SHELL := /bin/bash

.PHONY: run smoke docker-build docker-run compose-up

run:
	python3 mcp_server_focused.py

smoke:
	@echo "Running initialize and tools/list..."
	@python3 mcp_server_focused.py << 'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF

docker-build:
	docker build -t klavis-mcp-replicate .

docker-run:
	docker run --rm -it --env-file .env klavis-mcp-replicate

compose-up:
	docker compose up --build


