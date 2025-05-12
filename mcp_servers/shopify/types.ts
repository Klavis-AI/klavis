export interface ListProductsArgs {
    limit?: number;
    cursor?: string;
    collection_id?: string;
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
