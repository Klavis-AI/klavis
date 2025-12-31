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
import { ApiErrorResponse, ApiHeaders, AsyncLocalStorageState, CreateOrderArgs, CreateProductArgs, GetCustomerArgs, GetOrderArgs, GetProductArgs, ListCustomersArgs, ListOrdersArgs, ListProductsArgs, OrderStatus, ShopifyCredentials, UpdateProductArgs, ListCollectionsArgs, GetCollectionArgs, CreateCollectionArgs, ListInventoryItemsArgs, GetInventoryLevelsArgs, AdjustInventoryArgs, ListFulfillmentsArgs, CreateFulfillmentArgs, ListLocationsArgs, GetLocationArgs, ListDraftOrdersArgs, GetDraftOrderArgs, CreateDraftOrderArgs, ListDiscountsArgs, GetDiscountArgs, CreateDiscountArgs } from './types.js';
import { createOrderTool, createProductTool, getCustomerTool, getOrderTool, getProductTool, listCustomersTool, listOrdersTool, listProductsTool, updateProductTool, listCollectionsTool, getCollectionTool, createCollectionTool, listLocationsTool, getLocationTool, listInventoryItemsTool, getInventoryLevelsTool, adjustInventoryTool, listFulfillmentsTool, createFulfillmentTool, listDraftOrdersTool, getDraftOrderTool, createDraftOrderTool, listDiscountsTool, getDiscountTool, createDiscountTool } from './tools.js';
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

  private async graphqlRequest<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/graphql.json`,
      {
        method: 'POST',
        headers: this.apiHeaders,
        body: JSON.stringify({ query, variables }),
      }
    );

    const result = await response.json() as { data?: T; errors?: unknown[] };
    
    if (result.errors) {
      throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
    }
    
    if (!result.data) {
      throw new Error('GraphQL response missing data');
    }
    
    return result.data;
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

  async listProducts(limit: number = 50, cursor?: string, collection_id?: string, status?: string, vendor?: string, product_type?: string, since_id?: string, created_at_min?: string, created_at_max?: string, updated_at_min?: string, updated_at_max?: string): Promise<Record<string, unknown>> {
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

    if (status) {
      params.append("status", status);
    }

    if (vendor) {
      params.append("vendor", vendor);
    }

    if (product_type) {
      params.append("product_type", product_type);
    }

    if (since_id) {
      params.append("since_id", since_id);
    }

    if (created_at_min) {
      params.append("created_at_min", created_at_min);
    }

    if (created_at_max) {
      params.append("created_at_max", created_at_max);
    }

    if (updated_at_min) {
      params.append("updated_at_min", updated_at_min);
    }

    if (updated_at_max) {
      params.append("updated_at_max", updated_at_max);
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

  // Collections
  async listCollections(limit: number = 50, cursor?: string, title?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (cursor) {
      params.append("page_info", cursor);
    }

    if (title) {
      params.append("title", title);
    }

    // Get both custom and smart collections
    const [customResponse, smartResponse] = await Promise.all([
      fetch(
        `https://${this.shopDomain}/admin/api/${this.apiVersion}/custom_collections.json?${params}`,
        { headers: this.apiHeaders }
      ),
      fetch(
        `https://${this.shopDomain}/admin/api/${this.apiVersion}/smart_collections.json?${params}`,
        { headers: this.apiHeaders }
      )
    ]);

    const customData = await this.handleApiResponse<Record<string, unknown>>(customResponse);
    const smartData = await this.handleApiResponse<Record<string, unknown>>(smartResponse);

    return {
      custom_collections: customData.custom_collections || [],
      smart_collections: smartData.smart_collections || [],
    };
  }

  async getCollection(collection_id: string, type: 'custom' | 'smart' = 'custom'): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const endpoint = type === 'custom' ? 'custom_collections' : 'smart_collections';
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/${endpoint}/${collection_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createCollection(collectionData: CreateCollectionArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const type = collectionData.collection_type || 'custom';
    const endpoint = type === 'custom' ? 'custom_collections' : 'smart_collections';
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/${endpoint}.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ [type === 'custom' ? 'custom_collection' : 'smart_collection']: collectionData }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  // Locations
  async listLocations(): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/locations.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getLocation(location_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/locations/${location_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  // Inventory - Using GraphQL for better querying capabilities
  async listInventoryItems(
    limit: number = 50,
    query?: string,
    cursor?: string
  ): Promise<Record<string, unknown>> {
    const graphqlQuery = `
      query inventoryItems($first: Int!, $query: String, $after: String) {
        inventoryItems(first: $first, query: $query, after: $after) {
          pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
          }
          nodes {
            id
            sku
            tracked
            requiresShipping
            createdAt
            updatedAt
            unitCost {
              amount
              currencyCode
            }
            countryCodeOfOrigin
            harmonizedSystemCode
            inventoryLevels(first: 10) {
              nodes {
                id
                quantities(names: ["available", "incoming", "committed", "reserved", "on_hand"]) {
                  name
                  quantity
                }
                location {
                  id
                  name
                }
              }
            }
          }
        }
      }
    `;

    return this.graphqlRequest(graphqlQuery, {
      first: Math.min(limit, 250),
      query: query || null,
      after: cursor || null,
    });
  }

  async getInventoryLevels(inventory_item_ids?: string, location_ids?: string, limit: number = 50): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (inventory_item_ids) {
      params.append("inventory_item_ids", inventory_item_ids);
    }

    if (location_ids) {
      params.append("location_ids", location_ids);
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/inventory_levels.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async adjustInventory(adjustmentData: AdjustInventoryArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/inventory_levels/adjust.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify(adjustmentData),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  // Fulfillments
  async listFulfillments(order_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/orders/${order_id}/fulfillments.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createFulfillment(fulfillmentData: CreateFulfillmentArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const { order_id, ...fulfillment } = fulfillmentData;
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/orders/${order_id}/fulfillments.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ fulfillment }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  // Draft Orders
  async listDraftOrders(limit: number = 50, cursor?: string, status?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (cursor) {
      params.append("page_info", cursor);
    }

    if (status) {
      params.append("status", status);
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/draft_orders.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getDraftOrder(draft_order_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/draft_orders/${draft_order_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createDraftOrder(draftOrderData: CreateDraftOrderArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/draft_orders.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ draft_order: draftOrderData }),
      }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  // Discounts (Price Rules)
  async listDiscounts(limit: number = 50, cursor?: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const params = new URLSearchParams({
      limit: Math.min(limit, 250).toString(),
    });

    if (cursor) {
      params.append("page_info", cursor);
    }

    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/price_rules.json?${params}`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async getDiscount(price_rule_id: string): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/price_rules/${price_rule_id}.json`,
      { headers: this.apiHeaders }
    );

    return this.handleApiResponse<Record<string, unknown>>(response);
  }

  async createDiscount(discountData: CreateDiscountArgs): Promise<Record<string, unknown>> {
    this.refreshToken();
    await this.respectRateLimit();
    
    const response = await fetch(
      `https://${this.shopDomain}/admin/api/${this.apiVersion}/price_rules.json`,
      {
        method: "POST",
        headers: this.apiHeaders,
        body: JSON.stringify({ price_rule: discountData }),
      }
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
          // Product tools
          listProductsTool,
          getProductTool,
          createProductTool,
          updateProductTool,
          // Order tools
          listOrdersTool,
          getOrderTool,
          createOrderTool,
          // Customer tools
          listCustomersTool,
          getCustomerTool,
          // Collection tools
          listCollectionsTool,
          getCollectionTool,
          createCollectionTool,
          // Location tools
          listLocationsTool,
          getLocationTool,
          // Inventory tools
          listInventoryItemsTool,
          getInventoryLevelsTool,
          adjustInventoryTool,
          // Fulfillment tools
          listFulfillmentsTool,
          createFulfillmentTool,
          // Draft Order tools
          listDraftOrdersTool,
          getDraftOrderTool,
          createDraftOrderTool,
          // Discount tools
          listDiscountsTool,
          getDiscountTool,
          createDiscountTool,
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
              args.collection_id,
              args.status,
              args.vendor,
              args.product_type,
              args.since_id,
              args.created_at_min,
              args.created_at_max,
              args.updated_at_min,
              args.updated_at_max
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

          // Collection tools
          case "shopify_list_collections": {
            const args = request.params.arguments as unknown as ListCollectionsArgs;
            const response = await shopifyClient.listCollections(
              args.limit,
              args.cursor,
              args.title
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_collection": {
            const args = request.params.arguments as unknown as GetCollectionArgs;
            if (!args.collection_id) {
              throw new Error("Missing required argument: collection_id");
            }
            const response = await shopifyClient.getCollection(args.collection_id, (args as any).type);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_collection": {
            const args = request.params.arguments as unknown as CreateCollectionArgs;
            if (!args.title) {
              throw new Error("Missing required argument: title");
            }
            const response = await shopifyClient.createCollection(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          // Location tools
          case "shopify_list_locations": {
            const response = await shopifyClient.listLocations();
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_location": {
            const args = request.params.arguments as unknown as GetLocationArgs;
            if (!args.location_id) {
              throw new Error("Missing required argument: location_id");
            }
            const response = await shopifyClient.getLocation(args.location_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          // Inventory tools
          case "shopify_list_inventory_items": {
            const args = request.params.arguments as unknown as ListInventoryItemsArgs;
            const response = await shopifyClient.listInventoryItems(
              args.limit,
              args.query,
              args.cursor
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_inventory_levels": {
            const args = request.params.arguments as unknown as GetInventoryLevelsArgs;
            const response = await shopifyClient.getInventoryLevels(
              args.inventory_item_ids,
              args.location_ids,
              args.limit
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_adjust_inventory": {
            const args = request.params.arguments as unknown as AdjustInventoryArgs;
            if (!args.location_id || !args.inventory_item_id || args.available_adjustment === undefined) {
              throw new Error("Missing required arguments: location_id, inventory_item_id, available_adjustment");
            }
            const response = await shopifyClient.adjustInventory(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          // Fulfillment tools
          case "shopify_list_fulfillments": {
            const args = request.params.arguments as unknown as ListFulfillmentsArgs;
            if (!args.order_id) {
              throw new Error("Missing required argument: order_id");
            }
            const response = await shopifyClient.listFulfillments(args.order_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_fulfillment": {
            const args = request.params.arguments as unknown as CreateFulfillmentArgs;
            if (!args.order_id) {
              throw new Error("Missing required argument: order_id");
            }
            const response = await shopifyClient.createFulfillment(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          // Draft Order tools
          case "shopify_list_draft_orders": {
            const args = request.params.arguments as unknown as ListDraftOrdersArgs;
            const response = await shopifyClient.listDraftOrders(
              args.limit,
              args.cursor,
              args.status
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_draft_order": {
            const args = request.params.arguments as unknown as GetDraftOrderArgs;
            if (!args.draft_order_id) {
              throw new Error("Missing required argument: draft_order_id");
            }
            const response = await shopifyClient.getDraftOrder(args.draft_order_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_draft_order": {
            const args = request.params.arguments as unknown as CreateDraftOrderArgs;
            if (!args.line_items || args.line_items.length === 0) {
              throw new Error("Missing required argument: line_items");
            }
            const response = await shopifyClient.createDraftOrder(args);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          // Discount tools
          case "shopify_list_discounts": {
            const args = request.params.arguments as unknown as ListDiscountsArgs;
            const response = await shopifyClient.listDiscounts(
              args.limit,
              args.cursor
            );
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_get_discount": {
            const args = request.params.arguments as unknown as GetDiscountArgs;
            if (!args.price_rule_id) {
              throw new Error("Missing required argument: price_rule_id");
            }
            const response = await shopifyClient.getDiscount(args.price_rule_id);
            return {
              content: [{ type: "text", text: JSON.stringify(response) }],
            } as const;
          }

          case "shopify_create_discount": {
            const args = request.params.arguments as unknown as CreateDiscountArgs;
            if (!args.title || !args.value_type || !args.value || !args.target_type || !args.target_selection) {
              throw new Error("Missing required arguments: title, value_type, value, target_type, target_selection");
            }
            const response = await shopifyClient.createDiscount(args);
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