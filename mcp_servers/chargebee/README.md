# Chargebee MCP Server

A Model Context Protocol (MCP) server for Chargebee subscription billing integration. Manage customers, subscriptions, invoices, transactions, and events using Chargebee's API.

## Quick Start - Run in 30 Seconds

### Using Hosted Service (Recommended for Production)

Get instant access to Chargebee with our managed infrastructure - **no setup required**:

**[Get Free API Key](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("CHARGEBEE", "user123")
```

### Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/chargebee-mcp-server:latest

# Run Chargebee MCP Server
docker run -p 5000:5000 \
  -e AUTH_DATA='{"access_token":"your_chargebee_api_key","site":"your_site_name"}' \
  ghcr.io/klavis-ai/chargebee-mcp-server:latest
```

**Authentication:** Chargebee uses API key authentication. You can obtain your API key from your Chargebee dashboard under Settings > Configure Chargebee > API Keys.

## Available Tools

### Customer Management
- `chargebee_list_customers` - List all customers with pagination and filters
- `chargebee_get_customer` - Get detailed customer information
- `chargebee_create_customer` - Create a new customer
- `chargebee_update_customer` - Update customer details
- `chargebee_delete_customer` - Delete a customer

### Subscription Management
- `chargebee_list_subscriptions` - List subscriptions with filters
- `chargebee_get_subscription` - Get subscription details
- `chargebee_create_subscription` - Create a new subscription (Product Catalog 2.0)
- `chargebee_update_subscription` - Update subscription details
- `chargebee_cancel_subscription` - Cancel a subscription

### Invoice Management
- `chargebee_list_invoices` - List invoices with filters
- `chargebee_get_invoice` - Get invoice details

### Transaction Management
- `chargebee_list_transactions` - List payment transactions

### Event Management
- `chargebee_list_events` - List events for data sync and change tracking
- `chargebee_get_event` - Get event details

### Item Management (Product Catalog 2.0)
- `chargebee_list_items` - List items (plans, addons, charges)
- `chargebee_get_item` - Get item details

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CHARGEBEE_ACCESS_TOKEN` | Your Chargebee API key | Yes |
| `CHARGEBEE_SITE` | Your Chargebee site name | Yes |
| `CHARGEBEE_MCP_SERVER_PORT` | Server port (default: 5000) | No |

## Documentation & Support

| Resource | Link |
|----------|------|
| **Documentation** | [www.klavis.ai/docs](https://www.klavis.ai/docs) |
| **Discord** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |
| **Chargebee API Docs** | [apidocs.chargebee.com](https://apidocs.chargebee.com/docs/api) |

## Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## License

Apache 2.0 license - see [LICENSE](../../LICENSE) for details.

---

<div align="center">
  <p><strong>Supercharge AI Applications</strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://www.klavis.ai/docs">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>
