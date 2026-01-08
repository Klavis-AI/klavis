# Shopify MCP Server

A Model Context Protocol (MCP) server for Shopify integration. Manage products, orders, customers, collections, inventory, fulfillments, and store operations using Shopify's Admin API with OAuth support.

## 🚀 Quick Start - Run in 30 Seconds

### 🌐 Using Hosted Service (Recommended for Production)

Get instant access to Shopify with our managed infrastructure - **no setup required**:

**🔗 [Get Free API Key →](https://www.klavis.ai/home/api-keys)**

```bash
pip install klavis
# or
npm install klavis
```

```python
from klavis import Klavis

klavis = Klavis(api_key="your-free-key")
server = klavis.mcp_server.create_server_instance("SHOPIFY", "user123")
```

### 🐳 Using Docker (For Self-Hosting)

```bash
# Pull latest image
docker pull ghcr.io/klavis-ai/shopify-mcp-server:latest

# Run Shopify MCP Server with OAuth Support through Klavis AI
docker run -p 5000:5000 -e KLAVIS_API_KEY=$KLAVIS_API_KEY \
  ghcr.io/klavis-ai/shopify-mcp-server:latest

# Run Shopify MCP Server (no OAuth support)
docker run -p 5000:5000 -e AUTH_DATA='{"access_token":"your_shopify_access_token_here","shop_domain":"your-store.myshopify.com"}' \
  ghcr.io/klavis-ai/shopify-mcp-server:latest
```

**OAuth Setup:** Shopify requires OAuth authentication. Use `KLAVIS_API_KEY` from your [free API key](https://www.klavis.ai/home/api-keys) to handle the OAuth flow automatically.

## 🛠️ Available Tools (26 Tools)

### 📦 Product Management (4 tools)
- **`shopify_list_products`** - Search and list products with advanced filtering (status, vendor, product type, dates)
- **`shopify_get_product`** - Get detailed information about a specific product
- **`shopify_create_product`** - Create a new product with variants
- **`shopify_update_product`** - Update existing product information

### 🛒 Order Management (3 tools)
- **`shopify_list_orders`** - List orders with status filtering (open, closed, cancelled, any)
- **`shopify_get_order`** - Get complete order details including line items and fulfillment
- **`shopify_create_order`** - Create a new order programmatically

### 👥 Customer Management (2 tools)
- **`shopify_list_customers`** - Browse all customers with pagination
- **`shopify_get_customer`** - Get detailed customer profile and order history

### 📂 Collection Management (3 tools)
- **`shopify_list_collections`** - List all product collections (custom and smart)
- **`shopify_get_collection`** - Get collection details and rules
- **`shopify_create_collection`** - Create new custom or smart collection

### 📍 Location Management (2 tools)
- **`shopify_list_locations`** - List all store locations/warehouses
- **`shopify_get_location`** - Get detailed location information

### 📊 Inventory Management (3 tools)
- **`shopify_list_inventory_items`** - List inventory items with SKU and cost info
- **`shopify_get_inventory_levels`** - Check stock levels across locations
- **`shopify_adjust_inventory`** - Adjust inventory quantities at specific locations

### 📦 Fulfillment Management (2 tools)
- **`shopify_list_fulfillments`** - List shipments for an order
- **`shopify_create_fulfillment`** - Create fulfillment with tracking information

### 📝 Draft Order Management (3 tools)
- **`shopify_list_draft_orders`** - List draft orders awaiting completion
- **`shopify_get_draft_order`** - Get draft order details
- **`shopify_create_draft_order`** - Create draft order for phone/email sales

### 🏷️ Discount Management (3 tools)
- **`shopify_list_discounts`** - List all discount codes and price rules
- **`shopify_get_discount`** - Get discount configuration details
- **`shopify_create_discount`** - Create new discount/price rule

## 💡 Example Usage

### List recent unfulfilled orders
```
"Show me all open orders from the last 7 days"
```

### Check inventory across locations
```
"What's the current stock level for product ID 123456789 across all locations?"
```

### Create a discount code
```
"Create a 20% off discount for all products, valid for the next month, limit one per customer"
```

### Find products by vendor
```
"List all products from vendor 'Nike' that are currently active"
```

### Create a draft order for phone sales
```
"Create a draft order with 2 units of variant 987654321 for customer john@example.com"
```

### Fulfill an order with tracking
```
"Create a fulfillment for order 555666777 with UPS tracking number 1Z999AA10123456784"
```

## 🔧 Advanced Features

- **Cursor-based pagination** - Efficiently browse large datasets
- **Advanced filtering** - Filter products by status, vendor, type, and date ranges
- **Multi-location inventory** - Track stock across multiple warehouses
- **Smart collections** - Automated collections with rule-based product inclusion
- **Rate limiting** - Built-in 500ms throttling to respect API limits
- **Comprehensive error handling** - Detailed error messages for troubleshooting

## 📚 Documentation & Support

| Resource | Link |
|----------|------|
| **📖 Documentation** | [www.klavis.ai/docs](https://www.klavis.ai/docs) |
| **💬 Discord** | [Join Community](https://discord.gg/p7TuTEcssn) |
| **🐛 Issues** | [GitHub Issues](https://github.com/klavis-ai/klavis/issues) |
| **🛍️ Shopify API Docs** | [Shopify Admin API](https://shopify.dev/docs/api/admin-rest) |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

## 📜 License

Apache 2.0 license - see [LICENSE](../../LICENSE) for details.

---

<div align="center">
  <p><strong>🚀 Supercharge AI Applications </strong></p>
  <p>
    <a href="https://www.klavis.ai">Get Free API Key</a> •
    <a href="https://www.klavis.ai/docs">Documentation</a> •
    <a href="https://discord.gg/p7TuTEcssn">Discord</a>
  </p>
</div>
