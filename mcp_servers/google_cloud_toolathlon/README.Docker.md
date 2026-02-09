# Docker Guide for Google Cloud MCP Server

This guide explains how to build and run the Google Cloud MCP Server using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier deployment)
- Google Cloud Project with appropriate APIs enabled
- Service account key file (optional, if not using default credentials)

## Quick Start with Docker Compose

1. **Set environment variables:**

Create a `.env` file in this directory:

```bash
# Required
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional: If using service account key
GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json

# Optional: Access control lists (comma-separated)
ALLOWED_BUCKETS=bucket1,bucket2
ALLOWED_DATASETS=dataset1,dataset2
ALLOWED_LOG_BUCKETS=log-bucket1
ALLOWED_INSTANCES=instance1,instance2
```

2. **Place your service account key (optional):**

If using a service account key file:
- Place your `service-account-key.json` in this directory
- Uncomment the volumes section in `docker-compose.yml`

3. **Start the server:**

```bash
docker-compose up -d
```

4. **View logs:**

```bash
docker-compose logs -f
```

5. **Stop the server:**

```bash
docker-compose down
```

## Building and Running with Docker Commands

### Build the Image

From the **repository root** directory:

```bash
docker build -f mcp_servers/google_cloud_toolathlon/Dockerfile -t google-cloud-mcp .
```

### Run the Container

#### Using Default Credentials

```bash
docker run -d \
  --name google-cloud-mcp \
  -p 5000:5000 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  google-cloud-mcp
```

#### Using Service Account Key

```bash
docker run -d \
  --name google-cloud-mcp \
  -p 5000:5000 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json:ro \
  google-cloud-mcp
```

#### With Access Controls

```bash
docker run -d \
  --name google-cloud-mcp \
  -p 5000:5000 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -e ALLOWED_BUCKETS=bucket1,bucket2 \
  -e ALLOWED_DATASETS=dataset1,dataset2 \
  -e ALLOWED_INSTANCES=instance1,instance2 \
  google-cloud-mcp
```

## Accessing the Server

Once running, the server exposes two endpoints:

- **SSE endpoint:** http://localhost:5000/sse
- **StreamableHTTP endpoint:** http://localhost:5000/mcp

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | Your Google Cloud Project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | No | Path to service account key file |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 5000) |
| `ALLOWED_BUCKETS` | No | Comma-separated list of allowed GCS buckets |
| `ALLOWED_DATASETS` | No | Comma-separated list of allowed BigQuery datasets |
| `ALLOWED_LOG_BUCKETS` | No | Comma-separated list of allowed Cloud Logging buckets |
| `ALLOWED_INSTANCES` | No | Comma-separated list of allowed Compute Engine instances |
| `AUTH_DATA` | No | Base64-encoded OAuth auth data |

## Troubleshooting

### Permission Denied Errors

Ensure your service account has the necessary permissions:
- BigQuery Data Editor
- Storage Admin (or specific bucket permissions)
- Logging Admin
- Compute Admin

### Connection Refused

Check if the container is running:
```bash
docker ps
```

View container logs:
```bash
docker logs google-cloud-mcp
```

### Health Check Failing

Verify the server is responding:
```bash
curl http://localhost:5000/sse
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use minimal permissions** for service accounts
3. **Implement access control lists** using the ALLOWED_* environment variables
4. **Use secrets management** in production (e.g., Docker secrets, Kubernetes secrets)
5. **Regularly rotate** service account keys
6. **Use read-only mounts** for credential files (`:ro`)

## Production Deployment

For production use:

1. Use orchestration platforms (Kubernetes, Docker Swarm)
2. Implement proper secrets management
3. Set up monitoring and alerting
4. Use health checks and restart policies
5. Configure resource limits
6. Enable TLS/SSL termination at load balancer
7. Use private container registries

## Additional Resources

- [Main README](README.md)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication)
- [Docker Documentation](https://docs.docker.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
