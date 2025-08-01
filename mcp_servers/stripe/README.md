# Stripe MCP Server

A Model Context Protocol (MCP) server for Stripe operations, supporting both SSE and StreamableHTTP transports.

## Features

This server provides comprehensive Stripe functionality including:

### Customer Management
- Create customers
- List customers with filtering

### Product & Pricing
- Create products
- List products  
- Create prices for products
- List prices with filtering

### Payments
- Create payment links
- List payment intents
- Process refunds

### Invoicing
- List invoices
- Create invoices
- Add invoice items
- Finalize invoices

### Billing
- Create billing portal sessions

### Account Management
- Retrieve account balance

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export STRIPE_MCP_SERVER_PORT=5001  # Optional, defaults to 5001
```

## Usage

### Running the Server

```bash
python server.py
```

Options:
- `--port`: Port to listen on (default: 5001)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--json-response`: Enable JSON responses for StreamableHTTP instead of SSE streams

### Authentication

The server expects the Stripe secret key to be provided in request headers:

- **SSE**: Include `x-stripe-secret-key` header in your requests
- **StreamableHTTP**: Include `x-stripe-secret-key` header in your requests

Example:
```bash
curl -H "x-stripe-secret-key: sk_test_..." http://localhost:5001/sse
```

### Endpoints

The server provides two transport methods:

1. **SSE (Server-Sent Events)**: `http://localhost:5001/sse`
2. **StreamableHTTP**: `http://localhost:5001/mcp`

### Docker

Build and run with Docker:

```bash
# Build the image
docker build -t stripe-mcp-server -f mcp_servers/stripe/Dockerfile .

# Run the container
docker run -p 5001:5001 stripe-mcp-server
```

## Tool Reference

### Customer Tools
- `stripe_create_customer`: Create a new customer
- `stripe_list_customers`: List existing customers

### Product Tools  
- `stripe_create_product`: Create a new product
- `stripe_list_products`: List existing products
- `stripe_create_price`: Create a price for a product
- `stripe_list_prices`: List prices

### Payment Tools
- `stripe_create_payment_link`: Create a payment link
- `stripe_list_payment_intents`: List payment intents
- `stripe_create_refund`: Process a refund

### Invoice Tools
- `stripe_list_invoices`: List invoices
- `stripe_create_invoice`: Create a new invoice
- `stripe_create_invoice_item`: Add items to an invoice
- `stripe_finalize_invoice`: Finalize an invoice

### Billing Tools
- `stripe_create_billing_portal_session`: Create a billing portal session

### Account Tools
- `stripe_retrieve_balance`: Get account balance

## Security Notes

- Never commit your actual Stripe secret keys to version control
- Use environment variables or secure secret management for production
- The server expects secret keys via headers for better security
- Use test keys during development (prefix: `sk_test_`)

## Dependencies

This server uses the `stripe-agent-toolkit` library for Stripe API interactions and follows the MCP specification for tool definitions and execution. 