[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/cashfree-cashfree-mcp-badge.png)](https://mseep.ai/app/cashfree-cashfree-mcp)

# Cashfree MCP Server

Cashfree MCP server allows AI tools and agents to integrate with [Cashfree](https://www.cashfree.com/) APIs (Payment Gateway, Payouts, and SecureID) using the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).

## Setup

### Clone the Repository

```bash
git clone https://github.com/cashfree/cashfree-mcp.git
cd cashfree-mcp
```

### Install Dependencies

Before installing, ensure you have **Node.js v14.x or higher** installed. If you're using `nvm` or `brew`, make sure the correct version is active:

```bash
node -v
# Should output v14.x or higher
```

#### Step 1: Install project dependencies

```bash
npm install
```

This will install all required packages listed in `package.json`.

> 💡 If you're using `Node.js >=18`, you might face peer dependency issues with packages like `undici`. In that case, upgrade Node.js to `>=20.18.1` or adjust the package version if needed.

#### Step 2: Build the project

```bash
npm run build
```

This compiles the source files to the `dist/` directory, which is required to run the MCP server.

> 🛠️ If you see errors related to missing files in `/dist`, ensure you've run the build step successfully.


## Configuration

You will need a Cashfree account with API credentials (we support both sandbox and production keys). You can use Cashfree MCP in your favorite client, some sample configurations are shown below:

### Claude

Add the following configuration block to your `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cashfree": {
      "command": "node",
      "args": ["/path/to/cashfree-mcp/dist/index.js"],
      "env": {
        "PAYMENTS_APP_ID": "YOUR_PG_CLIENT_ID",
        "PAYMENTS_APP_SECRET": "YOUR_PG_CLIENT_SECRET",
        "PAYOUTS_APP_ID": "YOUR_PAYOUTS_CLIENT_ID",
        "PAYOUTS_APP_SECRET": "YOUR_PAYOUTS_CLIENT_SECRET",
        "TWO_FA_PUBLIC_KEY_PEM_PATH": "/path/to/public_key.pem",
        "SECUREID_APP_ID": "YOUR_SECUREID_CLIENT_ID",
        "SECUREID_APP_SECRET": "YOUR_SECUREID_CLIENT_SECRET",
        "TOOLS": "pg,payouts,secureid",
        "ENV": "sandbox",
        "ELICITATION_ENABLED": "true"
      }
    }
  }
}
```

### VS Code

Add the following configuration block to your VS Code settings

```json
{
  "mcp": {
    "inputs": [],
    "servers": {
      "cashfree": {
        "command": "node",
        "args": ["/path/to/cashfree-mcp/dist/index.js"],
        "env": {
          "PAYMENTS_APP_ID": "YOUR_PG_CLIENT_ID",
          "PAYMENTS_APP_SECRET": "YOUR_PG_CLIENT_SECRET",
          "PAYOUTS_APP_ID": "YOUR_PAYOUTS_CLIENT_ID",
          "PAYOUTS_APP_SECRET": "YOUR_PAYOUTS_CLIENT_SECRET",
          "TWO_FA_PUBLIC_KEY_PEM_PATH": "/path/to/public_key.pem",
          "SECUREID_APP_ID": "YOUR_SECUREID_CLIENT_ID",
          "SECUREID_APP_SECRET": "YOUR_SECUREID_CLIENT_SECRET",
          "TOOLS": "pg,payouts,secureid",
          "ENV": "sandbox",
          "ELICITATION_ENABLED": "true"
        }
      }
    }
  }
}
```

### API Credentials

Set the following environment variables for each service:
**Payment Gateway:**

- `PAYMENTS_APP_ID`: Your Payment Gateway client ID
- `PAYMENTS_APP_SECRET`: Your Payment Gateway client secret

**Payouts:**

- `PAYOUTS_APP_ID`: Your Payouts client ID
- `PAYOUTS_APP_SECRET`: Your Payouts client secret
- `TWO_FA_PUBLIC_KEY_PEM_PATH`: Path to your 2FA public key (required only if 2FA is enabled)

**SecureID:**

- `SECUREID_APP_ID`: Your SecureID client ID
- `SECUREID_APP_SECRET`: Your SecureID client secret
- `TWO_FA_PUBLIC_KEY_PEM_PATH`: Path to your 2FA public key (required only if 2FA is enabled)

### Environment

`ENV`: Set to `production` for production environment, `sandbox` for sandbox (default: `sandbox`)

### Tools Configuration

`TOOLS`: Comma-separated list of modules to enable. Available options:

- `pg`: Payment Gateway APIs
- `payouts`: Payouts APIs
- `secureid`: SecureID APIs

### Elicitation Configuration

`ELICITATION_ENABLED`: Set to `true` to enable interactive parameter elicitation, `false` to disable (default: `false`)

When enabled, the MCP server will prompt users for missing required parameters instead of failing with validation errors. This provides a more interactive experience by asking users to provide values for required fields that weren't initially supplied.

## Tools

Cashfree MCP has the following tools available, grouped by the product category

### Payment Gateway (PG)

| Tool Name                                                | Description                                                                                        |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **search**                                               | Search across the Cashfree Payments Developer Documentation.                                       |
| **get-input-source-help**                               | Get comprehensive instructions for handling input source variable errors.                          |
| **create-payment-link**                                  | Create a new payment link.                                                                         |
| **fetch-payment-link-details**                           | View all details and status of a payment link.                                                     |
| **cancel-payment-link**                                  | Cancel an active payment link. No further payments can be done against cancelled links             |
| **get-orders-for-a-payment-link**                        | View all order details for a payment link.                                                         |
| **create-order**                                         | Create orders with Cashfree to get a payment_sessions_id for transactions                          |
| **get-order**                                            | Fetch order details using order_id                                                                 |
| **get-order-extended**                                   | Get extended order data like address, cart, offers, customer details etc                           |
| **get-eligible-payment-methods**                         | Get eligible payment methods for a given order amount and ID                                       |
| **get-payments-for-an-order**                            | View all payment details for an order.                                                             |
| **get-payment-by-id**                                    | View payment details of an order for a Payment ID.                                                 |
| **create-refund**                                        | Initiate refunds.                                                                                  |
| **get-all-refunds-for-an-order**                         | Fetch all refunds processed against an order.                                                      |
| **get-refund**                                           | Fetch a specific refund processed on your Cashfree Account.                                        |
| **get-all-settlements**                                  | Get all settlement details by specifying the settlement ID, settlement UTR, or date range.         |
| **get-split-and-settlement-details-by-order-id-v2-0**    | Get split and settlement details, including settled/unsettled transactions for vendors in an order |
| **get-settlements-by-order-id**                          | View all the settlements of a particular order.                                                    |
| **get-disputes-by-order-id**                             | Get all dispute details by Order ID                                                                |
| **get-disputes-by-payment-id**                           | Get all dispute details by Payment ID                                                              |
| **get-disputes-by-dispute-id**                           | Get dispute details by Dispute ID                                                                  |
| **accept-dispute-by-dispute-id**                         | Accept a dispute by its Dispute ID                                                                 |
| **submit-evidence-to-contest-the-dispute-by-dispute-id** | Submit evidence to contest a dispute                                                               |
| **simulate-payment**                                     | Simulate payment for testing. Requires prior order creation                                        |
| **fetch-simulation**                                     | Fetch simulated payment details                                                                    |

### Payouts

| Tool Name                        | Description                                                                      |
| -------------------------------- | -------------------------------------------------------------------------------- |
| **standard-transfer-v2**         | Initiate an amount transfer at Cashfree Payments.                                |
| **get-transfer-status-v2**       | Get the status of an initiated transfer.                                         |
| **batch-transfer-v2**            | Initiate a batch transfer request at Cashfree Payments.                          |
| **get-batch-transfer-status-v2** | Get the status of an initiated batch transfer.                                   |
| **authorize**                    | Authenticate with the Cashfree system and obtain the authorization bearer token. |
| **create-cashgram**              | Create a Cashgram.                                                               |
| **deactivate-cashgram**          | Deactivate a Cashgram.                                                           |
| **get-cashgram-status**          | Get the status of a created Cashgram.                                            |

### SecureID

| Tool Name                      | Description                                       |
| ------------------------------ | ------------------------------------------------- |
| **verify-name-match**          | Verify names with variations.                     |
| **generate-kyc-link**          | Generate a verification form for KYC information. |
| **get-kyc-link-status**        | Get the status of a KYC verification form.        |
| **generate-static-kyc-link**   | Generate a static KYC link.                       |
| **deactivate-static-kyc-link** | Deactivate a static KYC link.                     |

## License

This project is licensed under the terms of the MIT open source license. Please refer to LICENSE for the full terms.

## Documentation

For detailed API documentation, visit the [Cashfree API Documentation](https://docs.cashfree.com/reference/).

## Support

For support, contact [care@cashfree.com](mailto:care@cashfree.com) or raise an issue in the [GitHub repository](https://github.com/cashfree/cashfree-mcp).
