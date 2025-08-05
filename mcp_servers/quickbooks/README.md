# QuickBooks MCP Server

A Model Context Protocol (MCP) server for QuickBooks integration, providing comprehensive accounting and business management capabilities.

## Features

### Account Management
- **List Accounts**: List all chart of accounts with filtering options
- **Get Account**: Retrieve detailed account information by ID
- **Create Account**: Create new accounts in the chart of accounts
- **Update Account**: Modify existing account details
- **Search Accounts**: Search accounts with advanced filters

### Customer Management
- **List Customers**: List all customers with pagination support
- **Get Customer**: Retrieve detailed customer information by ID
- **Create Customer**: Create new customer records with billing/shipping addresses
- **Update Customer**: Modify existing customer information
- **Search Customers**: Search customers with advanced filters
- **Activate/Deactivate Customer**: Enable or disable customer records

### Invoice Operations
- **Create Invoice**: Generate new invoices with line items and customer details
- **Get Invoice**: Retrieve complete invoice information by ID
- **List Invoices**: List all invoices with pagination support
- **Update Invoice**: Modify existing invoice details
- **Search Invoices**: Advanced invoice search with date ranges, amounts, and status filters
- **Send Invoice**: Email invoices to customers with delivery tracking
- **Void Invoice**: Void invoices while maintaining audit trail
- **Delete Invoice**: Permanently remove invoices (use with caution)
### Payment Processing
- **Create Payment**: Record customer payments and apply to invoices
- **Get Payment**: Retrieve payment details by ID
- **List Payments**: List all payments with pagination support
- **Update Payment**: Modify existing payment records
- **Search Payments**: Search payments with advanced filters including date ranges and amounts
- **Send Payment**: Email payment receipts to customers
- **Void Payment**: Void payments while maintaining audit trail
- **Delete Payment**: Permanently remove payments (use with caution)

### Vendor Management
- **List Vendors**: List all vendors with filtering options
- **Get Vendor**: Retrieve detailed vendor information by ID
- **Create Vendor**: Create new vendor records
- **Update Vendor**: Modify existing vendor information
- **Search Vendors**: Search vendors with advanced filters
- **Activate/Deactivate Vendor**: Enable or disable vendor records

## Prerequisites

### QuickBooks App Requirements

Before using this MCP server, you need to create a QuickBooks app at [Intuit Developer Portal](https://developer.intuit.com/) with the following permissions:

#### Required Scopes
- **com.intuit.quickbooks.accounting** - Access to accounting data including customers, invoices, payments, accounts, and vendors
- **com.intuit.quickbooks.payment** - Payment processing capabilities (if using payment features)

#### App Configuration
1. **App Type**: Choose "Web App" for OAuth 2.0 flow
2. **Redirect URIs**: Configure appropriate redirect URIs for your OAuth flow
3. **Webhooks**: Optional - configure if you need real-time notifications

> **Note**: The server supports both Sandbox and Production environments. Use Sandbox for development and testing.

## Available Tools

The server provides comprehensive tools across all major QuickBooks accounting areas. For the most up-to-date list of available tools and their parameters, you can:

1. **List tools via API**: Call the `tools/list` method after starting the server
2. **Check source code**: Refer to the individual tool modules in the `./tools/` directory
3. **Use MCP Inspector**: Run `npx @modelcontextprotocol/inspector python server.py` for interactive exploration

## Quick Start

### 1. Setup Environment Variables

Copy the example environment file and configure your QuickBooks credentials:

```bash
cp .env.example .env
```

Edit `.env` with your QuickBooks app credentials:

```bash
# Server Port Configuration (optional)
QB_MCP_SERVER_PORT=5001

# QuickBooks OAuth Credentials (required)
QB_ACCESS_TOKEN=your_access_token_here
QB_REALM_ID=your_company_realm_id_here

# Environment: 'sandbox' for testing, 'production' for live data
QB_ENVIRONMENT=sandbox
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Server

```bash
python server.py
```

The server will validate your QuickBooks connection on startup and supports dual transport modes.

### 4. Use as HTTP Server

The server supports both SSE and StreamableHTTP transport modes:

**SSE Endpoint:**
```bash
curl -X GET http://localhost:5001/sse \
  -H "x-qb-access-token: YOUR_QB_ACCESS_TOKEN" \
  -H "x-qb-realm-id: YOUR_QB_REALM_ID" \
  -H "x-qb-environment: sandbox"
```

**StreamableHTTP Endpoint:**
```bash
curl -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -H "x-qb-access-token: YOUR_QB_ACCESS_TOKEN" \
  -H "x-qb-realm-id: YOUR_QB_REALM_ID" \
  -H "x-qb-environment: sandbox" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### 5. Use as MCP Server

Add to your MCP client configuration:

```json
{
  "servers": {
    "quickbooks": {
      "type": "http",
      "url": "http://localhost:5001/mcp",
      "headers": {
        "x-qb-access-token": "YOUR_QB_ACCESS_TOKEN",
        "x-qb-realm-id": "YOUR_QB_REALM_ID",
        "x-qb-environment": "sandbox"
      }
    }
  }
}
```

## Authentication & Setup

### Obtaining QuickBooks Credentials

To use this MCP server, you need to create a QuickBooks app and obtain OAuth credentials:

#### 1. Create a QuickBooks App

1. Go to the [Intuit Developer Portal](https://developer.intuit.com/)
2. Sign in with your Intuit account
3. Click "Create an app"
4. Choose "QuickBooks Online and Payments" as the platform
5. Select appropriate scopes (accounting access required)
6. Complete app creation and note your Client ID and Client Secret

#### 2. Implement OAuth 2.0 Flow

**Authorization URL:**
```
https://appcenter.intuit.com/connect/oauth2?
  client_id=YOUR_CLIENT_ID&
  scope=com.intuit.quickbooks.accounting&
  redirect_uri=YOUR_REDIRECT_URI&
  response_type=code&
  access_type=offline
```

**Token Exchange:**
```bash
curl -X POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic BASE64(CLIENT_ID:CLIENT_SECRET)" \
  -d "grant_type=authorization_code&code=AUTHORIZATION_CODE&redirect_uri=YOUR_REDIRECT_URI"
```

**Refresh Tokens:**
```bash
curl -X POST https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic BASE64(CLIENT_ID:CLIENT_SECRET)" \
  -d "grant_type=refresh_token&refresh_token=YOUR_REFRESH_TOKEN"
```

#### 3. Required Information

After completing OAuth flow, you'll need:
- **Access Token** from OAuth authorization - this provides API access to QuickBooks data
- **Realm ID** (Company ID) from OAuth callback - this identifies which QuickBooks company to access
- **Environment** - use 'sandbox' for testing with sample data, 'production' for live business data

### Environment Configuration

Create a `.env` file in the server directory:

```bash
# Required: QuickBooks OAuth Configuration
QB_ACCESS_TOKEN=your_access_token
QB_REALM_ID=your_realm_id

# Optional: Environment Configuration
QB_ENVIRONMENT=sandbox  # Use 'production' for live QuickBooks data
QB_MCP_SERVER_PORT=5001  # Server port, defaults to 5001
```

### Credential Authentication

The server supports multiple ways to provide credentials:

1. **Environment Variables**: Set credentials in `.env` file (recommended for development)
2. **HTTP Headers**: Pass credentials in request headers (recommended for production):
   - `x-qb-access-token`: QuickBooks access token (required)
   - `x-qb-realm-id`: QuickBooks company/realm ID (required)
   - `x-qb-environment`: Environment - 'sandbox' or 'production' (optional, defaults to 'sandbox')
3. **Tool Arguments**: Pass credentials directly in tool calls (not recommended for security)

### Security Notes

- Keep your Client Secret secure and never expose it in client-side code
- Access tokens typically expire after 1 hour
- Refresh tokens expire after 101 days of inactivity
- Use HTTPS in production environments
- Store credentials securely using encryption

## Available Tools

### Tool Categories

The server provides comprehensive tools across all major QuickBooks areas:

- **Account Operations**: Manage chart of accounts (list, create, update, search)
- **Customer Operations**: Handle customer records and relationships
- **Invoice Operations**: Create, manage, and send invoices
- **Payment Operations**: Process and track customer payments
- **Vendor Operations**: Manage vendor relationships and records

### Discovering Available Tools

To get the current list of tools and their parameters:

```bash
# List all available tools
curl -X POST http://localhost:5001/mcp \
  -H "Content-Type: application/json" \
  -H "x-qb-access-token: YOUR_ACCESS_TOKEN" \
  -H "x-qb-realm-id: YOUR_REALM_ID" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

Or use the MCP Inspector for interactive exploration:

```bash
npx @modelcontextprotocol/inspector python server.py
```

## Example Usage

### Customer Management
```json
{
  "tool": "create_customer",
  "arguments": {
    "DisplayName": "Acme Corporation",
    "CompanyName": "Acme Corp",
    "PrimaryEmailAddr": "billing@acme.com",
    "PrimaryPhone": "555-1234",
    "BillAddrLine1": "123 Business St",
    "BillAddrCity": "Business City",
    "BillAddrPostalCode": "12345"
  }
}
```

### Invoice Creation
```json
{
  "tool": "create_invoice",
  "arguments": {
    "CustomerRefValue": "123",
    "LineItems": [
      {
        "amount": 1000.00,
        "description": "Monthly consulting services",
        "detail_type": "SalesItemLineDetail"
      }
    ]
  }
}
```

### Payment Recording
```json
{
  "tool": "create_payment",
  "arguments": {
    "CustomerRefValue": "123",
    "TotalAmt": 1000.00
  }
}
```

### Advanced Search
```json
{
  "tool": "search_invoices",
  "arguments": {
    "TxnDateFrom": "2024-01-01",
    "TxnDateTo": "2024-12-31",
    "MinAmount": 500,
    "CustomerName": "Acme"
  }
}
```

## Docker Support

### Build and Run with Docker

```bash
# Build the image
docker build -t quickbooks-mcp-server .

# Run with environment variables
docker run -p 5001:5001 \
  -e QB_ACCESS_TOKEN=your_access_token \
  -e QB_REALM_ID=your_realm_id \
  -e QB_ENVIRONMENT=sandbox \
  quickbooks-mcp-server
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  quickbooks-mcp:
    build: .
    ports:
      - "5001:5001"
    environment:
      - QB_ACCESS_TOKEN=${QB_ACCESS_TOKEN}
      - QB_REALM_ID=${QB_REALM_ID}
      - QB_ENVIRONMENT=sandbox
    volumes:
      - ./.env:/app/.env
```

## Testing with MCP Inspector

For development and testing:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run with Inspector
npx @modelcontextprotocol/inspector python server.py
```

## Troubleshooting

### Common Issues

#### 401 Authentication Error
If you get authentication errors:

1. **Check Token Expiration**: Access tokens expire after 1 hour
   ```bash
   # Check token status via API
   curl -H "Authorization: Bearer $QB_ACCESS_TOKEN" \
        "https://sandbox-quickbooks.api.intuit.com/v3/company/$QB_REALM_ID/companyinfo/$QB_REALM_ID"
   ```

2. **Refresh Access Token**: Use your refresh token to get a new access token
3. **Verify Credentials**: Ensure all credentials are correctly set
4. **Check Environment**: Verify sandbox vs production environment settings

#### 403 Permission Errors
- Ensure your QuickBooks app has the required scopes enabled
- Verify the user has permissions to access the requested data
- Check that the Realm ID matches the company being accessed

#### Connection Issues
- Verify internet connectivity and firewall settings
- Check QuickBooks service status at [Intuit Status Page](https://status.developer.intuit.com/)
- Ensure correct API endpoints for your environment

#### Token Refresh Errors
- Refresh tokens expire after 101 days of inactivity
- Re-authorize the user if refresh token is expired
- Implement automatic token refresh in production applications

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python server.py --log-level DEBUG
```

### Environment Validation

The server validates your QuickBooks connection on startup. Check the logs for:
- Credential validation status
- API connectivity
- Company information retrieval

### Support Resources

- [QuickBooks API Documentation](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities)
- [OAuth 2.0 Guide](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0)
- [Intuit Developer Community](https://help.developer.intuit.com/s/)

## Example Environment File

```bash
# .env
QB_ACCESS_TOKEN=your_access_token_here
QB_REALM_ID=your_company_realm_id_here
QB_ENVIRONMENT=sandbox
QB_MCP_SERVER_PORT=5001
```