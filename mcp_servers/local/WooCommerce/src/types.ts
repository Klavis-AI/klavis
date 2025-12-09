// WooCommerce meta_data type
export interface WooMetaData {
    id?: number;
    key: string;
    value: any;
}

// Product types
export interface ProductParams {
    productId?: number;
    perPage?: number;
    page?: number;
    search?: string;
    status?: string;
    category?: string;
    tag?: string;
    sku?: string;
    featured?: boolean;
    onSale?: boolean;
    minPrice?: string;
    maxPrice?: string;
    stockStatus?: string;
    orderby?: string;
    order?: string;
}

export interface CreateProductParams {
    productData: any;
}

export interface UpdateProductParams {
    productId: number;
    productData: any;
}

export interface DeleteProductParams {
    productId: number;
    force?: boolean;
}

// Order types
export interface OrderParams {
    orderId?: number;
    perPage?: number;
    page?: number;
    status?: string[];
    customer?: number;
    product?: number;
    dateAfter?: string;
    dateBefore?: string;
    orderby?: string;
    order?: string;
}

export interface CreateOrderParams {
    orderData: any;
}

export interface UpdateOrderParams {
    orderId: number;
    orderData: any;
}

export interface DeleteOrderParams {
    orderId: number;
    force?: boolean;
}

// Customer types
export interface CustomerParams {
    customerId?: number;
    perPage?: number;
    page?: number;
    search?: string;
    email?: string;
    role?: string;
    orderby?: string;
    order?: string;
}

export interface CreateCustomerParams {
    customerData: any;
}

export interface UpdateCustomerParams {
    customerId: number;
    customerData: any;
}

export interface DeleteCustomerParams {
    customerId: number;
    force?: boolean;
}

// Coupon types
export interface CouponParams {
    couponId?: number;
    perPage?: number;
    page?: number;
    search?: string;
    code?: string;
}

export interface CreateCouponParams {
    couponData: any;
}

export interface UpdateCouponParams {
    couponId: number;
    couponData: any;
}

export interface DeleteCouponParams {
    couponId: number;
    force?: boolean;
}

// Report types
export interface ReportParams {
    period?: string;
    dateMin?: string;
    dateMax?: string;
    perPage?: number;
    page?: number;
}

// Shipping types
export interface ShippingZoneParams {
    zoneId?: number;
}

export interface ShippingMethodParams {
    zoneId: number;
    instanceId?: number;
    methodData?: any;
}

// Tax types
export interface TaxRateParams {
    rateId?: number;
    taxClass?: string;
    perPage?: number;
    page?: number;
}

export interface TaxRateData {
    country?: string;
    state?: string;
    rate?: string;
    name?: string;
    priority?: number;
    compound?: boolean;
    shipping?: boolean;
    class?: string;
}

// Product variation types
export interface VariationParams {
    productId: number;
    variationId?: number;
    perPage?: number;
    page?: number;
}

// Meta data operations
export interface MetaDataParams {
    resourceType: 'product' | 'order' | 'customer';
    resourceId: number;
    metaKey?: string;
    metaValue?: any;
}

// Batch operations
export interface BatchUpdateParams {
    create?: any[];
    update?: any[];
    delete?: number[];
}

// Generic response type
export interface WooCommerceResponse<T = any> {
    data: T;
    headers?: any;
    status?: number;
}