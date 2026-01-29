#!/bin/bash
# Bash script for building and pushing Docker image

GITHUB_USERNAME="evalstate"
IMAGE_NAME="hf-mcp-server"
VERSION=$(date +"%Y%m%d-%H%M%S")

# Build the Docker image
docker build -t ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:latest .
docker tag ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:latest ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION}

# Push the image to GitHub Container Registry
docker push ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:latest
docker push ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION}

echo "Build and push completed successfully"
echo "Image: ghcr.io/${GITHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"