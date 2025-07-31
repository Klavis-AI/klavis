# Intuit QuickBooks MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Intuit QuickBooks APIs using the python-quickbooks SDK.

## Features

This server provides the following tools for QuickBooks:

- **Customers**: List, get, and create customer records
- **Accounts**: List and get chart of accounts
- **Invoices**: List, get, and create invoices
- **Payments**: Basic payment operations (placeholder)
- **Reports**: Basic report operations (placeholder)

## Environment Variables

Before using this server, you'll need to set up QuickBooks OAuth credentials:

```bash
# Required QuickBooks OAuth credentials
QB_CLIENT_ID=your_app_client_id
QB_CLIENT_SECRET=your_app_client_secret
QB_ACCESS_TOKEN=your_oauth_access_token
QB_REFRESH_TOKEN=your_oauth_refresh_token
QB_REALM_ID=your_company_id
QB_SANDBOX=true  # Set to 'false' for production
```

## Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up QuickBooks App**:
   - Create an app in [Intuit Developer Portal](https://developer.intuit.com/)
   - Get your client ID and secret
   - Use OAuth2 to get access and refresh tokens

3. **Configure environment**:
   ```bash
   export QB_CLIENT_ID="your_client_id"
   export QB_CLIENT_SECRET="your_client_secret"
   export QB_ACCESS_TOKEN="your_access_token"
   export QB_REFRESH_TOKEN="your_refresh_token"
   export QB_REALM_ID="your_realm_id"
   export QB_SANDBOX="true"  # Use sandbox for testing
   ```

## Usage

### Running the Server

```bash
python server.py
```

### Docker

Build and run with Docker:

```bash
docker build -t intuit-mcp-server .
docker run -e QB_CLIENT_ID=... -e QB_CLIENT_SECRET=... intuit-mcp-server
```

### Available Tools

#### Customers

- `list_customers`: List all customers
- `get_customer`: Get customer details by ID
- `create_customer`: Create a new customer

#### Accounts

- `list_accounts`: List chart of accounts
- `get_account`: Get account details by ID

#### Invoices

- `list_invoices`: List invoices with optional filters
- `get_invoice`: Get invoice details by ID
- `create_invoice`: Create a new invoice

### Example Usage

Once connected to an MCP client, you can use tools like:

```json
{
  "tool": "list_customers",
  "arguments": {
    "max_results": 50,
    "active_only": true
  }
}

{
  "tool": "create_customer",
  "arguments": {
    "display_name": "Acme Corp",
    "email": "billing@acme.com",
    "phone": "555-1234"
  }
}

{
  "tool": "create_invoice",
  "arguments": {
    "customer_id": "123",
    "line_items": [
      {
        "description": "Monthly service",
        "amount": 100.00
      }
    ]
  }
}
```

## Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python server.py
```

## QuickBooks OAuth Setup

1. Create an app at [Intuit Developer Portal](https://developer.intuit.com/)
2. Enable the required scopes in your app
3. Complete the OAuth flow to get `access_token` and `refresh_token`
4. Get your `realm_id` (company ID) from the OAuth response

### Sandbox vs Production

- **Sandbox**: Set `QB_SANDBOX=true` (default)
- **Production**: Set `QB_SANDBOX=false` and use production credentials

## Troubleshooting

### Authentication Issues
- Ensure all required environment variables are set
- Check that tokens are not expired
- Verify realm_id matches your QuickBooks company

### Permission Errors
- Ensure your QuickBooks app has the necessary scopes
- Check that user has permissions to access the requested data

### Common Commands
- Check client status: The server will log initialization status on startup
- Verify configuration: Missing credentials will be logged as warnings

## Example Environment File

```bash
# .env
QB_CLIENT_ID=your_client_id_here
QB_CLIENT_SECRET=your_client_secret_here
QB_ACCESS_TOKEN=access_token_from_oauth
QB_REFRESH_TOKEN=refresh_token_from_oauth
QB_REALM_ID=your_company_realm_id
QB_SANDBOX=true
```