import { Tool } from "@modelcontextprotocol/sdk/types.js";

// ============================================================================
// PRODUCT TOOLS
// ============================================================================

export const listProductsTool: Tool = {
    name: "shopify_list_products",
    description: "Search and list products in your Shopify store with advanced filtering. Returns comprehensive product details including title, description, vendor, pricing, product type, variants, images, and inventory status. Use this to find products by collection, status (active/draft/archived), vendor, product type, or browse all products with pagination. Supports filtering by creation/update dates. Results include up to 250 products per page with cursor-based pagination for retrieving additional pages.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of products to return per page (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results. Obtained from the Link header of previous response.",
        },
        collection_id: {
          type: "string",
          description: "Filter products by collection ID. Only returns products that belong to this collection.",
        },
        status: {
          type: "string",
          description: "Filter by product status. 'active' = published and available, 'draft' = unpublished, 'archived' = archived products",
          enum: ["active", "draft", "archived"],
        },
        vendor: {
          type: "string",
          description: "Filter products by vendor name (e.g., 'Nike', 'Adidas'). Exact match.",
        },
        product_type: {
          type: "string",
          description: "Filter products by product type/category (e.g., 'Shoes', 'T-Shirts'). Exact match.",
        },
        since_id: {
          type: "string",
          description: "Return products with IDs greater than this value. Useful for incremental syncing.",
        },
        created_at_min: {
          type: "string",
          description: "Show products created after this date and time (ISO 8601 format, e.g., '2024-01-01T00:00:00Z')",
        },
        created_at_max: {
          type: "string",
          description: "Show products created before this date and time (ISO 8601 format)",
        },
        updated_at_min: {
          type: "string",
          description: "Show products updated after this date and time (ISO 8601 format)",
        },
        updated_at_max: {
          type: "string",
          description: "Show products updated before this date and time (ISO 8601 format)",
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
    description: "Get comprehensive details about a specific product by ID. Returns complete product information including title, description, body HTML, vendor, product type, tags, status, all variants with pricing and inventory, product options (size, color, etc.), images with URLs, SEO metadata, and timestamps. Use this when you need detailed information about a single product, including all its variants and configuration.",
    inputSchema: {
      type: "object",
      properties: {
        product_id: {
          type: "string",
          description: "The unique Shopify ID of the product to retrieve (numeric string)",
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
    description: "Create a new product in the Shopify store with full configuration. Allows setting title, HTML description, vendor, product type, tags, status (active/draft/archived), and variants. Each variant can have its own price, SKU, inventory quantity, weight, barcode, and up to 3 option values (e.g., size, color, material). Use this to add new products to the catalog. The product will be created with the specified status and can include multiple variants for different configurations.",
    inputSchema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "The product title/name. This is what customers will see (e.g., 'Classic Cotton T-Shirt')",
        },
        body_html: {
          type: "string",
          description: "The product description in HTML format. Can include formatting, links, and images.",
        },
        vendor: {
          type: "string",
          description: "The name of the product vendor/manufacturer (e.g., 'Nike', 'Acme Corp')",
        },
        product_type: {
          type: "string",
          description: "The product category/type for organization (e.g., 'Shirts', 'Shoes', 'Accessories')",
        },
        tags: {
          type: "string",
          description: "Comma-separated list of tags for filtering and search (e.g., 'summer, sale, organic')",
        },
        status: {
          type: "string",
          description: "Product visibility: 'active' = published and visible, 'draft' = unpublished, 'archived' = archived",
          enum: ["active", "draft", "archived"],
        },
        variants: {
          type: "array",
          description: "Array of product variants for different configurations (size, color, etc.). At least one variant is required.",
          items: {
            type: "object",
            properties: {
              price: {
                type: "string",
                description: "Variant price as a decimal string (e.g., '29.99', '100.00')",
              },
              sku: {
                type: "string",
                description: "Stock Keeping Unit - unique identifier for inventory tracking",
              },
              inventory_quantity: {
                type: "number",
                description: "Available inventory quantity for this variant",
              },
              option1: {
                type: "string",
                description: "First option value (e.g., 'Blue', 'Small', 'Cotton')",
              },
              option2: {
                type: "string",
                description: "Second option value (e.g., 'Medium', 'XL')",
              },
              option3: {
                type: "string",
                description: "Third option value",
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
    description: "Update an existing product's information in the Shopify store. Allows modifying title, description, vendor, product type, tags, and status. Only the fields you provide will be updated - omitted fields remain unchanged. Use this to make changes to product details, change visibility status, update categorization, or modify product metadata. Note: To update variants, use the product_id and update via the product endpoint.",
    inputSchema: {
      type: "object",
      properties: {
        product_id: {
          type: "string",
          description: "The unique Shopify ID of the product to update (numeric string, required)",
        },
        title: {
          type: "string",
          description: "New product title/name",
        },
        body_html: {
          type: "string",
          description: "New product description in HTML format",
        },
        vendor: {
          type: "string",
          description: "New vendor/manufacturer name",
        },
        product_type: {
          type: "string",
          description: "New product category/type",
        },
        tags: {
          type: "string",
          description: "New comma-separated list of tags (replaces existing tags)",
        },
        status: {
          type: "string",
          description: "New product status: 'active' to publish, 'draft' to unpublish, 'archived' to archive",
          enum: ["active", "draft", "archived"],
        },
      },
      required: ["product_id"],
    },
    annotations: {
      category: "SHOPIFY_PRODUCT",
    },
};

// ============================================================================
// ORDER TOOLS
// ============================================================================
  
export const listOrdersTool: Tool = {
    name: "shopify_list_orders",
    description: "List and search orders in your Shopify store with filtering by status. Returns comprehensive order information including order number, customer details, line items with products and quantities, pricing (subtotal, taxes, discounts, total), payment status (pending, paid, refunded), fulfillment status (fulfilled, partial, unfulfilled), shipping and billing addresses, and timestamps. Use this to view recent orders, find unfulfilled orders, track cancelled orders, or get all orders with pagination. Results include up to 250 orders per page.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of orders to return per page (default 50, max 250)",
          default: 50,
        },
        status: {
          type: "string",
          description: "Filter by order status: 'open' = unpaid/unfulfilled, 'closed' = paid and fulfilled, 'cancelled' = cancelled orders, 'any' = all orders regardless of status",
          enum: ["open", "closed", "cancelled", "any"],
          default: "any",
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results. Obtained from the Link header of previous response.",
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
    description: "Get complete details about a specific order by ID. Returns comprehensive order information including order number, customer information (name, email, phone), all line items with product details and quantities, pricing breakdown (subtotal, taxes, shipping, discounts, total), financial status (pending, authorized, paid, partially_refunded, refunded, voided), fulfillment status and tracking, shipping and billing addresses, order notes, tags, risk analysis, and all timestamps. Use this when you need detailed information about a single order for customer service, fulfillment, or reporting purposes.",
    inputSchema: {
      type: "object",
      properties: {
        order_id: {
          type: "string",
          description: "The unique Shopify ID of the order to retrieve (numeric string)",
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
    description: "Create a new order in the Shopify store programmatically. Useful for creating orders from external systems, processing phone orders, or creating manual orders for customers. Requires line items with product variant IDs and quantities. Can optionally include customer information (email, name), shipping address, and billing address. The order will be created with 'pending' payment status and can be marked as paid later. Use this to record sales made outside the online store or to create draft orders for processing.",
    inputSchema: {
        type: "object",
        properties: {
        customer: {
            type: "object",
            description: "Customer information for the order. If email matches an existing customer, it will be linked.",
            properties: {
            email: {
                type: "string",
                description: "Customer email address (required for customer object)",
            },
            first_name: {
                type: "string",
                description: "Customer's first name",
            },
            last_name: {
                type: "string",
                description: "Customer's last name",
            },
            },
            required: ["email"],
        },
        line_items: {
            type: "array",
            description: "Products to include in the order. Each line item represents a product variant and quantity.",
            items: {
            type: "object",
            properties: {
                variant_id: {
                type: "number",
                description: "The Shopify product variant ID to add to the order",
                },
                quantity: {
                type: "number",
                description: "Quantity of this variant to order (must be > 0)",
                },
            },
            required: ["variant_id", "quantity"],
            },
        },
        shipping_address: {
            type: "object",
            description: "Shipping address for order delivery",
            properties: {
            address1: {
                type: "string",
                description: "Street address line 1",
            },
            city: {
                type: "string",
                description: "City name",
            },
            province: {
                type: "string",
                description: "Province, state, or region",
            },
            country: {
                type: "string",
                description: "Country name or ISO code",
            },
            zip: {
                type: "string",
                description: "Postal code or ZIP code",
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

// ============================================================================
// CUSTOMER TOOLS
// ============================================================================

export const listCustomersTool: Tool = {
    name: "shopify_list_customers",
    description: "List and browse all customers in your Shopify store with pagination. Returns customer information including name, email, phone number, total orders count, total amount spent, customer tags, marketing preferences, account status, default address, and creation/update timestamps. Use this to view your customer base, find customers by various criteria, or export customer data. Results include up to 250 customers per page with cursor-based pagination for retrieving additional pages.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of customers to return per page (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results. Obtained from the Link header of previous response.",
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
    description: "Get comprehensive details about a specific customer by ID. Returns complete customer profile including personal information (name, email, phone), order history (total orders, total spent), addresses (default and additional), marketing preferences (accepts marketing, email verified), customer tags, account state (enabled, disabled, invited, declined), notes, and metadata. Use this to look up customer details for support, verify customer information, or access their complete purchase history.",
    inputSchema: {
      type: "object",
      properties: {
        customer_id: {
          type: "string",
          description: "The unique Shopify ID of the customer to retrieve (numeric string)",
        },
      },
      required: ["customer_id"],
    },
    annotations: {
      category: "SHOPIFY_CUSTOMER",
      readOnlyHint: true,
    },
};

// ============================================================================
// COLLECTION TOOLS
// ============================================================================

export const listCollectionsTool: Tool = {
    name: "shopify_list_collections",
    description: "List all product collections in your Shopify store, including both custom collections (manually curated) and smart collections (automatically populated based on rules). Returns collection details including title, handle, description, publication status, sort order, collection type, and product count. Custom collections contain manually selected products, while smart collections use rules to automatically include products matching specific criteria (tags, price, vendor, etc.). Use this to browse your store's organization structure or find specific collections.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of collections to return per type (default 50, max 250). Returns both custom and smart collections.",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results",
        },
        title: {
          type: "string",
          description: "Filter collections by title (partial match supported)",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_COLLECTION",
      readOnlyHint: true,
    },
};

export const getCollectionTool: Tool = {
    name: "shopify_get_collection",
    description: "Get detailed information about a specific collection by ID. Returns complete collection details including title, description (body_html), handle (URL slug), publication date and scope, sort order for products, collection type (custom or smart), and for smart collections: the rule configuration (disjunctive flag and rule conditions). Smart collections show the automated rules that determine which products are included. Use this to understand collection configuration or debug smart collection rules.",
    inputSchema: {
      type: "object",
      properties: {
        collection_id: {
          type: "string",
          description: "The unique Shopify ID of the collection to retrieve (numeric string)",
        },
        type: {
          type: "string",
          description: "The type of collection: 'custom' for manually curated collections, 'smart' for rule-based automated collections",
          enum: ["custom", "smart"],
          default: "custom",
        },
      },
      required: ["collection_id"],
    },
    annotations: {
      category: "SHOPIFY_COLLECTION",
      readOnlyHint: true,
    },
};

export const createCollectionTool: Tool = {
    name: "shopify_create_collection",
    description: "Create a new product collection in your Shopify store. Collections help organize products for easier browsing. Custom collections require you to manually add products later. Smart collections automatically include products based on rules you define (e.g., all products tagged 'summer', all products under $50, all products from vendor 'Nike'). Specify title, optional HTML description, sort order for products, and collection type. Use this to create new ways to organize and present your products to customers.",
    inputSchema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "The collection title/name that will be displayed to customers (e.g., 'Summer Collection', 'Clearance Items')",
        },
        body_html: {
          type: "string",
          description: "Optional HTML description of the collection, displayed on the collection page",
        },
        sort_order: {
          type: "string",
          description: "How products are sorted: 'alpha-asc' (A-Z), 'alpha-desc' (Z-A), 'best-selling', 'created' (newest first), 'created-desc' (oldest first), 'manual', 'price-asc' (low to high), 'price-desc' (high to low)",
          enum: ["alpha-asc", "alpha-desc", "best-selling", "created", "created-desc", "manual", "price-asc", "price-desc"],
        },
        collection_type: {
          type: "string",
          description: "'custom' for manually curated collections where you select products, 'smart' for automated collections using rules",
          enum: ["custom", "smart"],
          default: "custom",
        },
      },
      required: ["title"],
    },
    annotations: {
      category: "SHOPIFY_COLLECTION",
    },
};

// ============================================================================
// LOCATION TOOLS
// ============================================================================

export const listLocationsTool: Tool = {
    name: "shopify_list_locations",
    description: "List all physical and virtual locations/warehouses configured in your Shopify store. Locations represent places where you stock and ship inventory from (warehouses, retail stores, pop-up shops, etc.). Returns location details including name, full address (street, city, province, country, postal code), phone number, active status, and whether it's a legacy location. Use this to see all your fulfillment locations, verify location setup, or choose locations for inventory operations and fulfillment.",
    inputSchema: {
      type: "object",
      properties: {},
    },
    annotations: {
      category: "SHOPIFY_LOCATION",
      readOnlyHint: true,
    },
};

export const getLocationTool: Tool = {
    name: "shopify_get_location",
    description: "Get detailed information about a specific location by ID. Returns complete location details including name, full address components, contact phone, active status, legacy flag, localized country/province names, and location capabilities. Use this to verify location details before inventory operations or to display location information for customer service.",
    inputSchema: {
      type: "object",
      properties: {
        location_id: {
          type: "string",
          description: "The unique Shopify ID of the location to retrieve (numeric string)",
        },
      },
      required: ["location_id"],
    },
    annotations: {
      category: "SHOPIFY_LOCATION",
      readOnlyHint: true,
    },
};

// ============================================================================
// INVENTORY TOOLS
// ============================================================================

export const listInventoryItemsTool: Tool = {
    name: "shopify_list_inventory_items",
    description: "List inventory items in your Shopify store with optional filtering. Each product variant has an associated inventory item that tracks stock across locations. Returns inventory item details including SKU, cost, tracked status, shipping requirements, country of origin, harmonized system codes, AND current inventory levels at all locations in a single request. Use the query parameter to filter by SKU (sku:'ABC123'), creation date (created_at:>2024-01-01), update date (updated_at:>2024-01-01), or ID range (id:>=12345). Results include up to 250 items per page with cursor-based pagination.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of inventory items to return (default 50, max 250)",
          default: 50,
        },
        query: {
          type: "string",
          description: "Search filter using Shopify query syntax. Examples: \"sku:'ABC123'\", \"created_at:>2024-01-01\", \"updated_at:>2024-06-01\", \"id:>=12345\". Can combine with OR/AND operators.",
        },
        cursor: {
          type: "string",
          description: "Pagination cursor (endCursor from previous response's pageInfo) for fetching the next page of results",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_INVENTORY",
      readOnlyHint: true,
    },
};

export const getInventoryLevelsTool: Tool = {
    name: "shopify_get_inventory_levels",
    description: "Get current stock levels for inventory items across your locations. Inventory levels show how much stock is available for each product variant at each location. Returns inventory item ID, location ID, available quantity, and last updated timestamp. Use this to check stock availability, find low inventory items, or see inventory distribution across locations. Filter by specific inventory items or locations to narrow results. Essential for order fulfillment and inventory management.",
    inputSchema: {
      type: "object",
      properties: {
        inventory_item_ids: {
          type: "string",
          description: "Comma-separated list of inventory item IDs to check stock for specific items",
        },
        location_ids: {
          type: "string",
          description: "Comma-separated list of location IDs to check stock at specific locations",
        },
        limit: {
          type: "number",
          description: "Maximum number of inventory levels to return (default 50, max 250)",
          default: 50,
        },
      },
    },
    annotations: {
      category: "SHOPIFY_INVENTORY",
      readOnlyHint: true,
    },
};

export const adjustInventoryTool: Tool = {
    name: "shopify_adjust_inventory",
    description: "Adjust the inventory quantity for an item at a specific location. Use this to add or remove stock after receiving shipments, cycle counts, damaged goods, or other inventory adjustments. Provide a positive number to increase stock or negative number to decrease stock. The adjustment is relative to the current quantity (not an absolute set). This updates the 'available' inventory that can be allocated to orders. Use get_inventory_levels first to check current quantities before adjusting.",
    inputSchema: {
      type: "object",
      properties: {
        location_id: {
          type: "string",
          description: "The location ID where inventory should be adjusted (numeric string)",
        },
        inventory_item_id: {
          type: "string",
          description: "The inventory item ID to adjust stock for (numeric string)",
        },
        available_adjustment: {
          type: "number",
          description: "The quantity to adjust by. Positive numbers add stock, negative numbers remove stock (e.g., 10, -5)",
        },
      },
      required: ["location_id", "inventory_item_id", "available_adjustment"],
    },
    annotations: {
      category: "SHOPIFY_INVENTORY",
    },
};

// ============================================================================
// FULFILLMENT TOOLS
// ============================================================================

export const listFulfillmentsTool: Tool = {
    name: "shopify_list_fulfillments",
    description: "List all fulfillments (shipments) for a specific order. Fulfillments represent shipments sent to customers and track which items were shipped, tracking information, and shipment status. Returns fulfillment ID, status (pending, open, success, cancelled, error, failure), line items included in the shipment, tracking company and numbers, tracking URLs, shipment status, location the order was fulfilled from, and timestamps. Use this to check shipment status, get tracking information for customers, or verify fulfillment completion.",
    inputSchema: {
      type: "object",
      properties: {
        order_id: {
          type: "string",
          description: "The order ID to get fulfillments for (numeric string)",
        },
      },
      required: ["order_id"],
    },
    annotations: {
      category: "SHOPIFY_FULFILLMENT",
      readOnlyHint: true,
    },
};

export const createFulfillmentTool: Tool = {
    name: "shopify_create_fulfillment",
    description: "Create a new fulfillment (shipment) for an order. Use this when you've shipped items to mark them as fulfilled and provide tracking information to customers. Specify which line items are being fulfilled, optionally provide tracking information (company, number, URL), and choose whether to notify the customer via email. If line_items is not specified, all unfulfilled items will be included. The fulfillment will update the order's fulfillment status and send tracking info to the customer if notify_customer is true.",
    inputSchema: {
      type: "object",
      properties: {
        order_id: {
          type: "string",
          description: "The order ID to create a fulfillment for (numeric string, required)",
        },
        location_id: {
          type: "string",
          description: "The location ID where inventory is being fulfilled from. If not provided, uses the order's assigned location.",
        },
        tracking_number: {
          type: "string",
          description: "Shipment tracking number from the carrier (e.g., '1Z999AA10123456784')",
        },
        tracking_company: {
          type: "string",
          description: "Name of the shipping carrier (e.g., 'UPS', 'FedEx', 'USPS', 'DHL')",
        },
        tracking_url: {
          type: "string",
          description: "Full URL to track the shipment on the carrier's website",
        },
        notify_customer: {
          type: "boolean",
          description: "Whether to send a shipment confirmation email with tracking to the customer (default: false)",
          default: false,
        },
        line_items: {
          type: "array",
          description: "Specific line items to fulfill. If omitted, all unfulfilled items are included.",
          items: {
            type: "object",
            properties: {
              id: {
                type: "string",
                description: "Line item ID from the order",
              },
              quantity: {
                type: "number",
                description: "Quantity of this line item to fulfill (must be ≤ unfulfilled quantity)",
              },
            },
            required: ["id", "quantity"],
          },
        },
      },
      required: ["order_id"],
    },
    annotations: {
      category: "SHOPIFY_FULFILLMENT",
    },
};

// ============================================================================
// DRAFT ORDER TOOLS
// ============================================================================

export const listDraftOrdersTool: Tool = {
    name: "shopify_list_draft_orders",
    description: "List draft orders in your Shopify store with optional filtering. Draft orders are orders created by merchants that haven't been completed or paid yet. They can be sent to customers as invoices for payment. Returns draft order details including name, status (open, invoice_sent, completed), customer info, line items, pricing, and timestamps. Use this to view pending draft orders, find orders waiting for payment, or manage orders created for phone/email sales. Results include up to 250 draft orders per page.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of draft orders to return per page (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results",
        },
        status: {
          type: "string",
          description: "Filter by status: 'open' = not yet sent or paid, 'invoice_sent' = invoice sent awaiting payment, 'completed' = converted to order",
          enum: ["open", "invoice_sent", "completed"],
        },
      },
    },
    annotations: {
      category: "SHOPIFY_DRAFT_ORDER",
      readOnlyHint: true,
    },
};

export const getDraftOrderTool: Tool = {
    name: "shopify_get_draft_order",
    description: "Get comprehensive details about a specific draft order by ID. Returns complete draft order information including order name, status, customer details, all line items with pricing, subtotal/taxes/total, shipping and billing addresses, notes, tags, invoice sent timestamp, completion timestamp, and metadata. Use this to review draft order details before sending invoice, verify customer information, or check draft order configuration.",
    inputSchema: {
      type: "object",
      properties: {
        draft_order_id: {
          type: "string",
          description: "The unique Shopify ID of the draft order to retrieve (numeric string)",
        },
      },
      required: ["draft_order_id"],
    },
    annotations: {
      category: "SHOPIFY_DRAFT_ORDER",
      readOnlyHint: true,
    },
};

export const createDraftOrderTool: Tool = {
    name: "shopify_create_draft_order",
    description: "Create a new draft order in your Shopify store. Draft orders are perfect for processing orders over the phone, via email, or for custom quotes. They allow you to create an order, potentially apply custom pricing or discounts, and send an invoice to the customer for payment. Once paid, the draft order converts to a regular order. Specify line items (product variants and quantities), optionally include customer information, shipping/billing addresses, notes, and tags. The draft order can be sent to customers as an invoice link for payment.",
    inputSchema: {
      type: "object",
      properties: {
        line_items: {
          type: "array",
          description: "Products to include in the draft order. Each line item requires a variant ID and quantity.",
          items: {
            type: "object",
            properties: {
              variant_id: {
                type: "number",
                description: "The Shopify product variant ID to add to the draft order",
              },
              quantity: {
                type: "number",
                description: "Quantity of this variant (must be > 0)",
              },
            },
            required: ["variant_id", "quantity"],
          },
        },
        customer: {
          type: "object",
          description: "Customer information. If email matches existing customer, it will be linked.",
          properties: {
            email: {
              type: "string",
              description: "Customer email address",
            },
            first_name: {
              type: "string",
              description: "Customer's first name",
            },
            last_name: {
              type: "string",
              description: "Customer's last name",
            },
          },
          required: ["email"],
        },
        shipping_address: {
          type: "object",
          description: "Shipping address for the draft order",
          properties: {
            address1: { type: "string", description: "Street address line 1" },
            city: { type: "string", description: "City name" },
            province: { type: "string", description: "Province, state, or region" },
            country: { type: "string", description: "Country name or ISO code" },
            zip: { type: "string", description: "Postal code or ZIP code" },
          },
          required: ["address1", "city", "country", "zip"],
        },
        billing_address: {
          type: "object",
          description: "Billing address (if different from shipping)",
          properties: {
            address1: { type: "string" },
            city: { type: "string" },
            province: { type: "string" },
            country: { type: "string" },
            zip: { type: "string" },
          },
          required: ["address1", "city", "country", "zip"],
        },
        note: {
          type: "string",
          description: "Internal note about the draft order (not visible to customer)",
        },
        email: {
          type: "string",
          description: "Email address to send the invoice to (if different from customer email)",
        },
        tags: {
          type: "string",
          description: "Comma-separated tags for organizing draft orders",
        },
      },
      required: ["line_items"],
    },
    annotations: {
      category: "SHOPIFY_DRAFT_ORDER",
    },
};

// ============================================================================
// DISCOUNT TOOLS (Price Rules)
// ============================================================================

export const listDiscountsTool: Tool = {
    name: "shopify_list_discounts",
    description: "List all discount codes and automatic discounts (price rules) in your Shopify store. Price rules define the discount logic and can have multiple discount codes associated with them. Returns discount details including title, value type (percentage or fixed amount), discount value, target (line items or shipping), target selection (all products or specific entitled products), allocation method, usage limits, date range (starts_at, ends_at), and once-per-customer restriction. Use this to view active promotions, find expired discounts, or audit your discount strategy.",
    inputSchema: {
      type: "object",
      properties: {
        limit: {
          type: "number",
          description: "Maximum number of price rules/discounts to return (default 50, max 250)",
          default: 50,
        },
        cursor: {
          type: "string",
          description: "Pagination cursor for fetching the next page of results",
        },
      },
    },
    annotations: {
      category: "SHOPIFY_DISCOUNT",
      readOnlyHint: true,
    },
};

export const getDiscountTool: Tool = {
    name: "shopify_get_discount",
    description: "Get detailed information about a specific discount/price rule by ID. Returns complete discount configuration including title, value type and amount, what it targets (products or shipping), how it's allocated, customer restrictions (once per customer), usage limits, validity period (start and end dates), prerequisite requirements (minimum subtotal or quantity), and which products/collections it applies to. Use this to review discount settings, troubleshoot discount issues, or verify promotion configuration before launching.",
    inputSchema: {
      type: "object",
      properties: {
        price_rule_id: {
          type: "string",
          description: "The unique Shopify ID of the price rule/discount to retrieve (numeric string)",
        },
      },
      required: ["price_rule_id"],
    },
    annotations: {
      category: "SHOPIFY_DISCOUNT",
      readOnlyHint: true,
    },
};

export const createDiscountTool: Tool = {
    name: "shopify_create_discount",
    description: "Create a new discount/price rule in your Shopify store. Discounts can be percentage-based (e.g., 20% off) or fixed amount (e.g., $10 off). They can apply to line items (products) or shipping. Configure target selection (all products or specific entitled products), allocation method (across all items or each item), validity period, usage limits, and customer restrictions. After creating the price rule, you'll need to create discount codes that customers can use. Use this to set up promotions, sales campaigns, or customer incentives.",
    inputSchema: {
      type: "object",
      properties: {
        title: {
          type: "string",
          description: "Internal name for the discount rule (e.g., 'Summer Sale 2024', '20% Off First Order')",
        },
        value_type: {
          type: "string",
          description: "'percentage' for percent-based discounts (value is 0-100), 'fixed_amount' for dollar/currency discounts",
          enum: ["percentage", "fixed_amount"],
        },
        value: {
          type: "string",
          description: "Discount value as a string. For percentage: '-10.0' = 10% off. For fixed_amount: '-10.00' = $10 off (negative number)",
        },
        target_type: {
          type: "string",
          description: "'line_item' to discount products, 'shipping_line' to discount shipping costs",
          enum: ["line_item", "shipping_line"],
        },
        target_selection: {
          type: "string",
          description: "'all' applies to all products/shipping, 'entitled' applies only to specific entitled products/shipping methods",
          enum: ["all", "entitled"],
        },
        allocation_method: {
          type: "string",
          description: "'across' splits discount across all items, 'each' applies full discount to each item",
          enum: ["across", "each"],
        },
        starts_at: {
          type: "string",
          description: "When the discount becomes active (ISO 8601 format, e.g., '2024-06-01T00:00:00Z')",
        },
        ends_at: {
          type: "string",
          description: "When the discount expires (ISO 8601 format). If omitted, discount never expires.",
        },
        once_per_customer: {
          type: "boolean",
          description: "If true, each customer can only use this discount once. If false, customers can reuse it.",
          default: false,
        },
        usage_limit: {
          type: "number",
          description: "Maximum total number of times this discount can be used across all customers. Omit for unlimited.",
        },
      },
      required: ["title", "value_type", "value", "target_type", "target_selection"],
    },
    annotations: {
      category: "SHOPIFY_DISCOUNT",
    },
};
