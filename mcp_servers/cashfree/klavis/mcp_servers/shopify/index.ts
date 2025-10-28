#!/usr/bin/env node
import express, { Request, Response as ExpressResponse } from 'express';
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import {
  CallToolRequest,
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from 'zod';
import { AsyncLocalStorage } from "async_hooks";
import { setTimeout } from 'timers/promises';
import { ApiErrorResponse, ApiHeaders, AsyncLocalStorageState, CreateOrderArgs, CreateProductArgs, GetCustomerArgs, GetOrderArgs, GetProductArgs, ListCustomersArgs, ListOrdersArgs, ListProductsArgs, OrderStatus, ShopifyCredentials, UpdateProductArgs } from './types.js';
import { createOrderTool, createProductTool, getCustomerTool, getOrderTool, getProductTool, listCustomersTool, listOrdersTool, listProductsTool, updateProductTool } from './tools.js';
import dotenv from 'dotenv';

dotenv.config();
class ShopifyClient {
  private apiHeaders: ApiHeaders;
  private shopDomain: string;
  private lastRequestTime: number = 0;
  private readonly minRequestInterval: number = 500;
  private readonly apiVersion = '2025-04';

  constructor(accessToken: string, shopDomain: string) {
    this.apiHeaders = {
      'X-Shopify-Access-Token': accessToken,
      'Content-Type': 'application/json',
    };
    this.shopDomain = shopDomain;
  }

  private async respectRateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.minRequestInterval) {
      const waitTime = this.minRequestInterval - timeSinceLastRequest;
      await setTimeout(waitTime);
    }
    
    this.lastRequestTime = Date.now();
  }

  private async handleApiResponse<T>(response: globalThis.Response): Promise<T> {
    if (response.ok) {
      return await response.json() as T;
    }
    
    const errorText = await response.text();
    let errorMessage = `Shopify API error: ${response.status}`;
    
    try {
      const errorJson = JSON.parse(errorText) as ApiErrorResponse;
      errorMessage = `Shopify API error: ${response.status} - ${JSON.stringify(errorJson)}`;
      
      // Handle rate limiting
      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '10', 10);
        console.warn(`Rate limited. Retrying after ${retryAfter} seconds`);
        await setTimeout(retryAfter * 1000);
        // In a production implementation, you would retry the request here
        // For now, just throwing the error to be consistent with existing code
        throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds.`);
      }
      
      // Handle GraphQL-specific errors
      if (errorJson.errors) {
        const graphQLErrors = errorJson.errors;
        errorMessage = `GraphQL errors: ${JSON.stringify(graphQLErrors)}`;
        
        // Check for ShopifyQL specific errors
        if (typeof graphQLErrors === 'object' && Array.isArray(graphQLErrors)) {
          const shopifyQLErrors = graphQLErrors.filter((err: any) => 
            err.message && err.message.includes('ShopifyQL'));
          
          if (shopifyQLErrors.length > 0) {
            errorMessage = `ShopifyQL error: ${shopifyQLErrors.map((e: any) => e.message).join('; ')}`;
          }
        }
      }
    } catch (e) {
      errorMessage = `Shopify API error: ${response.status} - ${errorText}`;
    }
    
    throw new Error(errorMessage);
  }

  refreshToken(): boolean {
    const credentials = getShopifyCredentials();
    if (credentials.accessToken && credentials.shopDomain) {
      this.apiHeaders['X-Shopify-Access-Token'] = credentials.accessToken;
      this.shopDomain = credentials.shopDomain;
      return true;
    }
    return false;
  }

  async listProducts(limit: number = 50, cursor?: string, collection_id?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (cursor) {
      params.append("page_info", cursor);
      params.append("limit", Math.min(limit, 250).toString());
    }

    if (collection_id) {
      params.append("collection_id", collection_id);
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/products.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getProduct(product_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/products/${product_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createProduct(productData: CreateProductArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/products.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ product: productData }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async updateProduct(product_id: string, productData: Partial<UpdateProductArgs>): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/products/${product_id}.json`,
      {
        method: "PUT",
        headers: this.apiHeaders,
        body: JSON.stringify({ product: productData }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async listOrders(limit: number = 50, status: OrderStatus = "any", cursor?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
      status: status,
    });

    if (cursor) {
      params.append("page_info", cursor);
      params.append("limit", Math.min(limit, 250).toString());
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/orders.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getOrder(order_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/orders/${order_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createOrder(orderData: CreateOrderArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/orders.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ order: orderData }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async listCustomers(limit: number = 50, cursor?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (cursor) {
      params.append("page_info", cursor);
      params.append("limit", Math.min(limit, 250).toString());
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/customers.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getCustomer(customer_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/customers/${customer_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }
}

const getShopifyMcpServer = (): Server => {
  const server = new Server(
    {
      name: "shopify-mcp-server",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );
  server.setRequestHandler(
    ListToolsRequestSchema,
    async () => {
      return {
        tools: [
          listProductsTool,
          getProductTool,
          createProductTool,
          updateProductTool,
          listOrdersTool,
          getOrderTool,
          createOrderTool,
          listCustomersTool,
          getCustomerTool
        ],
      };
    }
  );

  server.setRequestHandler(
    CallToolRequestSchema,
    async (request: CallToolRequest) => {
      try {
        if (!request.params?.name) {
          throw new Error("Missing tool name");
        }

        const credentials = getShopifyCredentials();
        if (!credentials.accessToken || !credentials.shopDomain) {
          throw new Error("No valid Shopify credentials found for this instance");
        }

        const shopifyClient = new ShopifyClient(credentials.accessToken, credentials.shopDomain);

        switch (request.params.name) {
          case "shopify_list_products": {
            const args = request.params.arguments as unknown as ListProductsArgs;
            const response = await shopifyClient.listProducts(
              args.limit,
              args.cursor,
              args.collection_id
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_product": {
            const args = request.params.arguments as unknown as GetProductArgs;
            if (!args.product_id) {
              throw new Error("Missing required argument: product_id");
            }
            const response = await shopifyClient.getProduct(args.product_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_product": {
            const args = request.params.arguments as unknown as CreateProductArgs;
            if (!args.title) {
              throw new Error("Missing required argument: title");
            }
            const response = await shopifyClient.createProduct(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_update_product": {
            const args = request.params.arguments as unknown as UpdateProductArgs;
            if (!args.product_id) {
              throw new Error("Missing required argument: product_id");
            }
            const { product_id, ...productData } = args;
            const response = await shopifyClient.updateProduct(product_id, productData);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_list_orders": {
            const args = request.params.arguments as unknown as ListOrdersArgs;
            const response = await shopifyClient.listOrders(
              args.limit,
              args.status as OrderStatus,
              args.cursor
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_order": {
            const args = request.params.arguments as unknown as GetOrderArgs;
            if (!args.order_id) {
              throw new Error("Missing required argument: order_id");
            }
            const response = await shopifyClient.getOrder(args.order_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_order": {
            const args = request.params.arguments as unknown as CreateOrderArgs;
            if (!args.line_items || args.line_items.length === 0) {
              throw new Error("Missing required argument: line_items");
            }
            const response = await shopifyClient.createOrder(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_list_customers": {
            const args = request.params.arguments as unknown as ListCustomersArgs;
            const response = await shopifyClient.listCustomers(
              args.limit,
              args.cursor
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_customer": {
            const args = request.params.arguments as unknown as GetCustomerArgs;
            if (!args.customer_id) {
              throw new Error("Missing required argument: customer_id");
            }
            const response = await shopifyClient.getCustomer(args.customer_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          default:
            throw new Error(`Unknown tool: ${request.params.name}`);
        }
      } catch (error) {
        console.error("Error executing tool:", error);

        if (error instanceof z.ZodError) {
          throw new Error(`Invalid input: ${JSON.stringify(error.errors)}`);
        }

        throw error;
      }
    }
  );

  return server;
};

const asyncLocalStorage = new AsyncLocalStorage<AsyncLocalStorageState>();

function extractAuthData(req: Request): { access_token?: string; shop_domain?: string } {
  let authData = process.env.AUTH_DATA;
  
  if (!authData && req.headers['x-auth-data']) {
    try {
      authData = Buffer.from(req.headers['x-auth-data'] as string, 'base64').toString('utf8');
    } catch (error) {
      console.error('Error parsing x-auth-data JSON:', error);
    }
  }

  if (!authData) {
    console.error('Error: Shopify access token is missing. Provide it via AUTH_DATA env var or x-auth-data header with access_token field.');
    return JSON.parse('{}');
  }

  const authDataJson = JSON.parse(authData) as { access_token?: string; shop_domain?: string };
  return authDataJson;
}

function getShopifyCredentials(): ShopifyCredentials {
  if (process.env.SHOPIFY_ACCESS_TOKEN && process.env.SHOPIFY_SHOP_DOMAIN) {
    return {
      accessToken: process.env.SHOPIFY_ACCESS_TOKEN,
      shopDomain: process.env.SHOPIFY_SHOP_DOMAIN,
    };
  }
  const store = asyncLocalStorage.getStore();
  return {
    accessToken: store?.shopify_access_token,
    shopDomain: store?.shopify_shop_domain,
  };
}

const app = express();
app.use(express.json());

app.post('/mcp', async (req: Request, res: ExpressResponse) => {
  const authData = extractAuthData(req);
  const accessToken = authData.access_token ?? '';
  const shopDomain = authData.shop_domain ?? '';

  const server = getShopifyMcpServer();
  try {
    const transport: StreamableHTTPServerTransport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });
    await server.connect(transport);
    asyncLocalStorage.run({ 
      shopify_access_token: accessToken, 
      shopify_shop_domain: shopDomain 
    }, async () => {
      await transport.handleRequest(req, res, req.body);
    });
    res.on('close', () => {
      console.log('Request closed');
      transport.close();
      server.close();
    });
  } catch (error) {
    console.error('Error handling MCP request:', error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal server error',
        },
        id: null,
      });
    }
  }
});

app.get('/mcp', async (req: Request, res: ExpressResponse) => {
  console.log('Received GET MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

app.delete('/mcp', async (req: Request, res: ExpressResponse) => {
  console.log('Received DELETE MCP request');
  res.writeHead(405).end(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32000,
      message: "Method not allowed."
    },
    id: null
  }));
});

const transports = new Map<string, SSEServerTransport>();

app.get("/sse", async (req, res) => {
  const transport = new SSEServerTransport(`/messages`, res);

  res.on('close', async () => {
    console.log(`SSE connection closed for transport: ${transport.sessionId}`);
    try {
      transports.delete(transport.sessionId);
    } finally {
    }
  });

  transports.set(transport.sessionId, transport);

  const server = getShopifyMcpServer();
  await server.connect(transport);

  console.log(`SSE connection established with transport: ${transport.sessionId}`);
});

app.post("/messages", async (req, res) => {
  const sessionId = req.query.sessionId as string;

  let transport: SSEServerTransport | undefined;
  transport = sessionId ? transports.get(sessionId) : undefined;
  if (transport) {
    const authData = extractAuthData(req);
    const accessToken = authData.access_token ?? '';
    const shopDomain = authData.shop_domain ?? '';

    asyncLocalStorage.run({ 
      shopify_access_token: accessToken, 
      shopify_shop_domain: shopDomain 
    }, async () => {
      await transport.handlePostMessage(req, res);
    });
  } else {
    console.error(`Transport not found for session ID: ${sessionId}`);
    res.status(404).send({ error: "Transport not found" });
  }
});

app.listen(process.env.PORT || 5000, () => {
  console.log(`server running on port ${process.env.PORT || 5000}`);
});