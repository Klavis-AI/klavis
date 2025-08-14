.PHONY: help install test run build run-docker clean logs

# Default target
help:
	@echo "Freshdesk MCP Server - Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests (if available)"
	@echo "  run         - Run server locally"
	@echo "  build       - Build Docker image"
	@echo "  run-docker  - Run server in Docker"
	@echo "  clean       - Clean up generated files"
	@echo "  logs        - View Docker logs"

# Install dependencies
install:
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Run tests (placeholder for future test implementation)
test:
	@echo "Tests not yet implemented"

# Run server locally
run:
	python server.py

# Build Docker image
build:
	docker build -t freshdesk-mcp-server .

# Run server in Docker
run-docker:
	docker run -p 5000:5000 \
		-e FRESHDESK_API_KEY=$${FRESHDESK_API_KEY} \
		-e FRESHDESK_DOMAIN=$${FRESHDESK_DOMAIN} \
		freshdesk-mcp-server

# Run with docker-compose
compose:
	docker-compose up --build

# Run with docker-compose in background
compose-daemon:
	docker-compose up -d --build

# Stop docker-compose
compose-stop:
	docker-compose down

# Clean up generated files
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# View Docker logs
logs:
	docker-compose logs -f freshdesk-mcp-server

# Health check
health:
	curl -f http://localhost:5000/health || echo "Server not responding"

# Format code (if black is available)
format:
	black . --line-length 100

# Lint code (if flake8 is available)
lint:
	flake8 . --max-line-length 100 --ignore E203,W503
