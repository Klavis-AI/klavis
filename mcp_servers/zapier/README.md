# Zapier MCP Server

A Model Context Protocol (MCP) server for Zapier integration that provides tools to manage workflows, tasks, webhooks, and apps.

## Features

- **Workflow Management**: Create, read, update, and delete Zapier workflows
- **Task History**: Retrieve task execution history and details
- **Webhook Management**: Create and manage webhooks for workflow triggers
- **App Integration**: List and manage connected Zapier apps
- **Enterprise Architecture**: Built with design patterns and clean architecture

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd mcp_servers/zapier
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
echo "ZAPIER_API_KEY=your_api_key_here" > .env
```

4. **Run the server**
```bash
python server.py
```

## Configuration

Set the following environment variables:

```bash
ZAPIER_API_KEY=your_zapier_api_key
API_BASE_URL=https://api.zapier.com/v1
API_TIMEOUT=30
LOG_LEVEL=INFO
```

## Available Tools

### Workflow Tools
- `list_workflows`: List all workflows
- `get_workflow`: Get workflow details
- `create_workflow`: Create a new workflow
- `update_workflow`: Update existing workflow
- `delete_workflow`: Delete a workflow
- `trigger_workflow`: Manually trigger a workflow

### Task Tools
- `list_tasks`: List task execution history
- `get_task`: Get task details

### Webhook Tools
- `list_webhooks`: List all webhooks
- `create_webhook`: Create a new webhook
- `get_webhook`: Get webhook details

### App Tools
- `list_apps`: List connected apps
- `get_app`: Get app details
- `connect_app`: Connect a new app

## Usage Examples

### List Workflows
```python
# List all workflows
result = await call_tool("list_workflows", {})
```

### Create Workflow
```python
# Create a new workflow
workflow_data = {
    "title": "Email to Slack",
    "description": "Send email notifications to Slack",
    "trigger_app": "gmail",
    "trigger_event": "new_email",
    "action_app": "slack",
    "action_event": "send_message"
}
result = await call_tool("create_workflow", workflow_data)
```

### Get Task History
```python
# Get task execution history
result = await call_tool("list_tasks", {"workflow_id": "workflow_123"})
```

## Testing

Run the test suite:

```bash
# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --specific interfaces entities

# Run with verbose output
python tests/run_tests.py --verbose
```

## Architecture

This server implements enterprise-grade design patterns:

- **Factory Pattern**: Component creation and dependency injection
- **Repository Pattern**: Data access abstraction
- **Service Pattern**: Business logic layer
- **Strategy Pattern**: Algorithm selection
- **Decorator Pattern**: Cross-cutting concerns
- **Clean Architecture**: Layered architecture with clear separation

## Docker

Build and run with Docker:

```bash
# Build the image
docker build -t zapier-mcp-server .

# Run the container
docker run -e ZAPIER_API_KEY=your_key zapier-mcp-server
```
