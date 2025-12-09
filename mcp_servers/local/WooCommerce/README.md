# WooCommerce MCP Server

An MCP (Model Context Protocol) server that provides access to WooCommerce REST API functionality.

## Features

- Complete WooCommerce API coverage
- Product management (including variations, categories, tags, reviews)
- Order management (including notes and refunds)
- Customer management
- Coupon management
- Shipping configuration
- Tax settings
- Reports and analytics
- System management and webhooks

## Installation

```bash
npm install @lockon0927/woocommerce-mcp
```

## Configuration

Configure in Claude Desktop:

```json
{
  "mcpServers": {
    "woocommerce": {
      "command": "npx",
      "args": [
        "@lockon0927/woocommerce-mcp"
      ],
      "env": {
        "WORDPRESS_SITE_URL": "https://your-site.com",
        "WOOCOMMERCE_CONSUMER_KEY": "ck_your_consumer_key_here",
        "WOOCOMMERCE_CONSUMER_SECRET": "cs_your_consumer_secret_here",
        "WORDPRESS_USERNAME": "your_username",
        "WORDPRESS_PASSWORD": "your_password"
      }
    }
  }
}
```

### Getting Your Credentials

1. **WooCommerce API Keys**: 
   - Go to WooCommerce → Settings → Advanced → REST API
   - Click "Add Key" to generate consumer key and secret

2. **WordPress Credentials**:
   - Use your WordPress admin username and password

3. **Site URL**:
   - Your WordPress site's base URL (e.g., https://yourstore.com)