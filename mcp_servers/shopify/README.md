# Shopify MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This server implements the Model Context Protocol (MCP) to provide access to various Shopify API functionalities as tools for language models or other MCP clients. It allows interacting with Shopify stores programmatically through a standardized interface.

This server follows the implementation pattern from the [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) reference implementation.

## Features

The server exposes the following Shopify API functions as MCP tools:

* `shopify_list_products`: List products in the Shopify store with pagination.
* `shopify_get_product`: Get detailed information about a specific product.
* `shopify_create_product`: Create a new product in the Shopify store.
* `shopify_update_product`: Update an existing product in the Shopify store.
* `shopify_list_orders`: List orders in the Shopify store with pagination.
* `shopify_get_order`: Get detailed information about a specific order.
* `shopify_create_order`: Create a new order in the Shopify store.
* `shopify_list_customers`: List customers in the Shopify store with pagination.
* `shopify_get_customer`: Get detailed information about a specific customer.

## Prerequisites

Before you begin, ensure you have the following:

## How to Obtain Your Shopify Access Token and Shop Domain

To use the Shopify MCP Server, you need two key pieces of information:

- **Shopify Access Token**: Used to authenticate API requests.
- **Shop Domain**: The unique domain of your Shopify store (e.g., `your-store.myshopify.com`).

Follow these steps to obtain both:

**1. Log in to Your Shopify Admin**

- Go to your Shopify Admin dashboard at `https://your-store.myshopify.com/admin`.

**2. Create a Custom App (for Private API Access)**

- In the Shopify Admin, click on **Settings** (bottom left).
- Select **Apps and sales channels**.
- Click **Develop apps for your store** (you may need to enable app development if it's your first time).
- Click **Create an app**.
- Enter a name for your app (e.g., "MCP Integration") and click **Create app**.

**3. Configure API Access and Permissions**

- In your newly created app, go to the **Configuration** tab.
- Click **Configure** under "Admin API integration".
- Select the required Admin API permissions based on the features you want to use (e.g., Products, Orders, Customers).
- Click **Save**.

| Tool                   | Required Access Scopes (Permissions) | 
| :--------------------- | :----------------------------------- |
| shopify_list_products  | `read_products`                      |
| shopify_get_product    | `read_products`                      |
| shopify_create_product | `write_products`                     |
| shopify_update_product | `write_products`                     |
| shopify_list_orders    | `read_orders`                        |
| shopify_get_order      | `read_orders`                        |
| shopify_create_order   | `write_orders`                       |
| shopify_list_customers | `read_customers`                     |
| shopify_get_customer   | `read_customers`                     |

**4. Install the App**

- Go to the **Install App** tab.
- Click **Install** to add the app to your store.

**5. Get the Access Token**

- After installing, go to the **API credentials** tab.
- Under "Access tokens", click **Reveal token once** to view your Admin API access token.
- **Copy and securely store this token**. You will not be able to view it again.

**6. Find Your Shop Domain**

- Your shop domain is the `.myshopify.com` address you use to access your Shopify Admin (e.g., `your-store.myshopify.com`).
- You can find it in your browser's address bar when logged into the Shopify Admin.


* **Node.js and npm:** Required for local development (check versions with `node -v` and `npm -v`).
* **Docker:** Required for running the server in a container (Recommended).
* **Shopify Access Token:** An API access token with the necessary permissions to perform the actions listed in the Features section. You can create a private app in your Shopify Admin to obtain an access token.
* **Shopify Shop Domain:** Your Shopify store's domain (e.g., `your-store.myshopify.com`).

## Setup

You can run the server using Docker (recommended) or locally.

### Docker (Recommended)

1.  **Create Environment File:**
    Create a file named `.env` in the `mcp_servers/shopify` directory with the following content:
    ```env
    # Optional: Your Shopify Access Token
    # If provided, this takes precedence over the x-shopify-access-token header
    SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
    
    # Optional: Your Shopify Shop Domain
    # If provided, this takes precedence over the x-shopify-shop-domain header
    SHOPIFY_SHOP_DOMAIN=your-shopify-store.shopify.com
    # If these variables are not set, the credentials must be provided via headers with each request (see Configuration).
    ```

2.  **Build Docker Image:**
    Navigate to the root `klavis` directory (one level above `mcp_servers`) in your terminal and run the build command:
    ```bash
    docker build -t shopify-mcp-server -f mcp_servers/shopify/Dockerfile .
    ```
    *(Make sure the path to the Dockerfile is correct relative to your current directory.)*

3.  **Run Docker Container:**
    Run the container, mapping the server's port (5000) to a port on your host machine (e.g., 5000):
    ```bash
    # Note: The .env file created in step 1 is copied into the image during the build process specified in the Dockerfile.
    docker run -p 5000:5000 --name shopify-mcp shopify-mcp-server 
    ```
    The server will start and listen on port 5000 inside the container.

### Local Development

1.  **Clone Repository:** (If you haven't already)
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Navigate to Directory:**
    ```bash
    cd mcp_servers/shopify
    ```

3.  **Create Environment File:**
    Create a file named `.env` in this directory as described in Step 1 of the Docker setup:
    ```env
    # Optional: Your Shopify Access Token
    # If provided, this takes precedence over the x-shopify-access-token header
    SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
    
    # Optional: Your Shopify Shop Domain
    # If provided, this takes precedence over the x-shopify-shop-domain header
    SHOPIFY_SHOP_DOMAIN=your-shopify-store.shopify.com
    # If these variables are not set, the credentials must be provided via headers with each request (see Configuration).
    ```

4.  **Install Dependencies:**
    ```bash
    npm install
    ```

5.  **Build and Run:**
    This command compiles the TypeScript code and starts the server:
    ```bash
    npm start
    ```
    The server will start and listen on `http://localhost:5000`.

## Configuration

*   **`SHOPIFY_ACCESS_TOKEN` (Environment Variable):** Optional. If set, this token will be used for all Shopify API calls. Takes precedence over the token provided in request headers.
*   **`SHOPIFY_SHOP_DOMAIN` (Environment Variable):** Optional. If set, this domain will be used for all Shopify API calls. Takes precedence over the domain provided in request headers.
*   **Shopify Access Token (Request Header):** If `SHOPIFY_ACCESS_TOKEN` is not set, the server expects the Shopify Access Token to be provided in the `x-shopify-access-token` HTTP header for every request.
*   **Shopify Shop Domain (Request Header):** If `SHOPIFY_SHOP_DOMAIN` is not set, the server expects the Shopify Shop Domain to be provided in the `x-shopify-shop-domain` HTTP header for every request.

## Usage

MCP clients can connect to this server via Server-Sent Events (SSE) and interact with it:

1.  **Establish SSE Connection:** Clients connect to the `/sse` endpoint (e.g., `http://localhost:5000/sse`).
2.  **Send Messages:** Clients send MCP requests (like `call_tool`) as JSON payloads via POST requests to the `/messages?sessionId=<session_id>` endpoint.
3.  **Authentication:** Each POST request to `/messages` **must** include the Shopify Access Token in the `x-shopify-access-token` header and the Shopify Shop Domain in the `x-shopify-shop-domain` header .

Refer to the [MCP SDK documentation](https://github.com/modelcontextprotocol) for details on client implementation.