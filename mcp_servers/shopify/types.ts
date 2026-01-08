export interface ListProductsArgs {
    limit?: number;
    cursor?: string;
    collection_id?: string;
    status?: ProductStatus;
    vendor?: string;
    product_type?: string;
    since_id?: string;
    created_at_min?: string;
    created_at_max?: string;
    updated_at_min?: string;
    updated_at_max?: string;
}

export interface GetProductArgs {
    product_id: string;
}

export interface ProductVariant {
    price: string;
    sku?: string;
    inventory_quantity?: number;
    option1?: string;
    option2?: string;
    option3?: string;
}

export interface CreateProductArgs {
    title: string;
    body_html?: string;
    vendor?: string;
    product_type?: string;
    tags?: string;
    status?: string;
    variants?: ProductVariant[];
}

export interface UpdateProductArgs {
    product_id: string;
    title?: string;
    body_html?: string;
    vendor?: string;
    product_type?: string;
    tags?: string;
    status?: string;
}

export interface ListOrdersArgs {
    limit?: number;
    status?: string;
    cursor?: string;
}

export interface GetOrderArgs {
    order_id: string;
}

export interface OrderLineItem {
    variant_id: number;
    quantity: number;
}

export interface OrderCustomer {
    email: string;
    first_name?: string;
    last_name?: string;
}

export interface ShippingAddress {
    address1: string;
    city: string;
    province?: string;
    country: string;
    zip: string;
}

export interface CreateOrderArgs {
    customer?: OrderCustomer;
    line_items: OrderLineItem[];
    shipping_address?: ShippingAddress;
}

export interface ListCustomersArgs {
    limit?: number;
    cursor?: string;
}

export interface GetCustomerArgs {
    customer_id: string;
}

export interface ShopifyCredentials {
    accessToken?: string;
    shopDomain?: string;
}

export interface AsyncLocalStorageState {
    shopify_access_token: string;
    shopify_shop_domain: string;
}

export interface ApiHeaders {
    [key: string]: string;
}

export interface ApiErrorResponse {
    errors?: unknown;
    [key: string]: unknown;
}

type ContentItem = {
    type: string;
    text: string;
}

export type OrderStatus = 'open' | 'closed' | 'cancelled' | 'any';
export type ProductStatus = 'active' | 'draft' | 'archived';

// Collection types
export interface ListCollectionsArgs {
    limit?: number;
    cursor?: string;
    title?: string;
}

export interface GetCollectionArgs {
    collection_id: string;
}

export interface CreateCollectionArgs {
    title: string;
    body_html?: string;
    sort_order?: string;
    collection_type?: 'custom' | 'smart';
}

// Inventory types
export interface ListInventoryItemsArgs {
    limit?: number;
    query?: string;
    cursor?: string;
}

export interface GetInventoryLevelsArgs {
    inventory_item_ids?: string;
    location_ids?: string;
    limit?: number;
}

export interface AdjustInventoryArgs {
    location_id: string;
    inventory_item_id: string;
    available_adjustment: number;
}

// Fulfillment types
export interface ListFulfillmentsArgs {
    order_id: string;
}

export interface CreateFulfillmentArgs {
    order_id: string;
    location_id?: string;
    tracking_number?: string;
    tracking_company?: string;
    tracking_url?: string;
    notify_customer?: boolean;
    line_items?: Array<{
        id: string;
        quantity: number;
    }>;
}

// Location types
export interface ListLocationsArgs {
    limit?: number;
}

export interface GetLocationArgs {
    location_id: string;
}

// Draft Order types
export interface ListDraftOrdersArgs {
    limit?: number;
    cursor?: string;
    status?: string;
}

export interface GetDraftOrderArgs {
    draft_order_id: string;
}

export interface CreateDraftOrderArgs {
    line_items: OrderLineItem[];
    customer?: OrderCustomer;
    shipping_address?: ShippingAddress;
    billing_address?: ShippingAddress;
    note?: string;
    email?: string;
    tags?: string;
}

// Discount types
export interface ListDiscountsArgs {
    limit?: number;
    cursor?: string;
}

export interface GetDiscountArgs {
    price_rule_id: string;
}

export interface CreateDiscountArgs {
    title: string;
    value_type: 'percentage' | 'fixed_amount';
    value: string;
    target_type: 'line_item' | 'shipping_line';
    target_selection: 'all' | 'entitled';
    allocation_method?: 'across' | 'each';
    starts_at?: string;
    ends_at?: string;
    once_per_customer?: boolean;
    usage_limit?: number;
}

