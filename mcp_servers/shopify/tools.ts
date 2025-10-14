import { Tool } from "@modelcontextprotocol/sdk/types.js";

export const listProductsTool: Tool = {
    name: "shopify_list_products",
    description: "List products in the Shopify store with pagination",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of products to return (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for next page of results",
        },
        collection_id: {
          type: "string",
          description: "Filter products by collection ID",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_PRODUCT",
      readOnlyHint: true,
    },
};
  
export const getProductTool: Tool = {
    name: "shopify_get_product",
    description: "Get detailed information about a specific product",
    inputSchema: {
      type: "object",
      properties: {
        product_id: {
          type: "string",
          description: "The ID of the product to retrieve",
        },
      },
      required: ["product_id"],
    },
    annotations: {
      category: "SHOPIFY_PRODUCT",
      readOnlyHint: true,
    },
};
  
export const createProductTool: Tool = {
    name: "shopify_create_product",
    description: "Create a new product in the Shopify store",
    inputSchema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "The title of the product",
        },
        body_html: {
          type: "string",
          description: "The HTML description of the product",
        },
        vendor: {
          type: "string",
          description: "The name of the product vendor",
        },
        product_type: {
          type: "string",
          description: "The type of product",
        },
        tags: {
          type: "string",
          description: "Comma-separated list of tags",
        },
        status: {
          type: "string",
          description: "Product status (active, draft, archived)",
          enum: ["active", "draft", "archived"],
        },
        variants: {
          type: "array",
          description: "Product variants",
          items: {
            type: "object",
            properties: {
              price: {
                type: "string",
                description: "Variant price (e.g., '29.99')",
              },
              sku: {
                type: "string",
                description: "Stock keeping unit",
              },
              inventory_quantity: {
                type: "number",
                description: "Inventory quantity",
              },
              option1: {
                type: "string",
                description: "First option (e.g., 'Blue')",
              },
              option2: {
                type: "string",
                description: "Second option (e.g., 'Small')",
              },
              option3: {
                type: "string",
                description: "Third option",
              },
            },
            required: ["price"],
          },
        },
          },
    required: ["title"],
  },
  annotations: {
    category: "SHOPIFY_PRODUCT",
  },
};
  
export const updateProductTool: Tool = {
    name: "shopify_update_product",
    description: "Update an existing product in the Shopify store",
    inputSchema: {
      type: "object",
      properties: {
        product_id: {
          type: "string",
          description: "The ID of the product to update",
        },
        title: {
          type: "string",
          description: "The title of the product",
        },
        body_html: {
          type: "string",
          description: "The HTML description of the product",
        },
        vendor: {
          type: "string",
          description: "The name of the product vendor",
        },
        product_type: {
          type: "string",
          description: "The type of product",
        },
        tags: {
          type: "string",
          description: "Comma-separated list of tags",
        },
        status: {
          type: "string",
          description: "Product status (active, draft, archived)",
          enum: ["active", "draft", "archived"],
        },
      },
      required: ["product_id"],
    },
    annotations: {
      category: "SHOPIFY_PRODUCT",
    },
};
  
export const listOrdersTool: Tool = {
    name: "shopify_list_orders",
    description: "List orders in the Shopify store with pagination",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of orders to return (default 50, max 250)",
          default: 50,
        },
        status: {
          type: "string",
          description: "Filter by order status (open, closed, cancelled, any)",
          enum: ["open", "closed", "cancelled", "any"],
          default: "any",
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for next page of results",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_ORDER",
      readOnlyHint: true,
    },
};
  
export const getOrderTool: Tool = {
    name: "shopify_get_order",
    description: "Get detailed information about a specific order",
    inputSchema: {
      type: "object",
      properties: {
        order_id: {
          type: "string",
          description: "The ID of the order to retrieve",
        },
      },
      required: ["order_id"],
    },
    annotations: {
      category: "SHOPIFY_ORDER",
      readOnlyHint: true,
    },
};
  
export const createOrderTool: Tool = {
    name: "shopify_create_order",
    description: "Create a new order in the Shopify store",
    inputSchema: {
        type: "object",
        properties: {
        customer: {
            type: "object",
            description: "Customer information",
            properties: {
            email: {
                type: "string",
                description: "Customer email",
            },
            first_name: {
                type: "string",
                description: "Customer first name",
            },
            last_name: {
                type: "string",
                description: "Customer last name",
            },
            },
            required: ["email"],
        },
        line_items: {
            type: "array",
            description: "Products to include in the order",
            items: {
            type: "object",
            properties: {
                variant_id: {
                type: "number",
                description: "The product variant ID",
                },
                quantity: {
                type: "number",
                description: "Quantity of the product",
                },
            },
            required: ["variant_id", "quantity"],
            },
        },
        shipping_address: {
            type: "object",
            description: "Shipping address",
            properties: {
            address1: {
                type: "string",
                description: "Address line 1",
            },
            city: {
                type: "string",
                description: "City",
            },
            province: {
                type: "string",
                description: "Province or state",
            },
            country: {
                type: "string",
                description: "Country",
            },
            zip: {
                type: "string",
                description: "Zip or postal code",
            },
            },
            required: ["address1", "city", "country", "zip"],
        },
        },
        required: ["line_items"],
    },
    annotations: {
      category: "SHOPIFY_ORDER",
    },
};

export const listCustomersTool: Tool = {
    name: "shopify_list_customers",
    description: "List customers in the Shopify store with pagination",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of customers to return (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for next page of results",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_CUSTOMER",
      readOnlyHint: true,
    },
};

export const getCustomerTool: Tool = {
    name: "shopify_get_customer",
    description: "Get detailed information about a specific customer",
    inputSchema: {
      type: "object",
      properties: {
        customer_id: {
          type: "string",
          description: "The ID of the customer to retrieve",
        },
      },
      required: ["customer_id"],
    },
    annotations: {
      category: "SHOPIFY_CUSTOMER",
      readOnlyHint: true,
    },
};
