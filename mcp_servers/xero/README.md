# Xero MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-00a393.svg)](https://fastapi.tiangolo.com/)
[![Xero API](https://img.shields.io/badge/Xero_API-v2-00B9F1.svg)](https://developer.xero.com/)

## 📖 Overview

Xero MCP Server is a Model Context Protocol (MCP) implementation that bridges language models and other applications with Xero's Accounting API. It provides a standardized interface for executing Xero accounting operations through various tools defined by the MCP standard.

## 🚀 Features

This server provides the following capabilities through MCP tools:

| Tool | Description |
|------|-------------|
| `list_organisation_details` | Retrieve details about the Xero organisation |
| `list_contacts` | Retrieve a list of contacts from Xero |
| `create_contact` | Create a new contact in Xero |
| `update_contact` | Update an existing contact in Xero |
| `list_invoices` | Retrieve a list of invoices from Xero |
| `create_invoice` | Create a new invoice in Xero |
| `update_invoice` | Update an existing draft invoice in Xero |
| `list_quotes` | Retrieve a list of quotes from Xero (with client-side filtering) |
| `create_quote` | Create a new quote in Xero |
| `update_quote` | Update an existing draft quote in Xero |
| `list_accounts` | Retrieve a list of accounts from Xero |
| `list_items` | Retrieve a list of items from Xero |
| `get_payroll_timesheet` | Retrieve an existing Payroll Timesheet from Xero |

## 🔧 Prerequisites

You'll need one of the following:

- **Docker:** Docker installed and running (recommended)
- **Python:** Python 3.12+ with pip

## ⚙️ Setup & Configuration

### Xero App Setup

1. **Create a Xero App**:
   - Visit the [Xero Developer Portal](https://developer.xero.com/)
   - Create a new application and add it to your developer account
   - Under the "Configuration" section, configure the following scopes:
     - `accounting.settings` (for organization and account access)
     - `accounting.transactions` (for invoices, quotes, and items)
     - `accounting.contacts` (for contact management)
     - `accounting.attachments` (for file attachments)
   - Copy your Client ID and Client Secret

2. **Generate Access Token**:
   - Use Xero's OAuth2 authorization code flow
   - Navigate to OAuth2 > URL Generator in the Xero Developer Portal
   - Generate an access token with the required scopes
   - For testing, you can use the temporary access token provided in the developer console

### Environment Configuration

1. **Create your environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your Xero credentials:
   ```
   XERO_ACCESS_TOKEN=YOUR_ACTUAL_XERO_ACCESS_TOKEN
   XERO_TENANT_ID=YOUR_XERO_TENANT_ID
   XERO_MCP_SERVER_PORT=5000
   ```

## 🏃‍♂️ Running the Server

### Option 1: Docker (Recommended)

The Docker build must be run from the project root directory (`klavis/`):

```bash
# Navigate to the root directory of the project
cd /path/to/klavis

# Build the Docker image
docker build -t xero-mcp-server -f mcp_servers/xero/Dockerfile .

# Run the container
docker run -d -p 5000:5000 --name xero-mcp xero-mcp-server
```

To use your local .env file instead of building it into the image:

```bash
docker run -d -p 5000:5000 --env-file mcp_servers/xero/.env --name xero-mcp xero-mcp-server
```

### Option 2: Python Virtual Environment

```bash
# Navigate to the Xero server directory
cd mcp_servers/xero

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Once running, the server will be accessible at `http://localhost:5000`.

## 🔌 API Usage

The server implements the Model Context Protocol (MCP) standard. Here's an example of how to call a tool:

```python
import httpx

async def call_xero_tool():
    url = "http://localhost:5000/mcp"
    payload = {
        "tool_name": "create_contact",
        "tool_args": {
            "name": "Acme Corporation",
            "email_address": "contact@acme.com",
            "is_customer": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        result = response.json()
        return result
```

## 📋 Common Operations

### Creating a Contact

```python
payload = {
    "tool_name": "create_contact",
    "tool_args": {
        "name": "John Doe",
        "email_address": "john@example.com",
        "is_customer": True,
        "phone_number": "+1234567890"
    }
}
```

### Creating an Invoice

```python
payload = {
    "tool_name": "create_invoice",
    "tool_args": {
        "contact_id": "contact-id-here",
        "reference": "INV-001",
        "line_items": [
            {
                "description": "Consulting Services",
                "quantity": 10,
                "unit_amount": 100.0,
                "account_code": "200"
            }
        ]
    }
}
```

### Creating a Quote

```python
payload = {
    "tool_name": "create_quote",
    "tool_args": {
        "contact_id": "contact-id-here",
        "reference": "QUO-001",
        "expiry_date": "2025-12-31",
        "line_items": [
            {
                "description": "Professional Services",
                "quantity": 5,
                "unit_amount": 150.0,
                "account_code": "200"
            }
        ]
    }
}
```

## 🛠️ Troubleshooting

### Docker Build Issues

- **File Not Found Errors**: If you see errors like `failed to compute cache key: failed to calculate checksum of ref: not found`, this means Docker can't find the files referenced in the Dockerfile. Make sure you're building from the root project directory (`klavis/`), not from the server directory.

### Common Runtime Issues

- **Authentication Failures**: Verify your access token is correct and hasn't expired. Xero access tokens typically have a short lifespan.
- **API Errors**: Check Xero API documentation for error meanings and status codes.
- **Missing Permissions**: Ensure your Xero app has the necessary scopes enabled.
- **Tenant ID Issues**: Make sure you're using the correct Xero Tenant ID for your organization.
- **Rate Limiting**: Xero has rate limits (5000 calls per day). Implement appropriate delays between requests if needed.

### Tool-Specific Issues

- **Quote Updates**: Only DRAFT quotes can be updated. Quotes with other statuses are read-only.
- **Invoice Updates**: Only DRAFT invoices can be modified. Once authorized or paid, invoices become read-only.
- **Line Items**: When updating quotes or invoices, you must provide complete line item information.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.