# Render Deployment Guide

This document explains how to deploy the Office Word MCP Server on Render.

## Required Environment Variables

Set the following environment variables in your Render service:

### `MCP_TRANSPORT`
- **Value**: `sse`
- **Description**: Sets the transport type to Server-Sent Events (SSE) for HTTP communication
- **Required**: Yes (for Render deployment)

### `MCP_HOST`
- **Value**: `0.0.0.0`
- **Description**: Binds the server to all network interfaces
- **Required**: No (defaults to 0.0.0.0)

### `FASTMCP_LOG_LEVEL`
- **Value**: `INFO`
- **Description**: Sets the logging level for FastMCP
- **Required**: No (defaults to INFO)

## How to Set Environment Variables

1. Go to your Render dashboard: https://dashboard.render.com
2. Navigate to your service: `Office-Word-MCP-Server`
3. Click on "Environment" in the left sidebar
4. Add the environment variable:
   - Key: `MCP_TRANSPORT`
   - Value: `sse`
5. Click "Save Changes"

## Deployment

After setting the environment variables:
1. Render will automatically redeploy your service
2. The server will start with SSE transport on the port provided by Render
3. Access your server at: `https://office-word-mcp-server-bzlp.onrender.com/sse`

## Health Check Endpoint

The FastMCP server with SSE transport automatically provides a health check endpoint at:
- `https://your-service.onrender.com/health`

## Troubleshooting

### Server exits with status 1
- **Cause**: Server is running in STDIO mode instead of SSE
- **Fix**: Ensure `MCP_TRANSPORT=sse` is set in environment variables

### Port binding errors
- **Cause**: Server not using Render's PORT environment variable
- **Fix**: This has been fixed in the latest version of main.py

### Cannot connect to server
- **Cause**: Health checks failing
- **Fix**: Ensure SSE transport is enabled and server is listening on 0.0.0.0

